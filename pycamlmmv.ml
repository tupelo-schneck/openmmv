external register_utility : Mmv.utility option -> unit = "ml_register_utility"

let _ = register_utility None

let _ = 
  Callback.register "run_election" Mmv.play;
  Callback.register "step_election" Mmv.step_election


let gref : Mmv.game option ref = ref None
let _ = Callback.register "send_election" (fun g -> gref := Some g)
