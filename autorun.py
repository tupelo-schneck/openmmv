import elections
g = elections.Election()
g.import_bltp("ballot.bltp")
import pycamlmmv
pycamlmmv.run_election(g)
