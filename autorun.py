import elections
g = elections.Election()
g.import_bltp("ICPSR_election_data/blt/a85.blt")
#g.run_election()
import pycamlmmv
pycamlmmv.send_election(g)
