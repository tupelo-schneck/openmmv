let letters = "ABCDEFGHIJKLMNOP"
let names = 
  let res = ref [] in
  for i = 0 to 15 do
    res := String.make 1 letters.[15 - i] :: !res
  done;
  !res

let projects =
  List.map (fun name ->
	      { projectid = Char.code(name.[0]) - Char.code('A');
		pname = name;
		minimum = if String.contains "EFGH" name.[0] then 10. else if name = "M" then 25. else 25.;
		maximum = if String.contains "EFGH" name.[0] then 10. else 25.;
		eliminated = infinity;
		fundings = [] }) names

let ballot_stubs = [
[1;3;4;2;6;7;8;5;12;11;9;10;14;15;16;13];
[1;3;4;2;6;7;8;5;12;11;9;10;14;15;16;13];
[1;3;4;2;6;7;8;5;12;11;9;10;14;15;16;13];
[1;3;4;2;6;7;8;5;12;11;9;10;14;15;16;13];
[1;3;4;2;6;7;8;5;12;11;9;10;14;15;16;13];
[4;2;3;1;6;7;8;5;12;11;9;10;14;15;16;13];
[1;3;4;2;6;7;8;5;12;11;9;10;14;15;16;13];
[5;7;8;6;2;3;4;1;12;11;9;10;14;15;16;13];
[5;9;11;7;2;3;4;1;12;10;6;8;14;15;16;13];
[5;9;11;7;2;3;4;1;12;10;6;8;14;15;16;13];
[5;9;10;7;3;1;2;4;12;11;6;8;14;15;16;13];
[9;11;12;10;2;3;4;1;8;7;5;6;14;15;16;13];
[9;11;12;10;2;3;4;1;8;7;5;6;14;15;16;13];
[13;15;16;14;10;11;12;9;4;3;1;2;6;7;8;5];
[13;15;16;14;7;9;10;5;4;3;1;2;8;11;12;6];
[13;15;16;14;7;9;11;5;4;3;1;2;8;10;12;6];
[13;15;16;14;8;10;11;5;3;2;4;1;7;9;12;6];
[13;15;16;14;6;7;8;5;4;3;1;2;10;11;12;9];
[13;15;16;14;10;11;12;9;4;3;1;2;6;7;8;5];
[13;15;16;14;10;11;12;9;8;7;5;6;2;3;4;1];
[13;15;16;14;10;11;12;9;8;7;5;6;2;3;4;1];
[13;15;16;14;10;11;12;9;8;7;5;6;2;3;4;1];
[13;15;16;14;10;11;12;9;8;7;5;6;1;3;4;2];
[13;15;16;14;10;11;12;9;8;7;5;6;2;3;4;1];
[13;15;16;14;10;11;12;9;8;7;5;6;2;3;4;1]]

let position_to_item n =
  let p = List.nth projects n in
  { bprojectid = p.projectid;
    bamount = p.maximum ;
    prior = 0.;
    actual_amount = 0.;
    bsupport = 0.;
    contribution = 0. }

let list_to_priorities l =
  let pairs = 
    let rec aux pos l =
      begin match l with
	| [] -> []
	| n::ns -> (n,position_to_item pos) :: aux (pos + 1) ns
      end
    in
    aux 0 l
  in
  let sorted_pairs = List.sort (fun (a,_) (b,_) -> compare a b) pairs in
  let _,items = List.split sorted_pairs in
  List.map (fun bi -> [bi]) items

let ballots =
  let rec aux n bs =
    begin match bs with
      | [] -> []
      | b::bs -> { ballotid = n; bname = string_of_int n; weight = 1.0; priorities = list_to_priorities b } :: aux (n+1) bs
    end
  in
  aux 1 ballot_stubs

let utility1 a x b = (*2. -. 2. *. x*)
  let b = min b (1. -. a) in
  (2. -. a -. (a +. b))
let utility2 a x b = (*3. -. 3. *. sqrt x*)
  let b = min b (1. -. a) in
  if b = 0. then 0. else
  let antideriv x = 3. *. x -. 2. *. x *. sqrt x in
  (antideriv (a +. b) -. antideriv a) /. b
let utility3 a x b = 1.
let utility4 a x b = 2.

let fix_util f a x b = max (f a x b) 1.


let game =
  {total = 190.;
   projects = projects;
   utility = utility1;
   quota = 6. /. 25.;
   ballots = ballots;
   round_to_nearest = 1.}

let print_ballot ?(all=false) b =
  let id_to_name n = String.make 1 (Char.chr(n + Char.code 'A')) in
  Printf.printf "\nBallot: %s\n" b.bname;
  List.iter (fun bp ->
	       List.iter (fun bi ->
			    if bi.contribution > 0. || all then
			      Printf.printf "%s: $%.2f [%.2f]\n" (id_to_name bi.bprojectid) bi.contribution bi.bsupport)
	       bp) b.priorities

let total_contributions_to_project_named g pname =
  let projectid = (List.find (fun p -> p.pname = pname) g.projects).projectid 
  in
  let res = ref 0. in
  let do_item b bi = 
    if bi.bprojectid = projectid 
    then res := !res +. b.weight *. bi.contribution 
  in
  List.iter (fun b -> List.iter (fun bp -> List.iter (do_item b) bp) 
             b.priorities) g.ballots;
  !res

let find_ballot_item which b =
  let find_in_bp bp =
    List.find (fun bi -> bi.bprojectid = which) bp
  in
  let rec aux bps =
    begin match bps with
      | [] -> assert false
      | bp::bps -> 
	  begin try
	    find_in_bp bp
	  with
	      Not_found -> aux bps
	  end
    end
  in
  aux b.priorities

let print_project game p =
  Printf.printf "%s: " p.pname;
  List.iter (fun b -> Printf.printf "$%.2f " (find_ballot_item p.projectid b).contribution) game.ballots;
  Printf.printf "\n"

let print_project' game p =
  let f = List.hd p.fundings in
  Printf.printf "%s: %.2f [%.2f]\n" p.pname f.pamount f.psupport

let winners game =
  List.filter (fun p -> p.fundings <> [] && (List.hd p.fundings).pamount < p.eliminated) game.projects

let winners' game =
  List.filter (fun p -> p.fundings <> [] && (List.hd p.fundings).psupport >= quota_support game) game.projects


(*
List.map (fun p -> (p.pname, total_contributions_to_project_named g p.pname)) (winners g);;

*)
