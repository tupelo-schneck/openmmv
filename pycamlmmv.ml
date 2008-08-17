external register_utility : Mmv.utility -> unit = "ml_register_utility"

let _ = register_utility (fun a x b -> 1.)

let _ = Callback.register "run_election" Mmv.play


let gref : Mmv.game option ref = ref None
let _ = Callback.register "send_election" (fun g -> gref := Some g)
