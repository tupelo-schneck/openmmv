import elections
g = elections.Election()
g.import_bltp("ballot_files/ICPSR_election_data/blt/a20.blt")
#g.run_election()
import pycamlmmv
pycamlmmv.send_election(g)
