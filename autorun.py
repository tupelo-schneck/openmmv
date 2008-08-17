import elections
g = elections.Election()
g.import_bltp("ballot.bltp")
#g.run_election()
import pycamlmmv
pycamlmmv.send_election(g)
