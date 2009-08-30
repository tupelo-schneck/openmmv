"Plugin module for BLTP project ballots."

import re
import string
from projectBallots import ProjectBallots
from plugins import LoaderPlugin

from LoaderPlugins.BltBallotLoader import BltBallotLoader

class BltpBallotLoader(BltBallotLoader,LoaderPlugin):
  "Ballot loader class for BLTP project ballots."

  extensions = ["bltp"]

  #blankLineRE = re.compile(r'^\s*(?:#.*)?$')
  nCandnSeatsRE = re.compile(r'^\s*(\d+)\s+(\d+)(?:\((\d+)\))?\s*(?:#.*)?$')
  #withdrawnRE = re.compile(r'^\s*(-\d+(?:\s+-\d+)*)\s*(?:#.*)?$')
  ballotRE = re.compile(r'^\s*(\d+(?:\s+\d+(?:\(\d+\))?)*)\s+0\s*(?:#.*)?$')
  ballotItemRE = re.compile(r'(\d+)(?:\((\d+)\))?')
  #endOfBallotsRE = re.compile(r'\s*0\s*(?:#.*)?')
  #stringRE = re.compile(r'^\s*"([^"]+)"\s*(?:#.*)?$')
  projRE = re.compile(r'^\s*"([^"]+)"(?:\((\d+)(?:,(\d+))?\))?\s*(?:#.*)?$')

  def __init__(self, fName=""):
    BltBallotLoader.__init__(self,fName)
    self.fName = fName

  ###

  def loadFile(self, ballotList, f):
    "Load BLTP ballot data from a file."

    ballotList.__class__ = ProjectBallots
    ballotList.projectSpecificInit()

    line = self.getNextNonBlankLine(f)
    (numCandidates, numSeats, supportObligation) = self.getNumCandidatesAndSeatsAndSupportObligation(line)
    ballotList.numCandidates = numCandidates
    ballotList.numSeats = numSeats
    ballotList.supportObligation = supportObligation

    line = self.getNextNonBlankLine(f)
    withdrawn = self.getWithdrawnCandidates(line)
    if withdrawn != []:
      ballotList.withdrawn = withdrawn
      line = self.getNextNonBlankLine(f)

    while not self.atEndOfBallots(line):
      (weight, cands, amts) = self.getBallot(line)
      # TypeError if not ProjectBallots
      ballotList.appendProjectBallot(weight, cands, amts)
      line = self.getNextNonBlankLine(f)

    line = self.getNextNonBlankLine(f)
    for c in range(numCandidates):
      (name, minimum, maximum) = self.getCandidateLine(line)
      ballotList.names[c] = name
      # AttributeError if not ProjectBallots
      ballotList.minimum[c] = minimum
      ballotList.maximum[c] = maximum      
      line = self.getNextNonBlankLine(f)

    ballotList.title = self.getTitle(line)
    
    # deal with ballot items without marked amounts
    for i in xrange(ballotList.numWeightedBallots):
      (w, cands, amts) = ballotList.getWeightedProjectBallot(i)
      changed = False
      for j in xrange(len(cands)):
        if amts[j] is None or amts[j]<0:
          amts[j] = ballotList.maximum[cands[j]]
          changed = True
      if changed:
        ballotList.setWeightedProjectBallot(i,w,cands,amts)
      
    
  ###

  def getNumCandidatesAndSeatsAndSupportObligation(self, line):
    out = self.nCandnSeatsRE.match(line)
    if out is None:
      raise RuntimeError, ("""\
Bad format in file when reading the number of
candidates and seats.  Expected two integers but
received:
%s""" % line)
    numCandidates = int(out.group(1))
    numSeats = int(out.group(2))
    supportObligation = out.group(3)
    if not supportObligation is None:
      supportObligation = int(supportObligation)
    return numCandidates, numSeats, supportObligation

  ###

#  def getWithdrawnCandidates(self, line):

  ###

#  def atEndOfBallots(self, line):

  ###

  def getBallot(self, line):
    out = self.ballotRE.match(line)
    if out is None:
      raise RuntimeError, ("""\
Bad format in file.  Expected a ballot but file does not match:
%s""" % line)

    x = out.group(1).split()
    weight = int(x.pop(0))
    cands = []
    amts = []
    for item in x:
      out = self.ballotItemRE.match(item)
      cands.append(int(out.group(1))-1)
      amt = out.group(2)
      if amt is None: amts.append(None)
      else: amts.append(int(amt))
    return (weight, cands, amts)

  ###
  
  def getCandidateLine(self, line):
    out = self.projRE.match(line)
    if out is None:
      raise RuntimeError, ("""\
Bad format in file.  Expected a project name and amounts but file does not match:
%s""" % line)
    name = out.group(1)
    minimum = out.group(2)
    if minimum is None: minimum = 1
    else: minimum = int(minimum)
    maximum = out.group(3)
    if maximum is None: maximum = minimum
    else: maximum = int(maximum)
    return name, minimum, maximum
  
  ###

#  def getTitle(self, line):

  ###
  
#  def getNextNonBlankLine(self, f):

  ###

  def saveFile(self, ballotList, f):
    "Save ballots in BLTP format."

    f.write("%d %d" % (ballotList.numCandidates, ballotList.numSeats))
    if ballotList.supportObligation == None or ballotList.supportObligation == 0:
        f.write("\n")
    else:
        f.write("(%d)\n" % (ballotList.supportObligation))
    
    writeLine = lambda x: f.write("%s\n" % x) # Write text with newline
    quotedLine = lambda x: writeLine('"%s"' % x) # Quoted text with newline
    writeNumbers = lambda x: writeLine(' '.join(map(str, x)))

    if ballotList.withdrawn != []:
      writeNumbers(-(c+1) for c in ballotList.withdrawn)

    for i in xrange(ballotList.numWeightedBallots):
      weight, cands, amts = ballotList.getWeightedProjectBallot(i)
      f.write("%d" % weight)
      for c, a in zip(cands,amts):
        f.write(" %d" % (c+1))
        if a!=ballotList.maximum[c]:
          f.write("(%d)" % a)
      writeLine(" 0")
    writeLine("0") # Marker for end of ballot section

    for name,theMin,theMax in zip(ballotList.names,ballotList.minimum,ballotList.maximum):
      f.write('"%s"' %n)
      if theMin!=1 or theMax!=theMin:
        f.write("(%d" % theMin)
        if theMax!=theMin:
          f.write(",%d)" % theMax)
        else:
          f.write(")")
      f.write("\n")
    quotedLine(ballotList.title)



