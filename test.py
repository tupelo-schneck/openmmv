from projectBallots import *
from BltpBallotLoader import *
from projectElection import *
from report import TextReport
b = Ballots()
loader = BltpBallotLoader()
loader.load(b,"ballot_files/otra2009/2009-10-05.bltp")
e = ProjectElection(b)
#e.countingMethod = "Meek"

def run():
  e.runElection()

def prin():
  r = TextReport(e)
  print r.generateReport()

