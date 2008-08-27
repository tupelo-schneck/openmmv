(* TODO: what to do with non-transferable? *)

type currency = float
type support = float
type utility = currency -> currency -> currency -> support (* flat_before, spent_before, flat_here *)

type funding_level = {
  mutable pamount : currency; (* mutable for ease of elimination *)
  mutable psupport : support;
  mutable pprev_support : support;
}

let new_initial_funding_level amount = {
  pamount = amount;
  psupport = 0.;
  pprev_support = 0.;
}

type project = {
  projectid : int;
  pname : string;
  minimum : currency;
  maximum : currency;
  mutable eliminated : currency;
  mutable fundings : funding_level list;
}

type ballot_item = {
  bprojectid : int;
  bamount : currency;
  prior : currency; (* how much has already gone to this project on this ballot *)
  mutable actual_amount : currency; 
  mutable bsupport : support;
  mutable contribution : currency;
  mutable project : project option;
}

type ballot_priority = ballot_item list

type ballot = {
  ballotid : int;
  bname : string;
  weight : float;
  priorities : ballot_priority list;
}

type game = {
  total : currency;
  projects : project list;
  utility : utility;
  quota : float; (* a fraction of the number of players *)
  ballots : ballot list;
  round_to_nearest : currency; (* used for project funding levels *)
}

let float_players (g:game) : float = 
  let res = ref 0. in
  List.iter (fun b -> res := !res +. b.weight) g.ballots;
  !res

let quota_support (g:game) : support =
  max 1.0 (g.quota *. float_players g)

let share (g:game) : currency =
  g.total /. float_players g

let support (g:game) (flat_before:currency) (spent_before:currency) (flat_here:currency) : support =
  let share = share g in
  let spend_limit = share -. spent_before in
  if spend_limit <= 0. then 0. else
  let support = g.utility (flat_before /. share) (spent_before /. share) (flat_here /. share) in
  let support = max 0. support in
  if support *. flat_here > spend_limit then spend_limit /. flat_here else support

let project_for_ballot_item (g:game) (b:ballot_item) : project =
  begin match b.project with
    | None ->
	let p =
	  List.find (fun p -> p.projectid = b.bprojectid) g.projects
	in
	b.project <- Some p;
	p
    | Some p -> p
  end

let spent_on_ballot_priority (bp:ballot_priority) : currency =
  let rec aux bs acc =
    begin match bs with
      | [] -> acc
      | b::bs -> aux bs (acc +. b.contribution)
    end
  in
  aux bp 0.

let flat_on_ballot_priority (bp:ballot_priority) : currency =
  let rec aux bs acc =
    begin match bs with
      | [] -> acc
      | b::bs -> aux bs (acc +. if b.bsupport = 0. then 0. else b.contribution /. b.bsupport)
    end
  in
  aux bp 0.

let spent_on_ballot (b:ballot) : currency =
  let rec aux bs acc =
    begin match bs with
      | [] -> acc
      | b::bs -> aux bs (acc +. spent_on_ballot_priority b)
    end
  in
  b.weight *. aux b.priorities 0.

(* Insert a new funding level for project p of the given amount *)
let add_new_funding_level_if_needed (p:project) (amount:currency) : unit =
  if amount >= p.eliminated then () else
  let new_funding_level f_opt = 
    begin match f_opt with
      | None -> new_initial_funding_level amount
      | Some f -> {f with pamount = amount}
    end 
  in
  let rec loop (before:funding_level list) (after:funding_level list) : unit =
    begin match after with
      | [] -> p.fundings <- List.rev_append before [new_funding_level None]
      | f :: fs ->
	  if f.pamount < amount then loop (f :: before) fs
	  else if f.pamount = amount then ()
	  else p.fundings <- List.rev_append before (new_funding_level (Some f) :: after)
    end
  in
  loop [] p.fundings

let add_support_for_ballot_item (g:game) (b:ballot_item) (weight:float) : unit =
  let p = project_for_ballot_item g b in
  let rec loop fs =
    begin match fs with
      | [] -> ()
      | f :: fs -> 
	  if f.pamount > p.eliminated || f.pamount > b.actual_amount then ()
	  else if f.pamount <= b.prior then loop fs
	  else begin
	    f.psupport <- f.psupport +. weight *. b.bsupport;
	    loop fs
	  end
    end
  in
  loop p.fundings

(**********************************************************************
 * The main function, which takes a single ballot item and figures out
 * its flat contribution (i.e. the contribution with support one).
 **********************************************************************)
let get_flat_contribution_of_ballot_item (g:game) (b:ballot_item) : unit =
  let p = project_for_ballot_item g b in
  add_new_funding_level_if_needed p b.bamount;
  b.bsupport <- 1.;
  let rec loop fs prior sofar =
    begin match fs with
      | [] -> 
	  b.actual_amount <- prior;
	  b.contribution <- sofar
      | f :: fs ->
	  (* if eliminated or past what this voter wants, done *)
	  if f.pamount > p.eliminated || f.pamount > b.bamount then begin
	    b.actual_amount <- prior;
	    b.contribution <- sofar
	  end
	  (* skipping over funding levels below b.prior *)
	  else if f.pamount <= prior then loop fs prior sofar
	  (* at this point, we're looking at a real funding level between prior
	     and b.bamount *)
	  else 
	    (* use quota_support for projects below quota *)
	    let f_support = max f.pprev_support (quota_support g) in
	    let this_contribution = (f.pamount -. prior) /. f_support in
	    loop fs f.pamount (sofar +. this_contribution)
    end
  in
  loop p.fundings b.prior 0.

let adjust_ballot_item (g:game) (b:ballot_item) (flat_sofar:currency) (spent_sofar:currency) 
  (weight:float) : unit =
  get_flat_contribution_of_ballot_item g b;
  b.bsupport <- support g flat_sofar spent_sofar b.contribution;
  b.contribution <- b.bsupport *. b.contribution;
  add_support_for_ballot_item g b weight
  
(**********************************************************************
 * This function is for dealing with tied items on a ballot
 **********************************************************************)
let adjust_ballot_priority (g:game) (bp:ballot_priority) 
  (flat_sofar:currency) (spent_sofar:currency) (weight:float) : unit =
  List.iter (get_flat_contribution_of_ballot_item g) bp;
  let flat_here = spent_on_ballot_priority bp in
  let support = support g flat_sofar spent_sofar flat_here in
  List.iter begin fun b ->
    b.bsupport <- support;
    b.contribution <- support *. b.contribution;
    add_support_for_ballot_item g b weight
  end bp

let adjust_ballot (g:game) (b:ballot) : unit =
  let rec loop_priorities priorities flat_sofar spent_sofar =
    begin match priorities with
      | [] -> ()
      | bp::bps ->
	  adjust_ballot_priority g bp flat_sofar spent_sofar b.weight;
	  let spent_here = spent_on_ballot_priority bp in
	  let flat_here = flat_on_ballot_priority bp in
	  loop_priorities bps (flat_sofar +. flat_here) (spent_sofar +. spent_here)
    end
  in
  loop_priorities b.priorities 0. 0.

let renew_project_supports (p:project) : unit =
  List.iter begin fun f -> 
	       f.pprev_support <- f.psupport; 
	       f.psupport <- 0.;
	     end p.fundings

(**********************************************************************
 * Perform one iteration over all ballots
 **********************************************************************)
let one_iteration (g:game) : unit =
  List.iter renew_project_supports g.projects;
  List.iter (adjust_ballot g) g.ballots


(**********************************************************************
 * Perform an elimination.
 * Currently it changes the amount of the funding level to $1 less.
 * TODO: consider a faster search for elimination level...
 **********************************************************************)
let eliminate (g:game) (p:project) (f:funding_level) (prior:currency) : unit =
  p.eliminated <- f.pamount;
  if f.pamount <= p.minimum then p.fundings <- [] else begin
    let new_amount = f.pamount -. g.round_to_nearest in
    let new_amount = if new_amount < p.minimum then p.minimum else new_amount in
    if new_amount <= prior then p.fundings <- List.filter (fun f' -> f' != f) p.fundings
    else f.pamount <- new_amount
  end

(********************************************************************** 
 * Say that there has been a change when the total change over all 
 * projects and funding levels is more than g.round_to_nearest
 **********************************************************************)
let change_in_projects (g:game) : bool =
  let rec loop_funding_levels fs prior sofar =
    if sofar >= g.round_to_nearest /. 2. then g.round_to_nearest /. 2. else
    begin match fs with
      | [] -> sofar
      | f::fs -> 
	  let low = min f.psupport f.pprev_support in
	  let high = max f.psupport f.pprev_support in
	  let f_support = max low (quota_support g) in
	  let contrib = (high -. low) /. f_support *. (f.pamount -. prior) in
	  loop_funding_levels fs f.pamount (sofar +. contrib)
    end
  in
  let rec loop_projects ps sofar =
    if sofar >= g.round_to_nearest /. 2. then true else
    begin match ps with
      | [] -> false
      | p::ps ->
	  loop_projects ps (loop_funding_levels p.fundings 0. sofar)
    end
  in
  loop_projects g.projects 0.

(* None if exclusion made; Some change otherwise *)
(* Need to find lowest, next lowest, surplus *)
let short_cut_exclusion_search (g:game) (* : currency option *) =
  let quota_support = quota_support g in
  let surplus = ref 0. in
  let lowest = ref [] in
  let rec consider_funding_levels p fs prior dist_accum res =
    begin match fs with
      | [] -> res
      | f :: fs ->
	  if f.pamount < p.eliminated && f.psupport > 0. then begin
	    if f.psupport >= quota_support then begin
	      let f_support = max f.pprev_support quota_support in
	      surplus := !surplus +. f.psupport /. f_support *. (f.pamount -. prior) -. f.pamount +. prior;
	      consider_funding_levels p fs f.pamount 0. None
	    end else begin
	      let dist = dist_accum +. (1. -. f.psupport /. quota_support) *. (f.pamount -. prior) in
	      (* don't eliminate something which is only one half-dollar from quota *)
	      (* unless it's a very small level *)
	      if dist > g.round_to_nearest /. 2. || dist > 0.1 *. f.pamount then
		consider_funding_levels p fs f.pamount dist (Some (p,f,prior,dist))
	      else
		consider_funding_levels p fs f.pamount dist res
	    end	
	  end
	  else res
    end
  in
  let consider_project p =
    begin match consider_funding_levels p p.fundings 0. 0. None with
      | None -> ()
      | Some ((_,f,_,dist) as candidate) ->
	  begin match !lowest with
	    | [] ->
		lowest := [candidate]
	    | ((_,f',_,dist') as last_lowest)::rest ->
		if dist > dist' ||
		  (dist = dist' && f.pamount > f'.pamount) then
		    lowest := [candidate; last_lowest]
		else begin match rest with
		  | [] ->
		      lowest := [last_lowest; candidate]
		  | (_,f',_,dist')::_ ->
		      if dist > dist' then
			lowest := [last_lowest; candidate]
		end
	  end;
    end
  in
  List.iter consider_project g.projects;
  begin match !lowest with
    | [(p,f,prior,dist); (_,_,_,dist')] when dist -. !surplus > dist' ->
	eliminate g p f prior;
	None
    | _ -> 
	Some (!surplus,!lowest)
  end

(**********************************************************************
 * Iterate while large enough changes are occuring
 **********************************************************************)
let rec many_iterations (g:game) : unit =
  one_iteration g;
  while change_in_projects g do one_iteration g done

(**********************************************************************
 * Eliminations
 **********************************************************************)
let eliminate_worst_funding_level ?(even_if_close:bool=false) (g:game) : bool =
  let best = ref None in
  let rec consider_funding_levels p fs prior dist_accum =
    begin match fs with
      | [] -> ()
      | f :: fs ->
	  if f.pamount < p.eliminated && f.psupport > 0. then begin
	    let dist = dist_accum +. (1. -. f.psupport /. quota_support g) *. (f.pamount -. prior) in
	    let dist = max 0. dist in
	    (* don't eliminate something which is only one half-dollar from quota *)
	    (* unless it's a very small level *)
	    if dist > (if even_if_close then 0. else g.round_to_nearest /. 2.) 
	      || dist > 0.1 *. f.pamount then
	      begin match !best with
		| None ->
		    best := Some (p,f,prior,dist)
		| Some (_,f',_,dist') ->
		    if dist > dist' ||
		      (dist = dist' && f.pamount > f'.pamount) then
			best := Some (p,f,prior,dist)
	      end;
	    consider_funding_levels p fs f.pamount dist
	  end
    end
  in
  List.iter (fun p -> consider_funding_levels p p.fundings 0. 0.) g.projects;
  begin match !best with
    | None -> false
    | Some (p,f,prior,dist) ->
	eliminate g p f prior;
	true
  end

let total_winners (g:game) : currency =
  let res = ref 0. in
  let rec loop_fundings fs best_with_nonzero_support =
    begin match fs with
      | [] -> best_with_nonzero_support
      | f::fs -> 
	  if f.psupport <= 0. 
	  then best_with_nonzero_support 
	  else loop_fundings fs f.pamount
    end
  in
  List.iter (fun p -> res := !res +. loop_fundings p.fundings 0.) g.projects;
  !res

let eliminate_zero_support_projects (g:game) : unit =
  List.iter begin fun p ->
    begin match p.fundings with
      | [] -> p.eliminated <- 0.
      | f::_ -> 
	  if f.psupport <= 0. then begin
	    p.eliminated <- 0.;
	    p.fundings <- []
	  end
    end
  end g.projects

let play' (g:game) : unit =
  many_iterations g;
  while eliminate_worst_funding_level g do many_iterations g done

let rec play (g:game) : unit =
  one_iteration g;
  while
    begin match short_cut_exclusion_search g with
      | None -> true
      | Some (surplus,lowest) -> 
	  if surplus < g.round_to_nearest /. 10. then
	    begin match lowest with
	      | (p,f,prior,_)::_ -> eliminate g p f prior; true
	      | [] -> false
	    end
	  else true
    end
  do 
    one_iteration g
  done;
  cleanup g
   
and cleanup (g:game) : unit =
  if total_winners g > g.total then begin
    assert (eliminate_worst_funding_level ~even_if_close:true g);
    play g
  end else eliminate_zero_support_projects g

