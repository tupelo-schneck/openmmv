(* TODO: what to do with non-transferable? *)

let epsilon = 0.000000001

type currency = float
type support = float
type utility = currency -> currency -> currency -> support (* flat_before, spent_before, flat_here *)

type funding_level = {
  mutable pamount : currency; (* mutable for ease of elimination *)
  mutable psize : currency; (* amount - size is next lowest funding level *)
  mutable pvote : currency;
  mutable plast_vote : currency;
  mutable psupport : support;
  mutable plast_support : support;
  (* keep_value is quota_support / plast_support *)
}

let new_initial_funding_level amount prior = {
  pamount = amount;
  psize = amount -. prior;
  pvote = 0.;
  plast_vote = 0.;
  psupport = 0.;
  plast_support = 0.;
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
  bprior : currency; (* how much has already gone to this project on this ballot *)
  mutable actual_amount : currency; 
  mutable bsupport : support;
  mutable contribution : currency;

  mutable project : project option;
}

type ballot_priority = {
  mutable items : ballot_item list
}

type ballot = {
  ballotid : int;
  bname : string;
  weight : float;
  mutable priorities : ballot_priority list;
}

type game = {
  total : currency;
  projects : project list;
  utility : utility option;
  quota : float; (* a fraction of the number of players *)
  mutable ballots : ballot list;
  round_to_nearest : currency; (* used for project funding levels *)

  mutable quota_support : support;
  mutable share : currency;
  mutable half_round_to_nearest : currency;
}

(* really more of a floor *)
let round (g:game) (f:float) =
  floor (f /. g.round_to_nearest) *. g.round_to_nearest

let float_players (g:game) : float = 
  let res = ref 0. in
  List.iter (fun b -> res := !res +. b.weight) g.ballots;
  !res

let initialize_game (g:game) : unit =
  let players = float_players g in
  g.quota_support <- max 1.0 (g.quota *. players);
  g.share <- g.total /. players;
  g.half_round_to_nearest <- g.round_to_nearest /. 2.

let support (g:game) (flat_before:currency) (spent_before:currency) (flat_here:currency) : support =
  let spend_limit = g.share -. spent_before in
  if spend_limit <= epsilon then 0. else
    begin match g.utility with
      | None -> 
	  if flat_here > spend_limit then spend_limit /. flat_here else 1.0
      | Some f ->
	  let support = 
	    f (flat_before /. g.share) (spent_before /. g.share) (flat_here /. g.share)
	  in
	  let support = max 0. support in
	  if support *. flat_here > spend_limit then spend_limit /. flat_here else support
    end

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
  List.fold_left (fun acc b -> acc +. b.contribution) 0. bp.items

let flat_on_ballot_priority (bp:ballot_priority) : currency =
  List.fold_left (fun acc b -> acc +. 
		    if b.bsupport <= 0. then 0. else b.contribution /. b.bsupport) 0. bp.items

let spent_on_ballot (b:ballot) : currency =
  b.weight *. List.fold_left (fun acc bp -> acc +. spent_on_ballot_priority bp) 0. b.priorities

(* Insert a new funding level for project p of the given amount *)
let add_new_funding_level_if_needed (p:project) (amount:currency) : unit =
  if amount >= p.eliminated then () else
  let new_funding_level f_opt prior = 
    begin match f_opt with
      | None -> new_initial_funding_level amount prior
      | Some f -> 
	  let old_size = f.psize in
	  let f_size = f.pamount -. amount in
	  let new_size = amount -. prior in
	  let old_vote = f.pvote in
	  let old_last_vote = f.plast_vote in
	  f.pvote <- old_vote *. f_size /. old_size;
	  f.plast_vote <- old_last_vote *. f_size /. old_size;
	  f.psize <- f_size;
	  {f with 
	     pvote = old_vote *. new_size /. old_size; 
	     plast_vote = old_last_vote *. new_size /. old_size;
	     pamount = amount; 
	     psize = new_size}
    end 
  in
  let rec loop (before:funding_level list) (after:funding_level list) (prior:currency) : unit =
    begin match after with
      | [] -> p.fundings <- List.rev_append before [new_funding_level None prior]
      | f :: fs ->
	  if f.pamount < amount then loop (f :: before) fs f.pamount
	  else if f.pamount = amount then ()
	  else p.fundings <- List.rev_append before (new_funding_level (Some f) prior :: after)
    end
  in
  loop [] p.fundings 0.

let add_support_for_ballot_item (g:game) (b:ballot_item) (weight:float) : unit =
  let p = project_for_ballot_item g b in
  let rec loop fs =
    begin match fs with
      | [] -> ()
      | f :: fs -> 
	  if f.pamount > p.eliminated || f.pamount > b.actual_amount then ()
	  else if f.pamount <= b.bprior then loop fs
	  else begin
	    f.psupport <- f.psupport +. weight *. b.bsupport;
	    let f_support = max g.quota_support f.plast_support in
	    f.pvote <- f.pvote +. weight *. b.bsupport *.
	      f.psize /. f_support;
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
  b.actual_amount <- 0.;
  b.contribution <- 0.;
  let rec loop fs =
    begin match fs with
      | [] -> ()
      | f :: fs ->
	  (* if eliminated or past what this voter wants, done *)
	  if f.pamount > p.eliminated || f.pamount > b.bamount then ()
	  (* skipping over funding levels below b.prior *)
	  else if f.pamount <= b.bprior then loop fs
	  (* at this point, we're looking at a real funding level between b.bprior
	     and b.bamount *)
	  else begin
	    b.actual_amount <- f.pamount;
	    let f_support = max g.quota_support f.plast_support in
	    let this_contribution = f.psize /. f_support in
	    b.contribution <- b.contribution +. this_contribution;
	    loop fs
	  end
    end
  in
  loop p.fundings

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
  (flat_sofar:currency) (spent_sofar:currency) (weight:float) : currency * currency =
  List.iter (get_flat_contribution_of_ballot_item g) bp.items;
  let flat_here = spent_on_ballot_priority bp in
  let support = support g flat_sofar spent_sofar flat_here in
  List.iter begin fun b ->
    b.bsupport <- support;
    b.contribution <- support *. b.contribution;
    add_support_for_ballot_item g b weight
  end bp.items;
  flat_here, support *. flat_here

let adjust_ballot (g:game) (b:ballot) : unit =
  let rec loop_priorities priorities flat_sofar spent_sofar =
    if g.share -. spent_sofar <= epsilon then () else
    begin match priorities with
      | [] -> ()
      | bp::bps ->
	  let flat_here, spent_here = adjust_ballot_priority g bp flat_sofar spent_sofar b.weight
	  in
	  loop_priorities bps (flat_sofar +. flat_here) (spent_sofar +. spent_here)
    end
  in
  loop_priorities b.priorities 0. 0.

let renew_project_supports (p:project) : unit =
  List.iter begin fun f -> 
    f.plast_support <- f.psupport;
    f.psupport <- 0.;
    f.plast_vote <- f.pvote;
    f.pvote <- 0.
  end p.fundings

(**********************************************************************
 * Perform one iteration over all ballots
 **********************************************************************)
let one_iteration (g:game) : unit =
  List.iter renew_project_supports g.projects;
  List.iter (adjust_ballot g) g.ballots


(**********************************************************************
 * Perform an elimination.
 * Precondition: f is largest funding level of p
 **********************************************************************)
let eliminate (g:game) (p:project) (f:funding_level) (new_amount:currency) : unit =
(*  let t = Util.process_time () in
  print_string "Elimination at ";
  print_float t;
  print_endline " seconds";
  flush stdout;
*)  
  p.eliminated <- f.pamount;
  if f.pamount <= p.minimum then p.fundings <- [] else begin
    let new_amount = min new_amount (f.pamount -. g.round_to_nearest) in
    let new_amount = round g new_amount in
    let new_amount = if new_amount < p.minimum then p.minimum else new_amount in
    if new_amount <= f.pamount -. f.psize 
    then p.fundings <- List.filter (fun f' -> f' != f) p.fundings
    else begin
      let old_size = f.psize in
      f.psize <- old_size -. f.pamount +. new_amount;
      f.pamount <- new_amount;
      f.pvote <- f.pvote *. f.psize /. old_size;
      f.plast_vote <- f.plast_vote *. f.psize /. old_size
    end
  end

let surplus_or_change ?(change:bool=false) ?(limit:currency = infinity) (g:game) : currency =
  let rec loop_funding_levels fs sofar =
    if sofar >= limit then limit else
    begin match fs with
      | [] -> sofar
      | f::fs -> 
	  let contribution = 
	    if change then abs_float (f.pvote -. f.plast_vote)
	    else max 0. (f.pvote -. f.psize)
	  in
	  loop_funding_levels fs (sofar +. contribution)
    end
  in
  let rec loop_projects ps sofar =
    if sofar >= limit then limit else
    begin match ps with
      | [] -> sofar
      | p::ps ->
	  loop_projects ps (loop_funding_levels p.fundings sofar)
    end
  in
  loop_projects g.projects 0.

let surplus (g:game) : currency = surplus_or_change g

let change_in_projects (g:game) : bool =
  surplus_or_change g ~change:true ~limit:g.half_round_to_nearest >= g.half_round_to_nearest

(* None if exclusion made; Some change otherwise *)
(* Need to find lowest, next lowest, surplus *)
let short_cut_exclusion_search (g:game) (* : currency option *) =
  let surplus = surplus g in
  let lowest = ref [] in
  let rec consider_funding_levels p fs dist_accum res =
    begin match fs with
      | [] -> res
      | f :: fs ->
	  if f.pamount < p.eliminated && f.pvote > 0. then begin
	    if f.pvote >= f.psize then begin
	      consider_funding_levels p fs 0. None
	    end else begin
	      let dist = dist_accum +. f.psize -. f.pvote in 
	      (* don't eliminate something which is only one half-dollar from quota *)
	      (* unless it's a very small level *)
	      if dist > g.half_round_to_nearest || dist > 0.1 *. f.pamount then
		consider_funding_levels p fs dist (Some (p,f,dist))
	      else
		consider_funding_levels p fs dist res
	    end	
	  end
	  else res
    end
  in
  let cmp (_,f1,dist1) (_,f2,dist2) =
    let res =
      if dist1 = dist2 then f2.pamount -. f1.pamount else dist2 -. dist1
    in
    if res < 0. then -1 
    else if res = 0. then 0
    else 1
  in
  let consider_project p =
    begin match consider_funding_levels p p.fundings 0. None with
      | None -> ()
      | Some candidate ->
	  lowest := List.merge cmp [candidate] !lowest;
	  begin match !lowest with
	    | a::b::_::_ -> lowest := [a;b]
	    | _ -> ()
	  end
    end
  in
  List.iter consider_project g.projects;
  begin match !lowest with
    | [(p,f,dist); (_,_,dist')] when dist -. surplus > dist' ->
(* Here we calculate the new amount which is lowest such that if you gave it
 * all the surplus, it would still be farther than dist'.  The fiddly calculation
 * is because amount, size and vote all change for the funding level *)
	let new_amount_num = 
	  f.psize *. (dist' +. surplus -. dist +. f.pamount) -. f.pvote *. f.pamount
	in
	let new_amount_den = f.psize -. f.pvote in
	let new_amount = new_amount_num /. new_amount_den in
	eliminate g p f new_amount;
	None
    | _ -> 
	Some (surplus,!lowest)
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
  let rec consider_funding_levels p fs dist_accum =
    begin match fs with
      | [] -> ()
      | f :: fs ->
	  if f.pamount < p.eliminated && f.pvote > 0. then begin
	    let dist = dist_accum +. f.psize -. f.pvote in
	    let dist = max 0. dist in
	    (* don't eliminate something which is only one half-dollar from quota *)
	    (* unless it's a very small level *)
	    if dist > (if even_if_close then 0. else g.half_round_to_nearest) 
	      || dist > 0.1 *. f.pamount then
	      begin match !best with
		| None ->
		    best := Some (p,f,dist)
		| Some (_,f',dist') ->
		    if dist > dist' ||
		      (dist = dist' && f.pamount > f'.pamount) then
			best := Some (p,f,dist)
	      end;
	    consider_funding_levels p fs dist
	  end
    end
  in
  List.iter (fun p -> consider_funding_levels p p.fundings 0.) g.projects;
  begin match !best with
    | None -> false
    | Some (p,f,dist) ->
	eliminate g p f (f.pamount -. g.round_to_nearest);
	true
  end

let total_winners (g:game) : currency =
  let res = ref 0. in
  let rec loop_fundings fs best_with_nonzero_support =
    begin match fs with
      | [] -> best_with_nonzero_support
      | f::fs -> 
	  if f.pvote <= 0. 
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
	  if f.pvote <= 0. then begin
	    p.eliminated <- 0.;
	    p.fundings <- []
	  end
    end
  end g.projects

let play' (g:game) : unit =
  initialize_game g;
  many_iterations g;
  while eliminate_worst_funding_level g do many_iterations g done

let rec play (g:game) : unit =
(*  let t = Util.process_time () in
  print_string "Start at ";
  print_float t;
  print_endline " seconds";
  flush stdout;
*)
  initialize_game g;
  one_iteration g;
  while
    begin match short_cut_exclusion_search g with
      | None -> true
      | Some (_,[]) -> false
      | Some (surplus,_) when surplus >= g.round_to_nearest /. 10. -> true
      | Some (_, (p,f,_)::_) ->
	  eliminate g p f (f.pamount -. g.round_to_nearest); true
    end
  do 
    one_iteration g
  done;
  cleanup g
(*  ;
  let t = Util.process_time () in
  print_string "Finished game at "; 
  print_float t;
  print_endline " seconds";
  flush stdout
*)
 
and cleanup (g:game) : unit =
  if total_winners g > g.total then begin
    assert (eliminate_worst_funding_level ~even_if_close:true g);
    play g
  end else eliminate_zero_support_projects g
