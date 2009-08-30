from projectBallots import *
from BltpBallotLoader import *
from projectElection import *
from report import TextReport
b = Ballots()
loader = BltpBallotLoader()
loader.load(b,"ballot_files/case_x.bltp")
e = ProjectElection(b)


def run():
  e.runElection()

def prin():
  r = TextReport(e)
  print r.generateReport()

