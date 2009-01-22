#!/usr/bin/env python

"""Module for counting ranked ballots with a variety of election methods.

Class Election
  Class NonIterative
    Class Approval
    Class Condorcet
    Class SNTV
    Class Bucklin
    Class Borda
  Class Iterative
    Class Bucklin
"""

## Copyright (C) 2003-2008 Jeffrey O'Neill
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

__revision__ = "$Id: NonSTV.py 456 2008-11-09 01:01:52Z jco8 $"

import sys
import re
import string
import math
import random
import textwrap
import version
from types import *
from array import array

##################################################################

class Election:
  """Base class for all election methods.

  This class defines functions and variables used by numerous election
  methods.  It is not itself a complete election method and must be
  sub-classed and further defined."""

  def __init__(self, b):

    # Set default values for options
    self.nSeats = 1
    self.title = ""
    self.date = ""
    self.debug = False
    self.strongTieBreakMethod = "random"
    self.b = b
    self.withdrawn = []
    self.namesPlusWithdrawn = b.names

    # If possible, get information from ballots file
    if vars(b).has_key("nSeats"): self.nSeats = b.nSeats
    if vars(b).has_key("title"): self.title = b.title
    if vars(b).has_key("data"): self.date = b.date
    if vars(b).has_key("withdrawn"): self.withdrawn = b.withdrawn[:]

  ###

  def setOptions(self, debug=None,
                 strongTieBreakMethod=None,
                 prec=None):
    
    if debug != None:
      assert(debug in [True, False])
      self.debug = debug

    if strongTieBreakMethod != None:
      assert(strongTieBreakMethod in ["random", "request", "alpha", "index"])
      self.strongTieBreakMethod = strongTieBreakMethod

    if prec != None:
      self.prec = prec          # Precision for computation

  ###

  def initialize(self):

    self.nRandom = 0           # Number of random choices made
    self.p = 10**self.prec     # Scale factor for computations
    self.setFields()           # Create printf strings
    self.checkMinRequirements()# Check for sufficient candidates and ballots

    # Withdraw candidates if necessary
    if self.withdrawn != []:
      b = self.b
      self.b = b.exciseCandidates(self.withdrawn)

  ###
  
  def joinList(self, list, convert="names"):

    assert(len(list)>0)

    if convert == "names":
      tmp = list[:]
      list = [self.b.names[c] for c in tmp]

    text = string.join(list)
    sep = ", "
    if text.find(",") != -1: sep = "; "
    
    if len(list) == 1:
      txt = list[0]
    elif len(list) == 2:
      txt = list[0] + " and " + list[1]
    else:
      txt = string.join(list[:-1], sep)
      txt += sep + "and " + list[-1]
    return txt

  ###

  def displayValue(self, value):
    "Format a value with specified precision."

    if self.prec > 0:
      return self.nfmt % (value/self.p, value%self.p)
    else:
      return self.nfmt % (value/self.p)

  ###
    
  def setFields(self, fw=None):
    "Set field widths to minimize white space in the output."

    if fw == None:
      # Base field width is the number of digits in the largest integer.
      mm = self.getMaxNumber()
      self.fw = int(math.floor(math.log10(mm))) + 1
    else:
      self.fw = fw
      
    # Increase field width for the decimal point and places after.
    if self.prec > 0:
      self.fw += self.prec + 1
    self.fw = max(self.fw, 4)  # Always want a field width of at least 4.

    # These are the format strings to be used.
    self.sfmt = "%" + str(self.fw) + "." + str(self.fw) + "s"  # %_._s
    if self.prec > 0:
      self.nfmt = "%d.%0" + str(self.prec) + "d" # %d.%0_d
    else:
      self.nfmt = "%d" # %d
 
  ###

  def checkMinRequirements(self):
    "Only attempt to count votes if there are enough candidates and voters."
    
    # some basic minimum requirements
    if (self.b.nCand < 2 or
        self.nSeats < 1 or
        self.b.nCand <= self.nSeats or
        self.b.nBallots <= self.nSeats
        ):
      raise RuntimeError, "Not enough ballots or candidates to run an "\
            "election."

  ###

  def topChoice(self, ballot, candidates):
    "Return the top choice on a ballot among candidates still in the running."

    for c in ballot:
      if c in candidates:
        return c
    return None

  ###

  def findTiedCand(self, cList, mostfewest, values):
    "Return a list of candidates tied for first or last."

    assert(mostfewest in ["most", "fewest"])
    assert(len(cList) > 0)
    tiedCand = []

    # Find a candidate who is winning/losing.  He may be tied with others.
    if mostfewest == "most":
      cList.sort(key=lambda a, f=values: -f[a])
    elif mostfewest == "fewest":
      cList.sort(key=lambda a, f=values: f[a])
    top = cList[0] # first/last place candidate

    # Find the number of candidates who are tied with him.
    for c in cList:
      if values[c] == values[top]:
        tiedCand.append(c)

    return tiedCand

  ###

  def chooseNfromM(self, N, values, cList, what):
    "Choose the N candidates with the most votes."
    
    # This is only used with self.count[c].

    desc = ""
    if len(cList) <= N:
      return (cList, desc)

    chosen = []          # Candidates who will be chosen
    maybe = cList[:]     # Candidates who may be chosen
    maybe.sort(key=lambda a, f=values: -f[a])
    LC = maybe[N]        # First losing candidate
    cutoff = values[LC]

    # All candidates with more than the Nth are chosen
    for c in maybe[:]:
      if values[c] > cutoff:
        maybe.remove(c)
        chosen.append(c)
      elif values[c] < cutoff:
        maybe.remove(c)

    # Break a possible tie for Nth place
    if len(chosen) < N:
      desc = "Candidates %s were tied when when choosing %s. " %\
              (self.joinList(maybe), what)
    while len(chosen) < N:
      (c, desc2) = self.breakStrongTie(maybe)
      desc += desc2
      chosen.append(c)
      maybe.remove(c)

    return (chosen, desc)

  ###

  def breakStrongTie(self, tiedC):
    "Break a strong tie between candidates."

    assert(len(tiedC) >= 1)
    
    # If we have the right number, then return all.
    if len(tiedC) == 1:
      return (tiedC[0], None)
    
    # Break the tie randomly.
    elif self.strongTieBreakMethod == "random":
      c = random.choice(tiedC)
      desc = "Candidate %s was chosen by breaking the tie randomly. " %\
            self.b.names[c]

    # Break the tie alphabetically by candidate's names.
    elif self.strongTieBreakMethod == "alpha":
      tiedC.sort(key=lambda a, f=self.b.names: f[a])
      c = tiedC[0]
      desc = "Candidate %s was chosen by breaking the tie alphabetically. " %\
            self.b.names[c]

    # Break the tie by candidate index number.
    elif self.strongTieBreakMethod == "index":
      tiedC.sort()
      c = tiedC[0]
      desc = "Candidate %s was chosen by breaking the tie by candidate index "\
            "number. " % self.b.names[c]

    else:
      assert(0)

    return (c, desc)

##################################################################
##################################################################
##################################################################

class NonIterative(Election):
  """Base class for all noniterative methods.

  This class defines functions and variables used by noniterative election
  methods.  It is not itself a complete election method and must be
  sub-classed and further defined."""

  def __init__(self, b):

    self.prec = 0
    Election.__init__(self, b)

  ###

  def initialize(self):
    Election.initialize(self)
    self.exhausted = 0
    self.msg = ""
    self.count = [0] * self.b.nCand    

  ###

  def chooseWinners(self):
    "Choose the candidates with the most votes as the winners"
    
    winners = [c for c in range(self.b.nCand) if self.count[c] > 0]
    if len(winners) > self.nSeats:
      (winners, desc) = self.chooseNfromM(self.nSeats, self.count,
                                          winners, "winner")
    return (winners, desc)

  ###

  def getMaxNumber(self):
    "Find the largest number to be printed in the results."

    if "count" in dir(self) and self.count != []:
      m = max(self.count)
      m /= self.p
    else:
      # Election not complete so use max expected count.
      m = self.b.nBallots
       
    return m
  
  ###
    
  def generateTextResults(self, maxWidth=80, style="full"):
    "Pretty print results in text format."

    assert(style in ["full", "table"])

    self.setFields()
    nCol = self.b.nCand
    nCol += 1 # Exhausted
    nSubCol = (maxWidth-2)/(self.fw+1)
    width = 2 + nSubCol*(self.fw+1)
    txt = ""
    
    # Include summary information for full results.
    if style == "full":

      txt += """\
Election title: %s
Method: %s
Number of total ballots: %d
Number of invalid or empty ballots: %d
Number of ballots used in the count: %d
%d candidate running for %d seats.

""" % (self.title,
       self.method + self.options,
       self.b.nBallots + self.b.nBadBallots,
       self.b.nBadBallots, self.b.nBallots, self.b.nCand, self.nSeats)
      
    # Find length of longest string in header
    maxLen = 9
    for c in range(self.b.nCand):
      maxLen = max(maxLen, len(self.b.names[c]))

    # Pad strings for table header
    maxLen += self.fw - (maxLen % self.fw)
    head = []
    for c in range(self.b.nCand):
      head.append(self.b.names[c].ljust(maxLen))
    head.append("Exhausted".ljust(maxLen))

    # Table header
    # nCol is the total number of columns
    # nSubCol is the number of columns that fit in the specified width
    # nRow is the number of rows needed to display all of the columns
    # nSubRow is the number of rows needed to display the full candidate names
    nRow = nCol/nSubCol
    if nCol % nSubCol > 0: nRow += 1
    nSubRow = maxLen/self.fw
    if maxLen % self.fw > 0: nSubRow += 1

    for r in range(nRow):
      for sr in range(nSubRow):
        if r == 0 and sr == 0:
          txt += " R"
        else:
          txt += "  "
        b = sr*self.fw
        e = b + self.fw

        for sc in range(nSubCol):
          h = r*nSubCol + sc
          if h == len(head): break
          txt += "|" + head[h][b:e]
        txt += "\n"

      if r < nRow-1:
        txt += "  |" + ("-"*self.fw + "+")*(nSubCol-1) + "-"*self.fw + "\n"
        
    # Separator line and round/stage number
    txt += "=" * width + "\n"
    txt += "%2d" % 1

    # Candidate vote totals for the round
    for c in range(self.b.nCand):
      txt += ("|" + self.sfmt) % self.displayValue(self.count[c])
      # Skip line if necessary
      if (c+1) % nSubCol == 0: txt += "\n  "

    # Exhausted ballots
    txt += ("|" + self.sfmt) % self.exhausted

    # Surplus and Threshold if dynamic
    txt += "\n"
    txt += "  |" + "-" * (width-3) + "\n"
    txt += textwrap.fill(self.msg, initial_indent="  | ",
                         subsequent_indent="  | ", width=width)
    txt += "\n\n"

    # Include winners for full results
    if style == "full":
      self.winners.sort()
      if len(self.winners) == 0:
        winTxt = "No winners.\n"
      elif len(self.winners) == 1:
        winTxt = "Winner is %s.\n" % self.joinList(self.winners)
      else:
        winTxt = "Winners are %s.\n" % self.joinList(self.winners)
      txt += textwrap.fill(winTxt, width=width)

    return txt

  ###
    
  def generateHTMLResults(self, maxWidth=80):
    "Pretty print results in html format."

    self.setFields()
    
    nCol = self.b.nCand
    nCol += 1 # Exhausted
    width = maxWidth

    txt = """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
        "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<title>%s</title>
</head>
<body>
Election title: %s<br>
Method: %s<br>
Number of total ballots: %d<br>
Number of invalid or empty ballots: %d<br>
Number of ballots used in the count: %d<br>
%d candidate running for %d seats.<br>
<br>

<table border=1 cellspacing=0>

<tr>
<th>R</th>
""" % (self.title, self.title,
       self.method + self.options,
       self.b.nBallots + self.b.nBadBallots,
       self.b.nBadBallots, self.b.nBallots, self.b.nCand, self.nSeats)

    for c in range(self.b.nCand):
      txt += "<th align='center'>%s</th>\n" % self.b.names[c]
    txt += "<th align='center'>%s</th>\n" % "Exhausted"
    txt += "</tr>\n\n"
      
    txt += "<tr>\n"
    txt += "<td align='center' rowspan=2>1</td>\n"
    for c in range(self.b.nCand):
      txt += "<td align='center'>%s</td>\n" % self.displayValue(self.count[c])
    txt += "<td align='center'>%s</td>\n" % self.displayValue(self.exhausted)
    txt += "</tr>\n\n"

    msgTxt = textwrap.fill(self.msg, width=width)
    txt += "<tr><td colspan=%d>%s</td></tr>\n\n" % (nCol, msgTxt)

    txt += "</table>\n\n"

    # Winners
    self.winners.sort()
    if len(self.winners) == 0:
      winTxt = "No winners."
    elif len(self.winners) == 1:
      winTxt = "Winner is %s." % self.joinList(self.winners)
    else:
      winTxt = "Winners are %s." % self.joinList(self.winners)
    winTxt = textwrap.fill(winTxt, width=width)
    winTxt = winTxt.replace("\n", "<br>\n")
    txt += "<p>%s</p>\n\n" % winTxt

    txt += "</body>\n</html>\n"

    return txt

  ###

  def generateERSCSVResults(self, skipDate=False):
    "Return a results sheet in the CVS format used by the ERS."

    assert(self.method != "Condorcet")

    if skipDate:
      today = ""
      v = ""
    else:
      from datetime import date
      today = date.today().strftime("%d %b %Y")
      v = version.v

    fmt1 = "%." + str(self.prec) + "f"
    fmt2 = "%+." + str(self.prec) + "f"
    
    # 8 header lines
    results = ("""\
"Election for","%s"
"Date","%s"
"Number to be elected",%d
"Valid votes",%d
"Invalid votes",%d
"Quota",""" + fmt1 + """
"OpenSTV","%s"
"Election rules","%s"
,
,"First"
"Candidates","Preferences"
""") % (self.b.title, today, self.nSeats, self.b.nBallots,
        self.b.nBadBallots, 0, v, self.method)

    # candidate lines
    for c in range(len(self.namesPlusWithdrawn)):
      
      if c in self.withdrawn:
        # Withdrawn candidates appear in the results even though there is
        # nothing to report.  Handle them separately.
        results += '"%s","Withdrawn",\n' % (self.namesPlusWithdrawn[c])

      else:
        # Since we are looping over all candidates, need to convert the index
        # into the list of non-withdrawn candidates.
        name = self.namesPlusWithdrawn[c]
        cc = self.b.names.index(name)
        results += '"%s",%d,' % (self.b.names[cc], 1.0*self.count[cc]/self.p)
        if cc in self.winners:
          results += '"Elected"'
        results += '\n'

    # non-transferable and totals
    results += '"Non-transferable", ,\n'
    results += '"Totals",' + str(self.b.nBallots) + '\n'

    return results

##################################################################
##################################################################
##################################################################

class Condorcet(NonIterative):
  """\
Method:
  Condorcet Voting

Description:
  Condorcet voting can only be used to elect one candidate.  The
  winner is the candidate who beats all of the other candidates in
  pairwise competitions.  If there is no such winner and a cycle
  occurs, then a completion method is used to choose the winner.

Options:
  There are three choices for the completion method.

Validation:
  Not validated."""
  
  def __init__(self, b):

    self.method = "Condorcet"
    self.completion = "Schwartz Sequential Dropping"
    NonIterative.__init__(self, b)
    self.options = " with %s for the completion method" % self.completion
    
  ###

  def setOptions(self, debug=None, strongTieBreakMethod=None, prec=None,
                 completion=None):
    
    NonIterative.setOptions(self, debug, strongTieBreakMethod, prec)

    if completion != None:
      assert(completion in ["Schwartz Sequential Dropping", "IRV on Smith Set",
                            "Borda on Smith Set"])
      self.completion = completion
      
  ###

  def computePMat(self):
    "Compute the pairwise comparison matrix."

    # Intialize space
    self.pMat = []
    for c in range(self.b.nCand):
      self.pMat.append([0] * self.b.nCand)

    # Compute pMat
    for i in range(len(self.b.packed)):
      remainingC = range(self.b.nCand)
      for c in self.b.packed[i]:
        remainingC.remove(c)
        for d in remainingC:
          self.pMat[c][d] += self.b.weight[i]

  ###

  def computeSmithSet(self):
    "Compute the Smith set."

    dMat = []
    for c in range(self.b.nCand):
      dMat.append([0] * self.b.nCand)

    # compute the Smith set
    # Adapted from code posted by Markus Schulze at
    # http://groups.yahoo.com/group/election-methods-list/message/6493
    self.smithSet = range(self.b.nCand)
    for c in range(self.b.nCand):
      for d in range(self.b.nCand):
        if c != d:
          if self.pMat[c][d] >= self.pMat[d][c]:
            dMat[c][d] = True
          else:
            dMat[c][d] = False
    for c in range(self.b.nCand):
      for d in range(self.b.nCand):
        if c != d:
          for k in range(self.b.nCand):
            if c != k and d != k:
              if dMat[d][c] and dMat[c][k]:
                dMat[d][k] = True
    for c in range(self.b.nCand):
      for d in range(self.b.nCand):
        if c != d:
          if ( (not dMat[c][d]) and
               dMat[d][c] and
               (c in self.smithSet) ):
            self.smithSet.remove(c)
    self.smithSet.sort()

  ###

  def SchwartzSequentialDropping(self):
    "Complete with SSD."

    # Adapted from http://electionmethods.org/CondorcetSSD.py
    # Copyright (C) 2002 by Mike Ossipoff and Russ Paielli
    # GNU General Public License

    # Initialize the defeats matrix: dMat[i][j] gives the magnitude of i's
    # defeat of j. If i doesn't defeat j, then dMat[i][j] == 0.
    dMat = []
    for c in range(self.b.nCand):
      dMat.append([0] * self.b.nCand)

    for c in range(self.b.nCand):
      for d in range(self.b.nCand):
        dMat[c][d] = self.pMat[c][d]
    for c in range(self.b.nCand):
      for d in range(c):
        if self.pMat[c][d] >  self.pMat[d][c]: dMat[d][c] = 0
        if self.pMat[c][d] <  self.pMat[d][c]: dMat[c][d] = 0
        if self.pMat[c][d] == self.pMat[d][c]: dMat[c][d] = dMat[d][c] = 0

    # Determine "beatpath" magnitudes array: dMat[i][j] will be the
    # maximum beatpath magnitudes array. The i,j entry is the greatest
    # magnitude of any beatpath from i to j. A beatpath's magnitude is
    # the magnitude of its weakest defeat.

    changing = 1
    while changing:
      changing = 0
      for c in range(self.b.nCand):
        for d in range(self.b.nCand):
          for k in range(self.b.nCand):
            dmin = min (dMat[c][d], dMat[d][k])
            if dMat[c][k] < dmin:
              dMat[c][k] = dmin
              changing = 1

    ppp = range(self.b.nCand)[:]
    for c in ppp[:]:
      for d in ppp[:]:
        if dMat[d][c] > dMat[c][d] and c in ppp:
          ppp.remove(c)

    txt = "Using Schwartz sequential dropping to choose the winner.\n"
    txt += "Matrix of beatpath magnitudes:\n\n"
    txt += self.returnMat(dMat) + "\n"
    if len(ppp) > 1:
      ppp.sort()
      txt += "Candidates remaining after SSD: %s\n\n" % self.joinList(ppp)
      txt += "Tie broken randomly.\n"
    (c0, desc) = self.breakStrongTie(ppp)
    return (c0, txt)

  ###

  def runElection(self):
    "Count the votes using Condorcet voting."

    self.initialize()
    
    # self.pMat[i][j]: number of votes ranking candidate i over candidate j
    self.computePMat()

    # Even though the Smith Set isn't needed for all completion methods
    # it provides interesting info, so compute it always.
    self.computeSmithSet()

    if len(self.smithSet) == 1:
      c0 = self.smithSet[0]
      self.completionInfo = "No completion necessary since the Smith set "\
                            "has just one candidate."
    else:
      # Do the completion
      if self.completion == "Schwartz Sequential Dropping":
        (c0, self.completionInfo) = self.SchwartzSequentialDropping()
      elif self.completion in ["IRV on Smith Set", "Borda on Smith Set"]:
        # Copy ballots and get rid of candidates not in Smith set
        withdrawList = []
        for c in range(self.b.nCand):
          if (c not in self.smithSet):
            withdrawList.append(c)
        b2 = self.b.exciseCandidates(withdrawList)
        if self.completion == "IRV on Smith Set":
          import STV
          e = STV.IRV(b2)
          e.setOptions(strongTieBreakMethod=self.strongTieBreakMethod)
          e.runElection()
          self.completionInfo = "Using IRV to choose the winner from the "\
                                "Smith set.\n\n"
          self.completionInfo += e.generateTextResults(style="table")
        elif self.completion == "Borda on Smith Set":
          e = Borda(b2)
          e.setOptions(strongTieBreakMethod=self.strongTieBreakMethod)
          e.runElection()
          self.completionInfo = "Using the Borda count to choose the winner "\
                                "from the Smith set.\n\n"
          self.completionInfo += e.generateTextResults(style="table")
        assert(len(e.winners) == 1)
        # The Smith set is sorted.  The winner just determined is the index
        # of the winner in the Smith set.
        c0 = self.smithSet[e.winners[0]]
      else:
        assert(0)

    self.winner = c0

  ###

  def returnMat(self, matrix):
    "Return the P matrix used in computing the Condorcet winner."

    self.setFields()
    nCol = self.b.nCand

    # Spacer
    txt = self.sfmt % ""

    # Candidate names
    for c in range(self.b.nCand):
      txt += ("|" + self.sfmt) % self.b.names[c]
    txt += "\n"

    # Separator line
    txt += "-"*self.fw + ("+" + "-"*self.fw)*nCol + "\n"

    # For each row, candidate name and matrix values
    for c in range(self.b.nCand):
      txt += self.sfmt % self.b.names[c]
      for d in range(self.b.nCand):
        txt += ("|" + self.sfmt) % self.displayValue(matrix[c][d])
      txt += "\n"
      
    return txt

  ###
    
  def getMaxNumber(self):
    "Find the largest number to be printed in the results."

    if "pMat" in dir(self) and self.pMat != []:
      # Election complete so find largest number.
      mm = 0
      for i in range(self.b.nCand):
        m = max(self.pMat[i])
        mm = max(mm, m)
    else:
      # Election not complete so use nBallots.
      mm = self.b.nBallots        

    return mm
  
  ###

  def generateTextResults(self, maxWidth=80):
    "Return a complete election result."

    self.setFields()

    txt = """Election: %s
Method: %s
Completion Method: %s
Number of Ballots: %d
%d candidates running for %d seat.

Pairwise Comparison Matrix:

%s
Smith Set: %s

%s
Winner is %s.
""" % (self.title, self.method, self.completion, self.b.nBallots,
       self.b.nCand, self.nSeats,
       self.returnMat(self.pMat),
       self.joinList(self.smithSet),
       self.completionInfo,
       self.b.names[self.winner]
       )

    return txt

##################################################################

class Approval(NonIterative):
  """\
Method:
  Approval Voting

Description:
  A voter can approve of as many candidates as he or she likes, and
  the candidate approved of by the greatest number of voters is
  elected.  A voter approves of a candidate by listing the candidate
  on the ballot.

Options:
  None.

Validation:
  Not validated."""

  def __init__(self, b):

    self.method = "Approval Voting"
    NonIterative.__init__(self, b)
    self.options = ""

  ###

  def runElection(self):
    "Coun the votes using approval voting."

    self.initialize()
    self.nRounds = 1

    # Count the approvals
    for i, blt in enumerate(self.b.packed):
      for j in range(len(blt)):
        self.count[blt[j]] += self.b.weight[i]

    self.msg += "Count of all approvals. "

    # Choose the winners
    (self.winners, desc) = self.chooseWinners()
    self.msg += desc

##################################################################

class SNTV(NonIterative):
  """\
Method:
  Single Non-Transferable Vote
  
Description:
  Only the first choices are used in counting the ballots, and the
  candidate with the greatest number of first choices is the winner.
  When there is only one seat to be filled, this corresponds to a
  traditional plurality election.  When there is more than one seat to
  be filled, this corresponds to limited voting and provides a simple
  form of proportional representation.
  
Options:
  None.

Validation:
  Not validated."""

  def __init__(self, b):

    self.method = "SNTV"
    NonIterative.__init__(self, b)
    self.options = ""
    
  ###
    
  def runElection(self):
    "Count the votes using SNTV."

    self.initialize()
    self.nRounds = 1

    # Count the first place votes
    for i in xrange(len(self.b.packed)):
      c = self.topChoice(self.b.packed[i], range(self.b.nCand))
      if c == None:
        self.exhausted[0] += self.b.weight[i]
      else:
        self.count[c] += self.b.weight[i]
    self.msg += ("Count of first choices. ")

    # Choose the winners
    (self.winners, desc) = self.chooseWinners()
    self.msg += desc

##################################################################

class Borda(NonIterative):
  """\
Method:
  Borda Count

Description:
  If there are 4 candidates, then a candidate receives 3 points for
  every first choice, 2 points for every second choice, and 1 point
  for every third choice.  A candidate receives no points if ranked
  last or not ranked at all.  Borda provides some proportionality but
  not as well as SNTV, IRV, or STV.

Options:
  A voter can gain strategic advantage by voting only for his or her
  first choice.  To prevent this advantage, the ballots can by
  "completed" whereby unranked candidates share the remaining points
  on a ballot.

Validation:
  Not validated."""

  def __init__(self, b):

    self.method = "Borda"
    self.ballotCompletion = False
    self.options = " without ballot completion"
    NonIterative.__init__(self, b)
    
  ###

  def setOptions(self, debug=None, strongTieBreakMethod=None, prec=None,
                 ballotCompletion=None):

    if ballotCompletion != None:
      assert(ballotCompletion in [True, False])
      self.ballotCompletion = ballotCompletion
      if ballotCompletion:
        # The only fractions that will ever appear because of ballot completion
        # is 1/2 so no more precision is necessary.
        self.options = " with ballot completion"
        prec = 1
      else:
        self.options = " without ballot completion"
        prec = 0

    NonIterative.setOptions(self, debug, strongTieBreakMethod, prec)

  ###

  def getMaxNumber(self):
    "Find the largest number to be printed in the results."

    if "count" in dir(self) and self.count != []:
      m = max(self.count)
      m /= self.p
    else:
      # Election not complete so use max expected count.
      m = self.b.nBallots * self.b.nCand * self.b.nCand
       
    return m
  
  ###
    
  def runElection(self):
    "Count the votes using the Borda Count."

    self.initialize()
    self.nRounds = 1

    # Add up the Borda counts
    for i, blt in enumerate(self.b.packed):
      # Ranked candidates get their usual Borda score
      for j in range(len(blt)):
        self.count[blt[j]] += self.p * self.b.weight[i] * (self.b.nCand-j-1)

      # If doing ballot completion, then unranked candidates share the
      # remaining Borda score.  Otherwise, goes to exhausted pile.
      if len(blt) < self.b.nCand-1:
        nMissingCand = self.b.nCand - len(blt)
        # missingCandCount = nMissingCand*(nMissingCand-1)/2/nMissingCand
        # simplifies to  missingCandCount = (nMissingCand-1)/2
        if self.ballotCompletion:
          for c in range(self.b.nCand):
            if c not in blt:
              self.count[c] += self.p * self.b.weight[i] * \
                                  (nMissingCand-1) / 2
        else:
          self.exhausted += self.p * self.b.weight[i] * \
                            (nMissingCand-1) * nMissingCand / 2

    self.msg += "Borda count totals. "

    # Choose the winners
    (self.winners, desc) = self.chooseWinners()
    self.msg += desc

##################################################################
##################################################################
##################################################################

class Iterative(Election):
  """Base class for all methods that consist of multiple rounds.
  It is not itself a complete election method and must be
  sub-classed and further defined."""

  def __init__(self, b):

    Election.__init__(self, b)
    self.ThreshMethod = True # methods may override this

    # Specify the method for breaking weak ties.
    #    backward -- present round backwards
    #    forward -- present round, first round forwards
    #    random  -- random choice
    self.weakTieBreakMethod = "backward"

  ###

  def initialize(self):
    Election.initialize(self)
    self.msg = []
    self.count = []
    self.exhausted = []
    # Winners are further broken into two categories.
    self.winnersEven = [] # winners who have had their surplus transferred
    self.winnersOver = [] # winners who still have a surplus

    # There is probably a better way to keep track of what happens at
    # each round.
    # action[r]("surplus|eliminate", [c1, c2, ...]) describes what happened
    # at round r.  Multiple candidates are either eliminated or have
    # their surplusses transferred
    # Nothing happens in the first round
    self.action = []

    # Keep track of what happens to candidates.
    self.wonAtRound = [None] * self.b.nCand
    self.lostAtRound = [None] * self.b.nCand

    self.losers = []
    self.purgatory = range(self.b.nCand)
    self.winners = []
    
  ###

  def getMaxNumber(self):
    "Find the largest number to be printed in the results."

    if "count" in dir(self) and self.count != []:
      # Election complete so find largest number.
      mm = 0
      for i in range(len(self.count)):
        m = max(self.count[i])
        mm = max(mm, m)
      mm /= self.p
    else:
      # Election not complete so use max expected count.
      mm = self.b.nBallots
       
    return mm
  
  ###

  def generateTextRoundResults(self, round, width, nSubCol):

    # This can only be called from generateTextResults()
    txt = ""

    # Separator line and round/stage number
    txt += "=" * width + "\n"
    RS = round
    if self.method == "ERS97 STV":
      RS = self.roundToStage(round)
    txt += "%2d" % (RS+1)

    # Candidate vote totals for the round
    for c in range(self.b.nCand):
      # If candidate has lost and has no votes, leave blank
      if c in self.losers and self.lostAtRound[c] <= round \
             and self.count[round][c] == 0:
        txt += ("|" + self.sfmt) % " "
      # otherwise print the total.
      else:
        txt += ("|" + self.sfmt) % self.displayValue(self.count[round][c])
      # Skip line if necessary
      if (c+1) % nSubCol == 0: txt += "\n  "

    # Exhausted ballots
    txt += ("|" + self.sfmt) % self.displayValue(self.exhausted[round])

    # Surplus and Threshold if dynamic
    if self.ThreshMethod:
      c += 1
      if (c+1) % nSubCol == 0: txt += "\n  "
      txt += ("|" + self.sfmt) % self.displayValue(self.surplus[round])
      c += 1
      if (c+1) % nSubCol == 0: txt += "\n  "
      txt += ("|" + self.sfmt) %self.displayValue(self.thresh[round])
    txt += "\n"

    txt += "  |" + "-" * (width-3) + "\n"
    txt += textwrap.fill(self.msg[round], initial_indent="  | ",
                         subsequent_indent="  | ", width=width)
    txt += "\n"

    return txt
  
  ###

  def generateTextResults(self, maxWidth=80, style="full", round=None):
    "Pretty print results in text format."

    assert(style in ["full", "table", "round"])
    self.setFields()
    
    txt = ""
    nCol = self.b.nCand
    nCol += 1 # Exhausted
    if self.ThreshMethod:
      nCol += 1
      if self.threshName[1] == "Dynamic":
        nCol += 1
    nSubCol = (maxWidth-2)/(self.fw+1)
    width = 2 + nSubCol*(self.fw+1)

    # Include summary information for full results.
    if style == "full":

      txt += """\
Election title: %s
Method: %s
Number of total ballots: %d
Number of invalid or empty ballots: %d
Number of ballots used in the count: %d
%d candidate running for %d seats.

""" % (self.title,
       self.method + self.options,
       self.b.nBallots + self.b.nBadBallots,
       self.b.nBadBallots, self.b.nBallots, self.b.nCand, self.nSeats)

    if style in ["full", "table"]:

      # Find length of longest string in header
      maxLen = 9
      for c in range(self.b.nCand):
        maxLen = max(maxLen, len(self.b.names[c]))
        
      # Pad strings for table header
      maxLen += self.fw - (maxLen % self.fw)
      head = []
      for c in range(self.b.nCand):
        head.append(self.b.names[c].ljust(maxLen))
      head.append("Exhausted".ljust(maxLen))
      if self.ThreshMethod:
        head.append("Surplus".ljust(maxLen))
        head.append("Threshold".ljust(maxLen))
      
      # Table header
      # nCol is the total number of columns
      # nSubCol is the number of columns that fit in the specified width
      # nRow is the number of rows needed to display all of the columns
      # nSubRow is the number of rows needed to display full candidate names
      nRow = nCol/nSubCol
      if nCol % nSubCol > 0: nRow += 1
      nSubRow = maxLen/self.fw
      if maxLen % self.fw > 0: nSubRow += 1
      
      for r in range(nRow):
        for sr in range(nSubRow):
          if r == 0 and sr == 0:
            txt += " R"
          else:
            txt += "  "
          b = sr*self.fw
          e = b + self.fw

          for sc in range(nSubCol):
            h = r*nSubCol + sc
            if h == len(head): break
            txt += "|" + head[h][b:e]
          txt += "\n"
        
        if r < nRow-1:
          txt += "  |" + ("-"*self.fw + "+")*(nSubCol-1) + "-"*self.fw + "\n"
        
      # Rounds
      for round in range(self.nRounds):
        txt += self.generateTextRoundResults(round, width, nSubCol)
      txt += "\n"

    # Include winners for full results
    if style == "full":
      self.winners.sort()
      if len(self.winners) == 0:
        winTxt = "No winners.\n"
      elif len(self.winners) == 1:
        winTxt = "Winner is %s.\n" % self.joinList(self.winners)
      else:
        winTxt = "Winners are %s.\n" % self.joinList(self.winners)
      txt += textwrap.fill(winTxt, width=width)

    # Generate results for only the specified round
    if style == "round":
      txt = self.generateTextRoundResults(round, width, nSubCol)

    return txt

  ###
    
  def generateHTMLResults(self, maxWidth=80):
    "Pretty print results in html format."

    self.setFields()
    
    nCol = self.b.nCand
    nCol += 1 # Exhausted
    if self.ThreshMethod:
      nCol += 2 # Surplus and Thresh
    width = maxWidth

    txt = """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
        "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<title>%s</title>
</head>
<body>
Election title: %s<br>
Method: %s<br>
Number of total ballots: %d<br>
Number of invalid or empty ballots: %d<br>
Number of ballots used in the count: %d<br>
%d candidate running for %d seats.<br>
<br>

<table border=1 cellspacing=0>

<tr>
<th>R</th>
""" % (self.title, self.title,
       self.method + self.options,
       self.b.nBallots + self.b.nBadBallots,
       self.b.nBadBallots, self.b.nBallots, self.b.nCand, self.nSeats)

    for c in range(self.b.nCand):
      txt += "<th align='center'>%s</th>\n" % self.b.names[c]
    txt += "<th align='center'>%s</th>\n" % "Exhausted"
    if self.ThreshMethod:
      txt += "<th align='center'>%s</th>\n" % "Surplus"
      txt += "<th align='center'>%s</th>\n" % "Threshold"
    txt += "</tr>\n\n"
      
    for round in range(self.nRounds):
      txt += "<tr>\n"
      txt += "<td align='center' rowspan=2>%s</td>\n" % (round+1)
      for c in range(self.b.nCand):
        txt += "<td align='center'>%s</td>\n" %\
               self.displayValue(self.count[round][c])
      if self.ThreshMethod:
        txt += "<td align='center'>%s</td>\n" %\
               self.displayValue(self.surplus[round])
        txt += "<td align='center'>%s</td>\n" %\
               self.displayValue(self.thresh[round])
      txt += "<td align='center'>%s</td>\n" %\
             self.displayValue(self.exhausted[round])
      txt += "</tr>\n\n"

      msgTxt = textwrap.fill(self.msg[round], width=width)
      txt += "<tr><td colspan=%d>%s</td></tr>\n\n" % (nCol, msgTxt)

    txt += "</table>\n\n"

    # Winners
    self.winners.sort()
    if len(self.winners) == 0:
      winTxt = "No winners."
    elif len(self.winners) == 1:
      winTxt = "Winner is %s." % self.joinList(self.winners)
    else:
      winTxt = "Winners are %s." % self.joinList(self.winners)
    winTxt = textwrap.fill(winTxt, width=width)
    winTxt = winTxt.replace("\n", "<br>\n")
    txt += "<p>%s</p>\n\n" % winTxt

    txt += "</body>\n</html>\n"

    return txt

  ###

  def generateERSCSVResults(self, skipDate=False):
    "Return a results sheet in the CVS format used by the ERS."

    assert(self.method != "Condorcet")
    fmt = "%+." + str(self.prec) + "f"

    if skipDate:
      today = ""
      v = ""
    else:
      from datetime import date
      today = date.today().strftime("%d %b %Y")
      v = version.v

    if self.method == "ERS97 STV":
      nRS = self.nStages
      quota = self.displayValue(self.quota[-1])
    elif self.ThreshMethod:
      nRS = self.nRounds
      quota = self.displayValue(self.thresh[-1])
    else:
      nRS = 1
      quota = 0

    # 8 header lines
    results = ("""\
"Election for","%s"
"Date","%s"
"Number to be elected",%d
"Valid votes",%d
"Invalid votes",%d
"Quota",%s
"OpenSTV","%s"
"Election rules","%s"
""") % (self.b.title, today, self.nSeats, self.b.nBallots,
        self.b.nBadBallots, quota, v, self.method)

    # title lines
    tl1 = ','
    tl2 = ',"First"'
    tl3 = '"Candidates","Preferences"'
    for RS in range(1, nRS):
      tl1 += ',"Stage",%d' % (RS+1)

      if self.method == "ERS97 STV":
        round = self.stages[RS][-1]
      else:
        round = RS

      if self.action[round][0] == "surplus":
        tl2 += ',"Surplus of",'
        c = self.action[round][1][0]
        tl3 += ',"' + self.b.names[c] + '",'
      elif self.action[round][0] == "eliminate":
        tl2 += ',"Exclusion of",'
        eliminated = [self.b.names[c] for c in self.action[round][1]]
        eliminated.sort()
        tl3 += ',"' + string.join(eliminated, '+') + '",'
      else:
        assert(0)

    results += tl1 + '\n'
    results += tl2 + '\n'
    results += tl3 + '\n'

    # candidate lines
    for c in range(len(self.namesPlusWithdrawn)):
      
      if c in self.withdrawn:
        # Withdrawn candidates appear in the results even though there is
        # nothing to report.  Handle them separately.
        results += '"%s","Withdrawn",' % (self.namesPlusWithdrawn[c])
        results += ',,' * (nRS-1) + '\n'

      else:

        # Since we are looping over all candidates, need to convert the index
        # into the list of non-withdrawn candidates.
        name = self.namesPlusWithdrawn[c]
        cc = self.b.names.index(name)

        results += '"%s",%d,' % (self.b.names[cc],
                                 self.count[0][cc]/self.p)

        for RS in range(1, nRS):
          if self.method == "ERS97 STV":
            round = self.stages[RS][-1]
            prevround = self.stages[RS-1][-1]
          else:
            round = RS
            prevround = RS - 1

          diff = self.count[round][cc] - self.count[prevround][cc]
          if diff == 0:
            diffstr = ''
          else:
            diffstr = fmt % (1.0*diff/self.p)

          count = self.count[round][cc]
          if cc in self.losers and self.lostAtRound[cc] <= round \
                 and count == 0:
            countstr = '"-"'
          else:
            countstr = self.displayValue(count)

          results += '%s,%s,' % (diffstr, countstr)

        if cc in self.winners:
          results += '"Elected"'
        results += '\n'

    # non-transferable
    results += '"Non-transferable", ,'
    for RS in range(1, nRS):
      if self.method == "ERS97 STV":
        round = self.stages[RS][-1]
        prevround = self.stages[RS-1][-1]
      else:
        round = RS
        prevround = RS - 1
      diff = self.exhausted[round] - self.exhausted[prevround]
      if diff == 0:
        diffstr = ''
      else:
        diffstr = fmt % (1.0*diff/self.p)

      exh = self.exhausted[round]
      exhstr = self.displayValue(exh)

      results += '%s,%s,' % (diffstr, exhstr)
    results += '\n'

    # totals
    results += '"Totals",' + str(self.b.nBallots)
    for RS in range(1, nRS):
      results += ',,%s' % self.displayValue(self.b.nBallots*self.p)
    results += '\n'

    return results

###

  def breakWeakTie(self, R, cList, mostfewest, what=""):
    "Break ties using previous rounds."

    # A weak tie is a tie at a given round.  If candidates are tied at
    # all rounds then it is a strong tie.

    assert(mostfewest in ["most", "fewest"])

    tiedC = self.findTiedCand(cList, mostfewest, self.count[R])
    if len(tiedC) == 1:
      return (tiedC[0], "") # no tie

    # Let the user know what is going on.
    desc = "Candidates %s were tied when choosing %s. "\
           % (self.joinList(tiedC), what)
    
    # Method for breaking weak ties
    order = range(R)
    if self.weakTieBreakMethod == "backward":
      order.reverse()
    
    if self.weakTieBreakMethod in ["forward", "backward"]: # != random
      # Try to break the tie using other rounds.
      for i in order:
        tiedC = self.findTiedCand(tiedC, mostfewest, self.count[i])
        if len(tiedC) == 1:
          desc += "Candidate %s was chosen by breaking the tie at round %d. "\
                  % (self.b.names[tiedC[0]], i+1)
          return (tiedC[0], desc)

    # The tie can't be broken with other rounds so do strong tie break.
    self.nRandom += 1
    (c, desc2) = self.breakStrongTie(tiedC)
    desc += desc2
    return (c, desc)

###

  def newWinners(self, winners, status="over"):
    "Perform basic accounting when a new winner is found."

    if len(winners) == 0: return ""
    
    winners.sort()
    for c in winners:
      self.purgatory.remove(c)
      self.winnersOver.append(c)
      self.wonAtRound[c] = self.R
    self.winners = self.winnersOver + self.winnersEven
    
    if len(winners) == 1 and status == "over":
      desc = "Candidate %s has reached the threshold and is elected. "\
             % self.joinList(winners)
    elif len(winners) == 1 and status == "under":
      desc = "Candidate %s is elected. " % self.joinList(winners)
    elif status == "over":
      desc = "Candidates %s have reached the threshold and are elected. "\
             % self.joinList(winners)
    elif status == "under":
      desc = "Candidates %s are elected. " % self.joinList(winners)
    elif status == "none":
      desc = ""

    return desc

###

  def newLosers(self, losers):
    "Perform basic accounting when a new loser is found."
    
    if len(losers) == 0: return

    losers.sort()
    for c in losers:
      self.purgatory.remove(c)
      self.losers.append(c)
      self.lostAtRound[c] = self.R

##################################################################

class Bucklin(Iterative):
  """\
Method:
  Bucklin System
  
Description:
  This implementation of Bucklin can only be used to elect one
  candidate.  A candidate receiving a majority of first choices is the
  winner.  If no candidate has a majority of first choices, then a
  candidate receiving a majority of first and second choices is the
  winner.  If more than one candidate has a majority of first and
  second choices, then the candidate having the most first and second
  choices is the winner.  This process is repeated for further choices
  as necessary.  The Bucklin system can also be used as a majoritarian
  system (i.e., not proportional representation) to elect multiple
  candidates, but this is not implemented here.
  
Options:
  None.

Validation:
  Not validated."""

  def __init__(self, b):

    self.method = "Bucklin"
    self.prec = 0
    Iterative.__init__(self, b)
    self.ThreshMethod = False
    self.options = ""

  ###
    
  def runElection(self):
    "Count the votes with the Bucklin system."

    self.initialize()

    # Sequentially use more candidates until we have a winner.
    for self.R in range(self.b.nCand):
      self.msg.append("")
      self.count.append([0] * self.b.nCand)
      self.exhausted.append(0)

      if self.R == 0:
        self.msg[self.R] += "Count of first choices. "
      else:
        self.msg[self.R] += "No candidate has a majority. "\
                            "Using %d rankings. " % (self.R+1)
        self.count[self.R] = self.count[self.R-1][:]
        self.exhausted[self.R] = self.exhausted[self.R-1]

      # Count votes using multiple rankings
      for i in xrange(len(self.b.packed)):
        if len(self.b.packed[i]) > self.R:
          c = self.b.packed[i][self.R]
          self.count[self.R][c] += self.b.weight[i]
        else:
          self.exhausted[self.R] += self.b.weight[i]

      # Check for winners.  Could be more than we need.
      potWinners = []
      for c in self.purgatory:
        if 2*self.count[self.R][c] > self.b.nBallots:
          potWinners.append(c)
      if len(potWinners) > 0:
        (c, desc) = self.breakWeakTie(self.R, potWinners, "most", "winner")
        desc2 = self.newWinners([c])
        self.msg[self.R] += desc + desc2
        break

    # If no candidate has a majority then a plurality is good enough
    if self.winners == []:
      (c, desc) = self.breakWeakTie(self.R, self.purgatory, "most", "winner")
      desc2 = self.newWinners([c], "under")
      self.msg[self.R] += desc + desc2

    self.nRounds = self.R + 1

##################################################################

