external register_utility : Mmv.utility -> unit = "ml_register_utility"

let _ = register_utility (fun a x b -> 1.)

let _ = Callback.register "run_election" Mmv.play
