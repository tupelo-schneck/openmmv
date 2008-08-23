import elections
g = elections.Election()
g.import_bltp("wikipedia3.bltp")
#g.run_election()
import pycamlmmv
pycamlmmv.send_election(g)
