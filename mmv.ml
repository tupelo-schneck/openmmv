(* TODO: what to do with non-transferable? *)

let allow_multiple_eliminations = true

let epsilon = 0.000000001

let sign_of_float f =
  if f < 0. then -1 
  else if f = 0. then 0
  else 1


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

type result_item = {
  rprojectid : int;
  ramount : currency;
  rwinner : bool;
}

type game_state = 
  | Initial 
  | FoundWinner 
  | FoundLoser 
  | EliminatedLosers 
  | AtCleanup
  | EliminatedNearWinner
  | AllowedNearWinners
  | Done

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
  mutable surplus_precision : currency;
  
  mutable results : result_item list;
  mutable state : game_state;
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
  g.share <- g.total /. players;
  g.half_round_to_nearest <- g.round_to_nearest /. 2.;
  g.surplus_precision <- min (0.0001 *. g.round_to_nearest) (0.0001 *. g.share);
  let least_minimum = ref infinity in
  List.iter (fun p -> least_minimum := min !least_minimum p.minimum) g.projects;
  (* Try to get contributions at support one closer to share when share is small *)
  g.quota_support <- max (max 1.0 (!least_minimum /. g.share)) (g.quota *. players)


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
	    f.psupport <- f.psupport +. weight *. b.bsupport
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

let finalize_projects (g:game) : unit =
  List.iter begin fun p ->
    List.iter begin fun f ->
      let f_support = max g.quota_support f.plast_support in
      f.pvote <- f.psize *. f.psupport /. f_support;
      if f.psupport >= g.quota_support 
	&& f.plast_support < g.quota_support then begin
	g.results <- { rprojectid = p.projectid; ramount = f.pamount; rwinner = true } ::
	  g.results
      end
    end p.fundings
  end g.projects
	
(**********************************************************************
 * Perform one iteration over all ballots
 **********************************************************************)
let one_iteration (g:game) : unit =
  List.iter renew_project_supports g.projects;
  List.iter (adjust_ballot g) g.ballots;
  finalize_projects g


let fully_eliminate (g:game) (p:project) : unit =
  let rec consider_fundings fs dist_accum max_keep =
    begin match fs with
      | [] -> ()
      | f :: fs ->
	  if f.pvote >= f.psize then consider_fundings fs 0. f.pamount
	  else begin
	    let dist = dist_accum +. f.psize -. f.pvote in 
	    if dist > g.half_round_to_nearest || dist > 0.1 *. f.pamount then begin
	      p.fundings <- List.filter (fun f -> f.pamount <= max_keep) p.fundings;
	      p.eliminated <- max_keep +. g.half_round_to_nearest;
	      g.results <- { rprojectid = p.projectid; ramount = p.eliminated; rwinner = false } ::
		g.results
	    end else
	      consider_fundings fs dist f.pamount
	  end
    end
  in
  consider_fundings p.fundings 0. 0.

(**********************************************************************
 * Perform an elimination.
 **********************************************************************)
let eliminate (g:game) (p:project) (f:funding_level) (new_amount:currency) : unit =
  if f.pamount <= p.minimum then begin
    p.fundings <- [];
    p.eliminated <- 0.
  end else begin
    let new_amount = min new_amount (f.pamount -. g.round_to_nearest) in
    let new_amount = round g new_amount in
    let new_amount = max p.minimum new_amount in
    let rec funding_level_with_new_amount fs =
      begin match fs with
	| [] -> assert false
	| f :: fs ->
	    if f.pamount < new_amount then funding_level_with_new_amount fs 
	    else f
      end
    in
    let f = funding_level_with_new_amount p.fundings in
    p.fundings <- List.filter (fun f' -> f'.pamount <= f.pamount) p.fundings;
    p.eliminated <- new_amount +. g.half_round_to_nearest;
    let old_size = f.psize in
    f.psize <- old_size -. f.pamount +. new_amount;
    f.pamount <- new_amount;
    f.pvote <- f.pvote *. f.psize /. old_size;
    f.plast_vote <- f.plast_vote *. f.psize /. old_size;
  end;
  g.results <- { rprojectid = p.projectid; ramount = p.eliminated; rwinner = false } ::
    g.results

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
  surplus_or_change g ~change:true ~limit:g.surplus_precision >= g.surplus_precision

let elimination_search ?(even_if_close:bool=false) (g:game) : 
  (project * funding_level * currency * currency) list =
  let rec consider_funding_levels p fs dist_accum elim_accum =
    begin match fs with
      | [] -> []
      | f :: fs ->
	  if f.pvote >= f.psize then begin
	    consider_funding_levels p fs 0. 0.
	  end else begin
	    let dist = dist_accum +. f.psize -. f.pvote in 
	    let elim = elim_accum +. f.pvote in
	    if fs = [] then
	      if even_if_close || dist > g.half_round_to_nearest || dist > 0.1 *. f.pamount then
		[(p,f,dist,elim)]
	      else []
	    else
	      consider_funding_levels p fs dist elim
	  end
    end
  in
  let cmp (_,f1,dist1,elim1) (_,f2,dist2,elim2) =
    sign_of_float (if dist1 = dist2 then elim2 -. elim1 else dist2 -. dist1)
  in
  List.fold_left begin fun lowest p ->
    let lowest = List.merge cmp (consider_funding_levels p p.fundings 0. 0.) lowest in
    if allow_multiple_eliminations then lowest else
    begin match lowest with
      | a::b::_::_ -> [a;b]
      | _ -> lowest
    end
  end [] g.projects

(* returns whether to continue iterations *)
let perform_elimination ?(even_if_close:bool=false) ?(really:bool=true) (g:game) : bool =
  let eliminables = elimination_search ~even_if_close g in
  let surplus = surplus g in
  let break_tie () =
    (* misnomer, doesn't really break the tie, it just picks one *)
    if surplus > g.surplus_precision then really else
    begin match eliminables with
      | [] -> false
      | (p,f,_,_) :: _ ->
	  if really then eliminate g p f (f.pamount -. g.round_to_nearest);
	  true
    end
  in
  if even_if_close then break_tie () else
  let rec do_full_elims_before p_limit es =
    begin match es with
      | [] -> assert false
      | (p,_,_,_) :: es ->
	  if p == p_limit then ()
	  else begin
	    fully_eliminate g p;
	    do_full_elims_before p_limit es
	  end
    end
  in
  let rec consider_elims es elim_accum =
    begin match es with 
      | (p,f,dist,elim) :: es ->
	  let new_dist = dist -. surplus -. elim_accum in
	  if new_dist <= epsilon then break_tie () else
	  let dist' =
	    begin match es with
	      | [] ->
		  if even_if_close then epsilon else 
		    min g.half_round_to_nearest (0.1 *. f.pamount)
	      | (_,_,dist',_) :: _ -> dist'
	    end
	  in
	  if new_dist <= dist' then begin 
	    if allow_multiple_eliminations
	    then consider_elims es (elim_accum +. elim)
	    else break_tie ()
	  end else begin
	    if really then begin
	      do_full_elims_before p eliminables;
	      let new_amount = f.pamount -. (dist -. surplus -. elim_accum -. dist') in
	      eliminate g p f new_amount
	    end;
	    true
	  end
      | [] -> break_tie ()
    end
  in
  consider_elims eliminables 0.

(**********************************************************************
 * Iterate while large enough changes are occuring
 **********************************************************************)
let rec many_iterations (g:game) : unit =
  one_iteration g;
  while change_in_projects g do one_iteration g done

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

let rec play (g:game) : unit =
  initialize_game g;
  one_iteration g;
  while perform_elimination g do
    one_iteration g
  done;
  cleanup g
 
and cleanup (g:game) : unit =
  if total_winners g > g.total then begin
    assert (perform_elimination ~even_if_close:true g);
    play g
  end else begin 
    eliminate_zero_support_projects g;
    (* anything left is a default winner *)
    List.iter begin fun p ->
      let len = List.length p.fundings in
      if len > 0 then begin
	let f = List.nth p.fundings (len - 1) in
	if f.psupport < g.quota_support then
	  g.results <- { rprojectid = p.projectid; ramount = f.pamount; rwinner = true } ::
	    g.results
      end
    end g.projects;
    g.state <- Done
  end

let step_election (g:game) : unit =
  initialize_game g;
  let iterations () =
    (* take steps until something interesting *)
    let old_results = g.results in
    if g.state <> FoundWinner then one_iteration g;
    g.state <- Initial;
    while g.state = Initial do
      if g.results != old_results then g.state <- FoundWinner
      else if perform_elimination ~really:false g then g.state <- FoundLoser
      else if surplus g <= g.surplus_precision then g.state <- AtCleanup
      else one_iteration g
    done
  in
  begin match g.state with
    | Initial | EliminatedLosers | EliminatedNearWinner | FoundWinner ->
	iterations ()
    | FoundLoser ->
	ignore (perform_elimination g);
	g.state <- EliminatedLosers
    | AtCleanup ->
	if total_winners g > g.total then begin
	  assert (perform_elimination ~even_if_close:true g);
	  g.state <- EliminatedNearWinner
	end 
	else begin
	  eliminate_zero_support_projects g;
	  (* anything left is a default winner *)
	  let old_results = g.results in
	  List.iter begin fun p ->
	    let len = List.length p.fundings in
	    if len > 0 then begin
	      let f = List.nth p.fundings (len - 1) in
	      if f.psupport < g.quota_support then
		g.results <- { rprojectid = p.projectid; ramount = f.pamount; rwinner = true } ::
		  g.results
	    end
	  end g.projects;
	  if old_results != g.results then g.state <- AllowedNearWinners else g.state <- Done
	end
    | AllowedNearWinners -> g.state <- Done
    | Done -> ()
  end
