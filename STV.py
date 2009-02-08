#!/usr/bin/env python

"""Module for counting ranked ballots with a variety of election methods.

Class STV
  Class NoSurplusSTV
    Class IRV
    Class SuppVote
    Class Coombs
  Class UnitarySTV
    Class CambridgeSTV
    Class DailSTV
    Class RTSTV
  Class GregorySTV
    Class ERS97STV
    Class NIrelandSTV
  Class InclusiveSTV
    Class BCSTV
    Class ScottishSTV
    Class GPCA2000STV
    Class FTSTV
  Class RecursiveSTV
    Class MeekSTV
    Class WarrenSTV
    Class RecursiveXSTV
      Class MeekXSTV
      Class WarrenXSTV
"""

## Copyright (C) 2003-2009 Jeffrey O'Neill
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

__revision__ = "$Id: STV.py 471 2009-01-31 19:29:20Z jco8 $"

import sys
import re
import string
import math
import random
import textwrap
import version
from types import *
from array import array
from NonSTV import *

##################################################################

class STV(Iterative):
  """Base class for all STV methods. This class defines functions and
  variables used by numerous STV methods.  It is not itself a complete
  election method and must be sub-classed and further defined."""

  def __init__(self, b):
    
    Iterative.__init__(self, b)
    
##################################################################
  
  def initialize(self):
    Iterative.initialize(self)
    self.firstEliminationRound = True

    self.R = 0           # current round
    self.nRounds = 0     # total number of rounds
    self.count = []      # count[r][c] is candidate c's votes at round r
    self.exhausted = []  # exhausted[r] is number of exhasuted votes
    self.surplus = []    # surplus[r] is number of surplus votes
    self.thresh = []     # thresh[r] is the winning threshold
    self.msg = []        # msg[r] contains text describing round r

    # votes[c] stores the indices of all votes for candidate c.
    self.votes = []
    for c in range(self.b.nCand):
      self.votes.append([])
    
##################################################################
  
  def allocateRound(self):
    "Allocate space for all data structures for one round."

    self.msg.append("")
    self.count.append([0] * self.b.nCand)
    self.exhausted.append(0)
    self.surplus.append(0)
    self.thresh.append(0)
    self.action.append(None)

  ###

  def updateThresh(self):
    "Compute the value of the winning threshold."

    assert(self.threshName[0] in ["Droop", "Hare"])
    assert(self.threshName[1] in ["Static", "Dynamic"])
    assert(self.threshName[2] in ["Whole", "Fractional"])

    if self.threshName[0] == "Droop":
      threshDen = self.nSeats + 1
    elif self.threshName[0] == "Hare":
      threshDen = self.nSeats

    if self.threshName[1] == "Static":
      threshNum = self.p * self.b.nBallots
    elif self.threshName[1] == "Dynamic":
      threshNum = self.p * self.b.nBallots - self.exhausted[self.R]

    if self.threshName[2] == "Whole":
      thresh = threshNum/threshDen/self.p*self.p + self.p
    elif self.threshName[2] == "Fractional":
      thresh = threshNum/threshDen + 1

    self.thresh[self.R] = thresh
    return ""
  
  ###

  def updateSurplus(self):
    "Compute the surplus for current round."

    self.surplus[self.R] = 0
    for c in self.winnersOver + self.purgatory:
      if self.count[self.R][c] > self.thresh[self.R]:
        self.surplus[self.R] += self.count[self.R][c] - self.thresh[self.R]
    return ""

  ###

  def updateWinners(self):
    "Find new winning candidates."

    winners = []
    desc = ""
    for c in self.purgatory[:]:
      if self.count[self.R][c] >= self.thresh[self.R]:
        winners.append(c)
    desc = self.newWinners(winners)
    return desc

  ###

  def isSurplusToTransfer(self):
    "Decide whether to transfer surplus votes or eliminate candidates."
    
    if ( self.surplus[self.R-1] == 0 or
         (self.delayedTransfer and self.getLosers() != []) ):
      if self.delayedTransfer and self.surplus[self.R-1] > 0:
        desc = "Candidates have surplus votes, but since "\
          "candiates can be safely eliminated, the transfer of surplus "\
          "votes will be delayed and candidates will be eliminated and their "\
          "votes transferred for the next round."
      else:
        desc = "No candidates have surplus votes so "\
          "candidates will be eliminated and their votes transferred for the "\
          "next round. "
      return (False, desc)
    else:
      desc = "Candidates have surplus votes so "\
        "surplus votes will be transferred for the next round. "
      return (True, desc)

  ###

  def chooseSurplusToTransfer(self):
    "Choose the candidate whose surplus will be transferred."

    # Choose the candidate with the greatest surplus.
    (c, desc) = self.breakWeakTie(self.R-1, self.winnersOver, "most",
                                  "surplus to transfer")
    return (c, desc)

###

  def getLosers(self, ppp = None):
    "Return all candidates who are sure losers."

    # Return all candidates who are sure losers but do not look at previous
    # rounds to break ties.  It will be slightly underinclusive.

    # If the surplus is zero and two or more candidates are tied for
    # last place, then one candidate could
    # be a sure loser by looking at previous rounds.  Such losers will not
    # be identified here.  Such losers can be found with breakWeakTie().
    # This will not affect delaying transfer of surplus since there will
    # not be a surplus in this situation.

    if ppp == None: ppp = self.purgatory
    R = self.R - 1
    maxNumLosers = len(ppp + self.winners) - self.nSeats
    ppp.sort(key=lambda a, f=self.count[R]: f[a])
    losers = []

    s = 0
    for i in range(maxNumLosers):
      c = ppp[i]
      cNext = ppp[i+1]
      s += self.count[R][c]
      if ( (i>0  and s + self.surplus[R] <= self.count[R][cNext]) or 
           (i==0 and s + self.surplus[R] < self.count[R][cNext]) ):
        losers = ppp[:i+1]

    return losers

  ###

  def chooseCandidatesToEliminate(self):
    "Choose one or more candidates to eliminate."

    elimList = []
    desc = ""
      
    # First elimination round is different for some methods
    # Skipped if no candidates would be eliminated
    if self.firstEliminationRound:

      if self.batchElimination == "Zero":
        desc = "Since this is the first elimination round, all candidates "\
               "without any votes are eliminated. "
        elimList = [c for c in self.purgatory if self.count[self.R-1][c]==0]
      elif self.batchElimination == "Cutoff":
        desc = "Since this is the first elimination round, all candidates "\
               "with fewer than %d votes are eliminated. " % \
               self.batchCutoff
        elimList = [c for c in self.purgatory
                    if self.count[self.R-1][c] < self.p*self.batchCutoff]
      elif self.batchElimination == "Losers":
        #### REWRITE THIS!!!
        desc = "All losing candidates are eliminated. "
        elimList0 = [c for c in self.purgatory if self.count[self.R-1][c]==0]
        ppp = self.purgatory[:]
        for c in elimList0: ppp.remove(c)
        elimList1 = self.getLosers(ppp)
        elimList = elimList0 + elimList1
        # Under the following conditions we can identify an additional loser.
        # We want to make sure not to eliminate too many candidates!
        if ( self.surplus[self.R-1] == 0 and
             elimList1 == [] and
             len(ppp + self.winners) > self.nSeats):
          (c, desc2) = self.breakWeakTie(self.R-1, ppp, "fewest",
                                        "candidates to eliminate")
          elimList.append(c)
          desc += desc2
      elif self.batchElimination == "None":
        pass
      else:
        assert(0)

    # Normal elimination round
    # This happens if not firstEliminationRound or if the first
    # elimination round didn't eliminate any candidates.
    if (not self.firstEliminationRound) or (elimList == []):
      if self.batchElimination == "Losers":
        desc = "All losing candidates are eliminated. "
        elimList = self.getLosers()
        if elimList == []:
          (c, desc2) = self.breakWeakTie(self.R-1, self.purgatory, "fewest",
                                        "candidates to eliminate")
          elimList = [c]
          desc += desc2
      else:
        desc = ""
        (c, desc2) = self.breakWeakTie(self.R-1, self.purgatory, "fewest",
                                      "candidates to eliminate")
        elimList = [c]
        desc += desc2

    # Don't do first elimination again.
    self.firstEliminationRound = False

    # Put losing candidates in the proper list
    self.newLosers(elimList)

    return (elimList, desc)
  
###

  def electionOver(self):
    "Election is over when we know all the winners."
    
    # Already recognized enough winners
    if len(self.winners) == self.nSeats:
      desc = "The election is over since all seats are filled. "
      return (True, desc)

    # Every candidate remaining with >0 votes is a winner.
    if len(self.purgatory + self.winners) <= self.nSeats:
      desc = "The election is over since the number of candidates remaining "\
             "is equal to the number of seats. "
      return (True, desc)

    # Not done yet.
    return (False, "")

  ###

  def updateStatus(self):
    "Update the status of winners who haven't reached the threshold."

    desc = ""
    self.nRounds = self.R+1

    # Update status of winners under the threshold
    if len(self.winners) < self.nSeats:
      winners = []
      losers = []
      for c in self.purgatory[:]:
        if self.count[self.R][c] > 0:
          winners.append(c)
        else:
          losers.append(c)
      desc += self.newWinners(winners, "under")
      self.newLosers(losers)

    return desc

  ###

  def initialVoteTally(self):
    "Count the first place votes."

    # Allocate votes to candidates based on the first choices.
    for i in xrange(len(self.b.packed)):
      c = self.topChoice(self.b.packed[i], self.purgatory)
      if c != None: self.votes[c].append(i)
    self.action[self.R] = ("first", [])
    return "Count of first choices. "

  ###

  def runElection(self):
    "Count the votes with STV."

    self.initialize()

    # Count first place votes
    self.allocateRound()
    self.msg[self.R] += self.initialVoteTally()    
    self.msg[self.R] += self.updateCount()
    self.msg[self.R] += self.updateThresh()
    self.msg[self.R] += self.updateSurplus()
    self.msg[self.R] += self.updateWinners()
    if self.debug:
      print self.generateTextResults(round=self.R)
    
    # Do another round...
    (done, descOver) = self.electionOver()
    while (not done):
      
      self.R += 1
      self.allocateRound()

      # Check to see if there is a surplus to transfer
      (transferSurplus, descTransition) = self.isSurplusToTransfer()
      self.msg[self.R-1] += descTransition
      
      if transferSurplus:
        self.msg[self.R] += self.transferSurplusVotes()
      else:
        self.msg[self.R] += self.eliminateCandidates()

      self.msg[self.R] += self.updateCount()
      self.msg[self.R] += self.updateThresh()
      self.msg[self.R] += self.updateSurplus()
      self.msg[self.R] += self.updateWinners()
      (done, descOver) = self.electionOver()
      if self.debug:
        print self.generateTextResults(round=self.R)

    self.msg[self.R] += descOver
    self.msg[self.R] += self.updateStatus()

##################################################################
##################################################################
##################################################################

class NoSurplusSTV(STV):
  """Base class for all STV methods that don't transfer surplus votes.
  It is not itself a complete election method and must be
  sub-classed and further defined."""

  def __init__(self, b):

    self.prec = 0
    STV.__init__(self, b)
    self.ThreshMethod = False
    self.threshName = None
    self.options = ""

  ###

  def updateThresh(self):
    "These methods don't have a threshold."
    return ""
  
  def updateSurplus(self):
    "These methods don't have surplus votes."
    return ""
    
  ###

  def isSurplusToTransfer(self):
    "Never transfer surplus votes."
    return (False, "")
  
  ###

  def eliminateCandidates(self):
    "Eliminate candidates for NoSurplus methods."

    (elimList, descChoose) = self.chooseCandidatesToEliminate()
    self.action[self.R] = ("eliminate", elimList)
    
    for loser in elimList:
      for i in self.votes[loser]:
        c = self.topChoice(self.b.packed[i], self.purgatory)
        if c != None:
          self.votes[c].append(i)
      self.votes[loser] = []

    desc = "Count after eliminating %s and transferring votes. "\
           % self.joinList(elimList)
    desc += descChoose
    return desc

  ###
  
  def updateWinners(self):
    "Since there is no threshold, winners are only determined at the end."
    return ""
    
  ###

  def updateCount(self):
    "Update the vote totals after a transfer of votes for NoSurplus methods."

    # Recount votes for all candidates
    for c in range(self.b.nCand):
      for i in self.votes[c]:
        self.count[self.R][c] += self.b.weight[i]

    # Compute the number of exhausted votes
    self.exhausted[self.R] = self.b.nBallots
    for c in range(self.b.nCand):
      self.exhausted[self.R] -= self.count[self.R][c]
    return ""

  ###

  def electionOver(self):
    "Election is over when only N+1 candidates remain."

    if len(self.purgatory) <= self.nSeats + 1:
      desc = ""
      if len(self.purgatory) > self.nSeats:
        (c, desc) = self.breakWeakTie(self.R, self.purgatory, "fewest",
                                       "winners")
        self.newLosers([c])
      winners = self.purgatory[:]
      desc += self.newWinners(winners, "none")
      return (True, desc)
    else:
      return (False, "")

##################################################################

class IRV(NoSurplusSTV):
  """\
Method:
  Instant Runoff Voting

Rules:
  San Francisco, CA: http://www.sfgov.org/site/election_index.asp?id=27564
  Burlington, VT: http://www.leg.state.vt.us/statutes/fullsection.cfm?Title=24APPENDIX&Chapter=003&Section=00005
  Takoma Park, MD: http://www.fairvote.org/media/irv/states/takoma-park-charter-amend.pdf
  

Description:
  IRV is more commonly used to elect one candidate but can also be
  used to provide proportional representation.  Ballots are first
  distributed according to their first choices.  The candidate with
  the fewest number of ballots is eliminated and the ballots are
  transferred to their next choices.  This process is repeated until
  the winners are determined.
  
Options:
  None.

Validation:
  Not validated."""
  
  def __init__(self, b):

    self.method = "IRV"
    NoSurplusSTV.__init__(self, b)
    self.batchElimination = "Zero"

##################################################################

class SuppVote(NoSurplusSTV):
  """\
Method:
  Supplemental Vote

Description:
  The supplemental vote is a simplified version of IRV.  Only the first
  two rankings on the ballots are used.  In the first round, the first
  rankings are counted and all candidates except for the top two are
  eliminated.  Ballots of eliminated candidates are transferred to their
  second rankings.  The supplemental vote is used to elect the Mayor of
  London.
  
Options:
  None.

Validation:
  Not validated."""

  def __init__(self, b):

    self.method = "Supplemental Vote"
    NoSurplusSTV.__init__(self, b)

  ###
    
  def chooseCandidatesToEliminate(self):
    "Eliminate all candidates except for the top two."

    (topTwo, desc) = self.chooseNfromM(2, self.count[0], self.purgatory,
                                       "top two candidates")
    losers = []
    for c in self.purgatory:
      if c not in topTwo:
        losers.append(c)

    self.newLosers(losers)        
    return (losers, desc)

##################################################################

class Coombs(NoSurplusSTV):
  """\
Method:
  Coombs
  
Description:
  Coombs is similar to IRV except that the candidate receiving the
  most last-place votes (instead of the fewest first-place votes) is
  eliminated at each round.  If a ballot ranks fewer than all of the
  candidates, then the unranked candidates share the last-place vote.
  
Options:
  None.

Validation:
  Not validated."""

  def __init__(self, b):

    self.method = "Coombs"
    NoSurplusSTV.__init__(self, b)
    self.batchElimination = "None"

  ###

  def initialize(self):
    NoSurplusSTV.initialize(self)
    # Create data structures for speeding up mostLast()
    self.unranked = [None] * len(self.b.packed)
    for i in xrange(len(self.b.packed)):
      u = array("B")
      for c in self.purgatory:
        if c in self.b.packed[i]: continue
        u.append(c)
      self.unranked[i] = u
    
  ###
    
  def mostLast(self):
    "Count the number of last-place votes per candidate."

    desc = ""

    # Count last place votes per candidate
    total = [0] * self.b.nCand
    for i in xrange(len(self.b.packed)):
      nUnranked = len(self.unranked[i])
      # If no unranked cands, last place candidate gets the vote
      if nUnranked == 0:
        ballot = self.b.packed[i][:]
        ballot.reverse()
        for c in ballot:
          if c in self.purgatory:
            break
        total[c] += self.b.weight[i]
      # Otherwise unranked cands share the last place vote
      else:
        share = 1.0 * self.b.weight[i] / nUnranked
        for c in self.unranked[i]:
          total[c] += share

    # Resolve ties
    ppp = self.purgatory[:]
    ppp.sort(key=lambda a, f=total: -f[a])
    c0 = ppp[0]
    numTied = total.count(total[c0])
    if numTied > 1:
      desc += "Candidates %s were tied when choosing a candidate to "\
              "eliminate. " % self.joinList(ppp[:numTied])
      (c0, desc2) = self.breakStrongTie(ppp[:numTied])
      desc += desc2

    desc += "Last place votes: "
    for c in self.purgatory[:-1]:
      desc += "%s, %f; "  % (self.b.names[c], total[c])
    c = self.purgatory[-1] 
    desc += "and %s, %f. "  % (self.b.names[c], total[c])

    # Update data structures
    for i in xrange(len(self.b.packed)):
      if c0 in self.unranked[i]: self.unranked[i].remove(c0)

    return (c0, desc)

  ###

  def chooseCandidatesToEliminate(self):
    "Choose candidates to eliminate."

    (c, desc) = self.mostLast()
    self.newLosers([c])
    elimList = [c]
    return (elimList, desc)

  ###

  def electionOver(self):
    "Election is over when only N candidates remain."

    if len(self.purgatory) <= self.nSeats:
      winners = self.purgatory[:]
      desc = self.newWinners(winners, "none")
      return (True, desc)
    else:
      return (False, "")

##################################################################
##################################################################
##################################################################

class UnitarySTV(STV):
  """Base class for all unitary STV methods.  This class defines
  functions and variables used by unitary STV methods.  It is not
  itself a complete election method and must be sub-classed and
  further defined."""

  def __init__(self, b):
    
    self.prec = 0
    STV.__init__(self, b)

    assert(self.threshName[2] == "Whole")

    self.auditTrail = []
    for c in range(self.b.nCand):
      self.auditTrail.append([])
    self.auditTrail.append([]) # for non-transferable votes
    

  ###
      
  def initialVoteTally(self):
    "Count the first place votes with unitary rules."

    # Allocate votes to candidates bases on the first choices.
    for i in xrange(len(self.b.raw)):
      c = self.topChoice(self.b.raw[i], self.purgatory)
      if c != None: 
        self.votes[c].append(i)
        self.auditTrail[c].append(self.b.bid[i])
      else:
        self.auditTrail[-1].append(self.b.bid[i])

    self.action[self.R] = ("first", [])
    
    return "Count of first choices. "

  ###

  def updateCount(self):
    "Update the vote totals after a transfer of votes."

    # If we are in the process of transferring surplus votes, then
    # the transferor needs to be treated specially.
    if self.action[self.R][0] == "surplus":
      cSurplus = self.action[self.R][1][0] # always array of 1
      self.winnersOver.remove(cSurplus)

    # Update counts for losers, purgatory, and winnersOver.
    for c in self.losers + self.purgatory + self.winnersOver:
      self.count[self.R][c] = len(self.votes[c])

    # Set counts for winnersEven.  This will always be the same as the
    # previous round.
    for c in self.winnersEven:
      self.count[self.R][c] = self.count[self.R-1][c]

    # Set counts for the candidate in transition from winnersOver to
    # winnersEven.  The transferor must be treated differently from
    # winnersOver and winnersEven.
    if self.action[self.R][0] == "surplus":
      self.count[self.R][cSurplus] = self.thresh[self.R-1]

    # Compute the number of exhausted votes.
    self.exhausted[self.R] = self.b.nBallots
    for c in range(self.b.nCand):
      self.exhausted[self.R] -= self.count[self.R][c]

    # Put the transferor where he belongs.
    if self.action[self.R][0] == "surplus":
      self.winnersEven.append(cSurplus)

    return ""

##################################################################

class DailSTV(UnitarySTV):
  """\
Method:
  Dail STV
  
Description:

  This version of STV is used for the Dail in Ireland.  This
  implementation is not complete
  
Options:
  None.

Validation:
  Not validated."""
  
  def __init__(self, b):
    
    self.method = "Dail STV"
    self.options = ""
    self.threshName = ("Droop", "Static", "Whole")
    self.delayedTransfer = True
    self.batchElimination = "Losers"

    # Dail rules do last batch transfers
    self.batches = []    # Votes are transferred in batches
    for c in range(self.b.nCand):  # Need to store batches for each cand.
      self.batches.append([])

    UnitarySTV.__init__(self, b)

##################################################################

class CambridgeSTV(UnitarySTV):
  """\
Method:
  Cambridge STV

Rules:
  Proportional Representation Voting in Cambridge Municipal Elections
  http://www.cambridgema.gov/Election/prop-voting.html
 
Description:
  This version of STV has been used by the City of Cambridge,
  Massachusetts since 1941.  For more details see
  http://www.ci.cambridge.ma.us/~Election/.  Since candidates with
  fewer than 50 votes are eliminated, this method should not be used
  with a small number of ballots.

Options:
  None.

Validation:
  Validated against official Cambridge results from 1999 to present."""
  
  def __init__(self, b):
    
    self.method = "Cambridge STV"
    self.batchElimination = "Cutoff"
    self.batchCutoff = 50
    self.options = ""
    self.threshName = ("Droop", "Static", "Whole")
    self.delayedTransfer = False
    UnitarySTV.__init__(self, b)

  ###

  def setOptions(self, debug=None, strongTieBreakMethod=None, prec=None,
                 batchCutoff=None):

    if batchCutoff != None:
      self.batchCutoff = batchCutoff
    UnitarySTV.setOptions(self, debug, strongTieBreakMethod, prec)

  ###

  def checkMinRequirements(self):
    "Only attempt to count votes if there are enough candidates and voters."
    
    UnitarySTV.checkMinRequirements(self)
    if self.b.nBallots < self.batchCutoff * self.nSeats:
      raise RuntimeError, "Not enough ballots to run an election."
    
  ###

  def transferSurplusVotes(self):
    "Transfer surplus votes according to the Cambridge rules."
    
    (c0, descChoose) = self.chooseSurplusToTransfer()
    self.action[self.R] = ("surplus", [c0])

    # transfer surplus according to Cambridge, MA rules.
    # the Cincinati method is confusing when the
    # surplus is just 1 or 2 votes...

    total = int(self.count[self.R-1][c0])
    surplus = int(total - self.thresh[self.R-1])
    skip = int(round(1.0 * total / surplus)) # decimation factor
    start = skip - 1                         # starting point

    # compute the order in which ballots will be considered for transfer
    if surplus == 1:
      order = range(total)
      order = order[-1:] + order[:-1]
    else:
      order = []
      for i in range(start, start+skip):
        for j in range(i, total, skip):
          order.append(j)
      for i in range(start):
        order.append(i)

    # transfer the ballots
    nTransferred = 0
    ppp = self.purgatory[:]  # candidates who can receive votes
    # attempt to transfer votes in the precalculated order
    for ci in order:   # ci is the cith vote of a candidate
      bi = self.votes[c0][ci]  # bi is the bith ballot
      # Get the next candidate.
      # If no next candidate, then the vote is not transferable and
      # remains with the current candidate.
      c = self.topChoice(self.b.raw[bi], ppp)
      if c != None:
        self.votes[c].append(bi)
        self.auditTrail[c].append(self.b.bid[bi])
        self.auditTrail[c0][ci] = "<del>%s</del> &rArr; %s" % \
                                 (self.b.bid[bi], self.b.names[c])
        # If the receiving candidate is now a winner, then that
        # candidate can no longer receive any more votes.
        if len(self.votes[c]) >= self.thresh[self.R-1]:
          ppp.remove(c)
        nTransferred += 1
      else:
        self.auditTrail[c0][ci] = "%s (Nontransferable)" % self.b.bid[bi]
      # Check if the entire surplus has been transferred
      if nTransferred == surplus:
        break

    self.votes[c0] = []
    desc = "Count after transferring surplus votes from %s by using the "\
           "Cincinnati method with a skip value of %d. " %\
           (self.b.names[c0], skip)
    desc += descChoose
    return desc

  ###

  def eliminateCandidates(self):
    "Eliminate candidate according to the Cambridge rules."

    (elimList, descChoose) = self.chooseCandidatesToEliminate()
    self.action[self.R] = ("eliminate", elimList)
    
    # Transfer from candidates with fewest votes first
    losers = elimList[:]
    ppp = self.purgatory[:]
    for j in range(len(losers)):
      (loser, desc) = self.breakWeakTie(self.R-1, losers, "fewest",
                                        "order of candidate elimination")
      losers.remove(loser)
      for ci, bi in enumerate(self.votes[loser]):
        c = self.topChoice(self.b.raw[bi], ppp)
        if c != None:
          self.votes[c].append(bi)
          self.auditTrail[c].append(self.b.bid[bi])
          self.auditTrail[loser][ci] = "<del>%s</del> &rArr; %s" % \
                                       (self.b.bid[bi], self.b.names[c])
          # If receiving candidate becomes a winner, then that
          # candidate can't receive any more votes.
          if len(self.votes[c]) >= self.thresh[self.R-1]:
            ppp.remove(c)
        else:
          self.auditTrail[-1].append(self.b.bid[bi])
          self.auditTrail[loser][ci] = "<del>%s</del> &rArr; Exhausted" % \
                                       self.b.bid[bi]

      self.votes[loser] = []

    desc = "Count after eliminating %s and transferring votes. "\
           % self.joinList(elimList)
    desc += descChoose
    return desc

  ###

  def saveAuditTrail(self):
    "Save files with the audit trail"
    
    for c in range(self.b.nCand):
      
      txt = """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
        "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<title>Audit Trail for %s</title>
</head>
<body>
""" % self.b.names[c]

      for i, s in enumerate(self.auditTrail[c]):
        txt += "%d: %s<br>" % (i, s)
        
      txt += """\
</body>
</html>
"""

##################################################################

class RTSTV(UnitarySTV):
  """\
Method:
  Customizable Random Transfer STV
  
Description:
  This is a customizable implementation of random transfer STV.

Options:
  See the Help menu for a description of the options.

Validation:
  Not validated."""

  def __init__(self, b):

    self.method = "Random Transfer STV"
    self.threshName = ("Droop", "Static", "Whole")
    self.options = " with %s threshold" % string.join(self.threshName, "-")
    self.delayedTransfer = False
    self.batchElimination = "Zero"
    self.batchCutoff = 50
    UnitarySTV.__init__(self, b)

  ###

  def setOptions(self, debug=None, strongTieBreakMethod=None, prec=None,
                 threshName=None, delayedTransfer=None,
                 batchElimination=None, batchCutoff=None):
    
    if threshName != None:
      self.threshName = threshName
      self.options = " with %s threshold" % string.join(self.threshName, "-")
    if delayedTransfer != None:
      self.delayedTransfer = delayedTransfer
    if batchElimination != None:
      self.batchElimination = batchElimination
    if batchCutoff != None:
      self.batchCutoff = batchCutoff
    UnitarySTV.setOptions(self, debug, strongTieBreakMethod, prec)

  ###
    
  def transferSurplusVotes(self):
    "Transfer surplus votes with random transfer rules."

    (c0, descChoose) = self.chooseSurplusToTransfer()
    self.action[self.R] = ("surplus", [c0])

    # transfer whole votes in excess of the threshold
    surplus = int(self.count[self.R-1][c0] - self.thresh[self.R-1])
    for i in self.votes[c0][:surplus]:
      c = self.topChoice(self.b.raw[i], self.purgatory)
      if c != None:
        self.votes[c].append(i)

    self.votes[c0] = []

    desc = "Count after transferring surplus votes from %s. " %\
           self.b.names[c0]
    desc += descChoose
    return desc

  ###

  def eliminateCandidates(self):
    "Eliminate candidates according to the random transfer rules."

    (elimList, descChoose) = self.chooseCandidatesToEliminate()
    self.action[self.R] = ("eliminate", elimList)
    
    # Transfer whole votes from losers.
    for loser in elimList:
      for i in self.votes[loser]:
        c = self.topChoice(self.b.raw[i], self.purgatory)
        if c != None:
          self.votes[c].append(i)
      self.votes[loser] = []

    desc = "Count after eliminating %s and transferring votes. "\
          % self.joinList(elimList)
    desc += descChoose
    return desc

##################################################################
##################################################################
##################################################################

class GregorySTV(STV):
  """Base class for all Gregory STV methods.  This class defines
  functions and variables used by Gregory STV methods.  It is not
  itself a complete election method and must be sub-classed and
  further defined."""
  
  def __init__(self, b):

    STV.__init__(self, b)

  ###

  def initialize(self):
    STV.initialize(self)
    self.f = [self.p] * len(self.b.packed)
    # Gregory rules do last batch transfers
    self.batches = []
    for c in range(self.b.nCand):  # Need to store batches for each cand.
      self.batches.append([])
    
  ###

  def initialVoteTally(self):
    "Count the first place votes with Gregory rules."

    # Allocate votes to candidates based on the first choices.
    for i in xrange(len(self.b.packed)):
      c = self.topChoice(self.b.packed[i], self.purgatory)
      if c != None: self.votes[c].append(i)

    # The first batch is all the votes a candidate has.
    for c in range(self.b.nCand):
      self.batches[c].append(self.votes[c][:])
    self.action[self.R] = ("first", [])
    return "Count of first choices. "

  ###

  def transferSurplusVotes(self):
    "Transfer surplus votes according to the Gregory rules."

    (c0, descChoose) = self.chooseSurplusToTransfer()
    self.action[self.R] = ("surplus", [c0])

    # Each candidate will receive a new batch of votes so
    # create a data structure to store the vote indices.
    newBatch = []
    for c in range(self.b.nCand):
      newBatch.append([])

    # We need to compute several quantities:
    #   surplus -- the number of votes of the transferor over quota
    #   batchValue -- value of all votes in the batch of the transferor
    #   transferableValue -- batchValue minus exhausted votes
    # batchValue is not currently used but I may need it later.
    if self.method == "ERS97 STV":
      quota = self.quota[self.R-1]
    elif self.method in ["N. Ireland STV"]:
      quota = self.thresh[self.R-1]
    surplus = self.count[self.R-1][c0] - quota
    lastBatch = self.batches[c0][-1]
    batchValue = 0
    transferableValue = 0
    nTransferable = 0
    for i in lastBatch:
      batchValue += self.b.weight[i] * self.f[i]
      if self.topChoice(self.b.packed[i], self.purgatory) != None:
        transferableValue += self.b.weight[i] * self.f[i]
        nTransferable += self.p * self.b.weight[i]

    # Do the transfer
    for i in lastBatch:
      if transferableValue > surplus:
        self.f[i] = self.p * surplus / nTransferable
      c = self.topChoice(self.b.packed[i], self.purgatory)
      if c!= None:
        self.votes[c].append(i)
        newBatch[c].append(i)

    # for candidates who received votes, add new batch
    for c in self.purgatory:
      if len(newBatch[c]) > 0:
        self.batches[c].append(newBatch[c])

    self.votes[c0] = []

    desc = "Count after transferring surplus votes from %s. " %\
           self.b.names[c0]
    desc += descChoose
    return desc

  ###

  def updateCount(self):
    "Update the vote totals after a transfer of votes."

    # If we are in the process of transferring surplus votes, then
    # the transferor needs to be treated specially.
    if self.action[self.R][0] == "surplus":
      cSurplus = self.action[self.R][1][0] # always array of 1
      self.winnersOver.remove(cSurplus)

    # Update counts for losers, purgatory, and winnersOver.
    # Because of substage transfers with ERS97, losing candidates
    # will sometimes have a count greater than 0.  For, all other methods
    # losers will always have 0 votes.
    for c in self.losers + self.purgatory + self.winnersOver:
      self.count[self.R][c] = 0
      for i in self.votes[c]:
        self.count[self.R][c] += self.b.weight[i] * self.f[i]

    # Set counts for winnersEven.  This will always be the same as the
    # previous round.
    for c in self.winnersEven:
      self.count[self.R][c] = self.count[self.R-1][c]

    # Set counts for the candidate in transition from winnersOver to
    # winnersEven.  The transferor must be treated differently from
    # winnersOver and winnersEven.
    if self.action[self.R][0] == "surplus":
      if self.method == "N. Ireland STV":
        self.count[self.R][cSurplus] = self.thresh[self.R-1]
      elif self.method == "ERS97 STV":
        self.count[self.R][cSurplus] = self.quota[self.R-1]
      else:
        assert(0)

    # Compute the number of exhausted votes.
    self.exhausted[self.R] = self.p * self.b.nBallots
    for c in range(self.b.nCand):
      self.exhausted[self.R] -= self.count[self.R][c]

    # Put the transferor where he belongs.
    if self.action[self.R][0] == "surplus":
      self.winnersEven.append(cSurplus)

    return ""

  ###

  def transferVotesWithValue(self, v):
    "Eliminate candidates according to the Gregory rules."

    # Set up holders for transferees
    newBatch = []
    for c in range(self.b.nCand):
      newBatch.append([])

    # Transfer votes of this value
    for i in self.votesByTransferValue[v]:
      c = self.topChoice(self.b.packed[i], self.purgatory)
      if c != None:
        self.votes[c].append(i)
        newBatch[c].append(i)
      # Don't know where this vote came from so try all losers
      for d in self.losers:
        if i in self.votes[d]:
          self.votes[d].remove(i)

    # For candidates who received votes, add new batch
    for c in self.purgatory:
      if len(newBatch[c]) > 0:
        self.batches[c].append(newBatch[c])
        
  ###

  def eliminateCandidates(self):
    "Eliminate candidates and transfer votes according to Gregory rules."
    
    (losers, desc) = self.chooseCandidatesToEliminate()
    self.action[self.R] = ("eliminate", losers)
    self.sortVotesByTransferValue(losers)
    nTransferValues = len(self.transferValues)

    if nTransferValues == 0:
      # This will happen when all eliminated candidates have 0 votes
      desc += self.updateCount()
      desc += self.updateThresh()
      desc += self.updateSurplus()
      desc += "Count after eliminating %s. No votes are "\
              "transferred since all eliminated candidates "\
              "have zero votes. " % self.joinList(losers)
      desc += self.updateWinners()
      self.msg[self.R] = desc
      return

    for i, v in enumerate(self.transferValues):
      if self.method == "N. Ireland STV" and i == 0:
        desc += "Count after eliminating %s and transferring "\
               "votes. " % self.joinList(losers)
      if self.method == "ERS97 STV":
        if i != 0:
          self.msg[self.R] = desc
          desc = ""
          self.R += 1
          self.allocateRound()
          self.action[self.R] = self.action[self.R-1]
          self.stages[self.S].append(self.R)
        desc += "Count after substage %d of %d of eliminating "\
                "%s. Transferred votes with value %s. "\
                % (i+1, nTransferValues, self.joinList(losers),
                   self.displayValue(v))
      self.transferVotesWithValue(v)
      desc += self.updateCount()
      desc += self.updateThresh()
      desc += self.updateSurplus()
      desc += self.updateWinners()
      (done, descOver) = self.electionOver()
      if done:
        self.msg[self.R] = desc
        return

    self.msg[self.R] = desc
    return

  ###

  def runElection(self):
    "Count the votes with Gregory rules."

    self.initialize()

    # Count first place votes
    self.allocateRound()
    self.msg[self.R] += self.initialVoteTally()    
    self.msg[self.R] += self.updateCount()
    self.msg[self.R] += self.updateThresh()
    self.msg[self.R] += self.updateSurplus()
    self.msg[self.R] += self.updateWinners()
    if self.method == "ERS97 STV":
      self.stages.append([])
      self.stages[self.S].append(self.R)
    if self.debug:
      print self.generateTextResults(round=self.R)
    
    # Do another round...
    (done, descOver) = self.electionOver()
    while (not done):
      
      self.R += 1
      self.allocateRound()
      if self.method == "ERS97 STV":
        self.S +=1
        self.stages.append([])
        self.stages[self.S].append(self.R)

      # Check to see if there is a surplus to transfer
      (transferSurplus, descTransition) = self.isSurplusToTransfer()
      self.msg[self.R-1] += descTransition

      if transferSurplus:
        self.msg[self.R] += self.transferSurplusVotes()
        self.msg[self.R] += self.updateCount()
        self.msg[self.R] += self.updateThresh()
        self.msg[self.R] += self.updateSurplus()
        self.msg[self.R] += self.updateWinners()

      else:
        self.eliminateCandidates()

      (done, descOver) = self.electionOver()
      if self.debug:
        print self.generateTextResults(round=self.R)

    self.msg[self.R] += descOver
    self.msg[self.R] += self.updateStatus()

##################################################################

class ERS97STV(GregorySTV):
  """\
Method:
  ERS97 SRV

Rules:
  How to Conduct an Election by the Single Transferable Vote
  http://www.electoral-reform.org.uk/votingsystems/stvrules.htm

Description:
  This version of STV is promulgated by the Electoral Reform Society.
  Several countries base their STV implementations on these rules.
  
Options:
  None.

Validation:
  Validated against eSTV."""
  
  def __init__(self, b):
    
    self.method = "ERS97 STV"
    self.prec = 2
    GregorySTV.__init__(self, b)
    self.options = ""
    self.weakTieBreakMethod = "forward"
    self.threshName = ("ERS97", "Dynamic", "Fractional")
    self.delayedTransfer = True
    self.batchElimination = "Losers"

  ###

  def initialize(self):
    GregorySTV.initialize(self)
    # Data structures needed only for ERS97 rules.
    # ERS97 rules contain stages and substages, but each of these is a round.
    # Example:
    #   R S
    #   ---
    #   1 1
    #   2 2
    #   3
    #   4 3
    # We need to compute all of the rounds but only print the stages.
    # Round 3 is a substage between stages 2 and 3.  Substages occur when
    # transferring ballots from eliminated candidate and different ballots
    # have different values.  The stage involves transferring all of the
    # ballots, but each substage involves transferring ballots of a given
    # value.
    self.quota = []
    self.S = 0
    self.stages = []    # Stores rounds for each stage
                        # [ [0] [1] [2] [3 4] [5] ... ]

  ###

  def roundToStage(self, r):
    "Return the stage corresponding to a given round."
    for s in range(len(self.stages)):
      if r in self.stages[s]: return s
    assert(0)

  ###

  def allocateRound(self):
    "Add quota allocation."

    GregorySTV.allocateRound(self)
    self.quota.append(0)
    # These are copied from the previous round.  Depending on the situation,
    # they will be reused or updated in place.
    if self.R > 0:
      self.quota[self.R] = self.quota[self.R-1]
      self.thresh[self.R] = self.thresh[self.R-1]

  ###

  def updateThresh(self):
    "Compute the value of the ERS97 winning threshold."

    assert(self.threshName[0] == "ERS97")
    assert(self.threshName[1] == "Dynamic")
    assert(self.threshName[2] == "Fractional")
    desc = ""

    # The quota is recalculated at every round until there is at
    # least one winner.  Afterwards it is just repeated.
    if self.winners == []:
      quota, r = divmod(self.p*self.b.nBallots - self.exhausted[self.R],
                          self.nSeats+1)
      if r > 0: quota += 1
      if self.R == 0:
        desc2 = "The initial quota is %s. " % self.displayValue(quota)
      else:
        desc2 = "Since no candidate has been elected, the quota is reduced "\
                "to %s. " % self.displayValue(quota)
      desc += desc2
    else:
      quota = self.quota[self.R]

    # The winning threshold changes every round.  See ERS97 rules
    # for an explanation.
    totalActiveVote = 0
    for c in self.purgatory + self.losers:
      totalActiveVote += self.count[self.R][c]
    for c in self.winnersOver:
      if self.count[self.R][c] > quota:
        totalActiveVote += self.count[self.R][c] - quota
    nSeatsRemaining = self.nSeats - len(self.winners)
    if nSeatsRemaining > 0:
      thresh, r = divmod(totalActiveVote, nSeatsRemaining+1)
      if r > 0: thresh += 1
    else:
      thresh = self.thresh[self.R]

    self.quota[self.R] = quota
    self.thresh[self.R] = thresh

    return desc

  ###

  def updateSurplus(self):
    "Compute the threshold and surplus for current round."

    # Update surplus
    self.surplus[self.R] = 0
    for c in self.winnersOver + self.purgatory:
      if self.count[self.R][c] > self.quota[self.R]:
        self.surplus[self.R] += self.count[self.R][c] - self.quota[self.R]
    return ""

  ###

  def updateWinners(self):
    "Find new winning candidates."

    # ERS97 is a pain because it can happen that there is one more
    # candidate over thresh than there are spots remaining!
    # If this happens there will be a tie.

    # When there are not enough votes, thresh can go to 0.00.
    # When this happens, every remaining candidate would be a winner
    # (even those with 0 votes).  Require at least 0.01 votes to be a
    # winner.

    # count the number of winners
    desc = ""
    potWinners = []
    for c in self.purgatory:
      if self.count[self.R][c] >= max(self.thresh[self.R], 1):
        potWinners.append(c)

    # if there is an extra do tie breaking
    assert(len(potWinners) + len(self.winners) <= self.nSeats + 1)
    if len(potWinners) + len(self.winners) == self.nSeats + 1:
      (c, desc2) = self.breakWeakTie(self.R, potWinners, "fewest",
                                     "a candidate over threshold to eliminate")
      desc += desc2
      potWinners.remove(c)

    # change status of all winners
    if len(potWinners) > 0:
      potWinners.sort(key=lambda a, f=self.count[self.R]: -f[a])
      desc2 = self.newWinners(potWinners)
      desc += desc2
      desc2 = self.updateThresh()
      desc += desc2
      self.updateSurplus()
      # lowered threshold could create new winners
      if len(self.winners) < self.nSeats:
        desc2 = self.updateWinners()
        desc += desc2

    return desc

  ###

  def updateStatus(self):
    "Update status for ERS97"

    self.nStages = self.S+1
    return GregorySTV.updateStatus(self)

  ###

  def sortVotesByTransferValue(self, list):
    "Sort votes according to ERS97 rules."

    self.votesByTransferValue = {}
    for loser in list:
      for i in self.votes[loser]:
        v = self.f[i]
        if v not in self.votesByTransferValue.keys():
          self.votesByTransferValue[v] = []
        self.votesByTransferValue[v].append(i)

    self.transferValues = self.votesByTransferValue.keys()
    self.transferValues.sort(reverse=True)

##################################################################

class NIrelandSTV(GregorySTV):
  """\
Method:
  N. Ireland STV

Rules:
  The Local Elections (Northern Ireland) Order 1985.
  Statutory Instrument 1985 No. 454.
  Not available online.

Description:
  This version of STV is used for local elections in Northern Ireland.
  The rules are similar to the ERS97 rules but much simpler.

Options:
  None.

Validation:
  Not validated."""
  
  def __init__(self, b):
    
    self.method = "N. Ireland STV"
    self.prec = 2
    GregorySTV.__init__(self, b)
    self.options = ""
    self.weakTieBreakMethod = "forward"
    self.threshName = ("Droop", "Static", "Whole")
    self.delayedTransfer = True
    self.batchElimination = "Losers"

  ###

  def sortVotesByTransferValue(self, list):
    "Sort votes according to N. Ireland rules."

    self.votesByTransferValue = {}
    for loser in list:
      for i in self.votes[loser]:
        v = self.f[i]
        if i in self.batches[loser][0]:
          key = "first"
        else:
          key = v
        if key not in self.votesByTransferValue.keys():
          self.votesByTransferValue[key] = []
        self.votesByTransferValue[key].append(i)

    self.transferValues = self.votesByTransferValue.keys()
    if "first" in self.transferValues:
      self.transferValues.remove("first")
      self.transferValues.sort(reverse=True)
      self.transferValues.insert(0, "first")
    else:
      self.transferValues.sort(reverse=True)      

##################################################################
##################################################################
##################################################################

class InclusiveSTV(STV):
  """Base class for all inclusive STV methods.  This class defines
  functions and variables used by inclusive STV methods.  It is not
  itself a complete election method and must be sub-classed and
  further defined."""

  def __init__(self, b):
    
    STV.__init__(self, b)

  ###

  def initialize(self):
    STV.initialize(self)
    self.f = [self.p] * len(self.b.packed)
    
  ###

  def transferSurplusVotes(self):
    "Transfer the surplus votes of one candidate."

    (c0, descChoose) = self.chooseSurplusToTransfer()
    self.action[self.R] = ("surplus", [c0])

    # Transfer all of the votes at a fraction of their value
    surplus = self.count[self.R-1][c0] - self.thresh[self.R-1]
    for i in self.votes[c0][:]:
      self.f[i] = self.f[i] * surplus / self.count[self.R-1][c0]
      c = self.topChoice(self.b.packed[i], self.purgatory)
      if c != None:
        self.votes[c].append(i)

    self.votes[c0] = []

    desc = "Count after transferring surplus votes from %s with a transfer "\
           "value of %s/%s. " %\
           (self.b.names[c0],
            self.displayValue(surplus),
            self.displayValue(self.count[self.R-1][c0]))
    desc + descChoose
    return desc

  ###

  def updateCount(self):
    "Update the vote totals after a transfer of votes."

    # If we are in the process of transferring surplus votes, then
    # the transferor needs to be treated specially.
    if self.action[self.R][0] == "surplus":
      cSurplus = self.action[self.R][1][0] # always array of 1
      self.winnersOver.remove(cSurplus)

        # Update counts for losers, purgatory, and winnersOver.
    # Because of substage transfers with ERS97, losing candidates
    # will sometimes have a count greater than 0.  For, all other methods
    # losers will always have 0 votes.
    for c in self.losers + self.purgatory + self.winnersOver:
      self.count[self.R][c] = 0
      for i in self.votes[c]:
        self.count[self.R][c] += self.b.weight[i] * self.f[i]

    # Set counts for winnersEven.  This will always be the same as the
    # previous round.
    for c in self.winnersEven:
      self.count[self.R][c] = self.count[self.R-1][c]

    # Set counts for the candidate in transition from winnersOver to
    # winnersEven.  The transferor must be treated differently from
    # winnersOver and winnersEven.
    if self.action[self.R][0] == "surplus":
      self.count[self.R][cSurplus] = self.thresh[self.R-1]

    # Compute the number of exhausted votes.
    self.exhausted[self.R] = self.p * self.b.nBallots
    for c in range(self.b.nCand):
      self.exhausted[self.R] -= self.count[self.R][c]

    # Put the transferor where he belongs.
    if self.action[self.R][0] == "surplus":
      self.winnersEven.append(cSurplus)

    return ""

  ###

  def eliminateCandidates(self):
    "Eliminate a list of candidates."

    (elimList, descChoose) = self.chooseCandidatesToEliminate()
    self.action[self.R] = ("eliminate", elimList)
    
    # Transfer votes from losers simulataneously.
    for loser in elimList:
      for i in self.votes[loser]:
        c = self.topChoice(self.b.packed[i], self.purgatory)
        if c != None:
          self.votes[c].append(i)
      self.votes[loser] = []

    desc = "Count after eliminating %s and transferring votes. "\
           % self.joinList(elimList)
    desc += descChoose
    return desc

##################################################################

class BCSTV(InclusiveSTV):
  """\
Method:
  British Columbia STV

Proposed Rules:
  British Columbia Citizen's Assembly Technical Report
  http://www.citizensassembly.bc.ca/resources/TechReport(full).pdf

Description:
  These rules have been proposed for the Province of British Columbia.
  This is a straightforward implementation of STV and recommended to
  organizations using STV for the first time.  See the Help menu for a
  more detailed description.  For an alternative description of the
  rules see
  http://www.fairvote.org/library/statutes/choice_voting.htm.
  
Options:
  None.

Validation:
  Not validated."""
  
  def __init__(self, b):
    
    self.method = "British Columbia STV"
    self.prec = 6
    InclusiveSTV.__init__(self, b)
    self.options = ""
    self.threshName = ("Droop", "Static", "Whole")
    self.delayedTransfer = False
    self.batchElimination = "Zero"

##################################################################

class ScottishSTV(InclusiveSTV):
  """\
Method:
  Scottish STV

Rules:
  The Scottish Local Government Elections Order 2007
  http://www.opsi.gov.uk/legislation/scotland/ssi2007/ssi_20070042_en.pdf
  
Description:
  Scotland enacted these rules for local elections in 2007.  This is a
  straightforward implementation of STV and recommended to
  organizations using STV for the first time.  Previous users of
  British Columbia STV should now use Scottish STV, as the only
  difference between the two sets of rules is that Scottish STV
  carries out computations to five decimal points rather than six.

Options:
  None.

Validation:
  Validated against eSTV."""
  
  def __init__(self, b):
    
    self.method = "Scottish STV"
    self.prec = 5
    InclusiveSTV.__init__(self, b)
    self.options = ""
    self.threshName = ("Droop", "Static", "Whole")
    self.delayedTransfer = False
    self.batchElimination = "None"

##################################################################

class GPCA2000STV(InclusiveSTV):
  """\
Method:
  Green Party of California STV

Description:
  Rules as adopted in December 2000.
  
Options:
  None.

Validation:
  Not validated."""
  
  def __init__(self, b):
    
    self.method = "GPCA2000 STV"
    self.prec = 5
    InclusiveSTV.__init__(self, b)
    self.options = ""
    self.weakTieBreakMethod = "random"
    self.threshName = ("Droop", "Static", "Fractional")
    self.delayedTransfer = False
    self.batchElimination = "Zero"

###

  def electionOver(self):
    "Election is over when we fill all the seats or eliminate all the losers."
    
    # Already recognized enough winners
    if len(self.winners) == self.nSeats:
      desc = "The election is over since all seats are filled. "
      return (True, desc)

    # A candidate must meet the static threshold to win a seat.
    if len(self.purgatory) == 0:
      desc = "The election is over since all candidates have been eliminated. "
      return (True, desc)

    # Not done yet.
    return (False, "")

##################################################################

class FTSTV(InclusiveSTV):
  """\
Method:
  Customizable Franctional Transfer STV

Description:
  This is a customizable implementation of fractional transfer STV.  The
  base method is similar Scottish STV.

Options:
  See the Help menu for a description of the options.

Validation:
  Not validated."""

  def __init__(self, b):

    self.method = "Fractional Transfer STV"
    self.prec = 6
    self.threshName = ("Droop", "Static", "Whole")
    self.delayedTransfer = False
    self.batchElimination = "Zero"
    self.batchCutoff = 0
    self.options = " with %s threshold" % string.join(self.threshName, "-")
    InclusiveSTV.__init__(self, b)

  ###

  def setOptions(self, debug=None, strongTieBreakMethod=None, prec=None,
                 threshName=None, delayedTransfer=None,
                 batchElimination=None, batchCutoff=None):
    
    if threshName != None:
      self.threshName = threshName
      self.options = " with %s threshold" % string.join(self.threshName, "-")
    if delayedTransfer != None:
      self.delayedTransfer = delayedTransfer
    if batchElimination != None:
      self.batchElimination = batchElimination
    if batchCutoff != None:
      self.batchCutoff = batchCutoff
    InclusiveSTV.setOptions(self, debug, strongTieBreakMethod, prec)

##################################################################
##################################################################
##################################################################

class RecursiveSTV(STV):
  """Base class for all recursive STV methods.  This class defines
  functions and variables used by recursive STV methods.  It is not
  itself a complete election method and must be sub-classed and
  further defined."""

  def __init__(self, b):
    
    self.threshName = ("Droop", "Dynamic", "Fractional")
    self.prec = 6
    self.options = " with %s threshold" % string.join(self.threshName, "-")
    STV.__init__(self, b)

  ###

  def initialize(self):
    STV.initialize(self)
    self.f = []

  ###

  def setOptions(self, debug=None, strongTieBreakMethod=None, prec=None,
                 threshName=None):
    
    if threshName != None:
      self.threshName = threshName
      self.options = " with %s threshold" % string.join(self.threshName, "-")
    STV.setOptions(self, debug, strongTieBreakMethod, prec)

  ###

  def checkMinRequirements(self):
    "Only attempt to count votes if there are enough candidates and voters."
    
    STV.checkMinRequirements(self)

    # Meek precondition -- apply to all methods
    withSupport = set(range(self.b.nCand))
    for b in self.b.packed:
      for c in b:
        withSupport.add(c)
      if len(withSupport) >= self.nSeats:
        break
    if len(withSupport) < self.nSeats:
      raise RuntimeError, "Not enough candidates with support to run an "\
            "election."
    
  ###

  def allocateRound(self):
    "Add keep value allocation."

    STV.allocateRound(self)
    self.f.append([0] * self.b.nCand)
    
  ###

  def initializeTreeAndKeepValues(self):
    "Initialize the tree data structure and candidate keep values."

    # The tree stores exactly the ballot information needed to count the
    # votes.  The first level of the tree is the top active candidate
    # (winner or in purgatory).  Since for winning candidates, a portion
    # of the ballot goes to the next candidate, the tree is extended until
    # it reaches a candidate in purgatory or the ballot is exhausted.

    # In the beginning, all candidates are in purgatory so there is only
    # one level in the tree.
    self.tree = {}
    for i in xrange(len(self.b.packed)):
      self.addBallotToTree(self.tree, i)

    # fractions so that candidates don't go over threshold
    for c in range(self.b.nCand):
      self.f[0][c] = self.p

  ##
      
  def addBallotToTree(self, tree, ballotIndex, ballot=""):
    "Add one ballot to the tree."

    if ballot == "": ballot = self.b.packed[ballotIndex]
    weight = self.b.weight[ballotIndex]
    
    c = self.topChoice(ballot, self.purgatory + self.winners)

    if c == None:
      # This will happen if the ballot contains only winning and losing
      # candidates.  The ballot index will not need to be transferred
      # again so it can be thrown away.
      return

    # Create space if necessary.
    if not tree.has_key(c):
      tree[c] = {}
      tree[c]["n"] = 0
      tree[c]["bi"] = []

    tree[c]["n"] += weight

    if c in self.winners:
      # Because candidate is a winner, a portion of the ballot goes to
      # the next candidate.  Pass on a truncated ballot so that the same
      # candidate doesn't get counted twice.
      i = ballot.index(c)
      ballot2 = ballot[i+1:]
      self.addBallotToTree(tree[c], ballotIndex, ballot2)
    else:
      # Canidate is in purgatory so we stop here.
      tree[c]["bi"].append(ballotIndex)
      
  ###

  def updateTree(self, tree):
    "Update the tree data structure to account for new winners and losers."

    for c in tree.keys():
      if c == "n": continue
      if c == "bi": continue

      if c in self.losers:
        # The current candidate is a loser, so the current node needs to be
        # removed from the tree.  Lower nodes, corresponding to lower ranked
        # candidates are merged with nodes at this same level.
        for i in tree[c]["bi"]:
          ballot = self.b.packed[i]
          j = ballot.index(c)
          ballot2 = ballot[j+1:]
          self.addBallotToTree(tree, i, ballot2)
        del tree[c]

      elif c in self.winners and len(tree[c]["bi"]) > 0:
        # The current candidate is a new winner (has ballot indices), so
        # expand this node to the next level.  There is no need to call
        # updateTree() recursively since addBallotToTree() will appropriately
        # expand lower nodes.
        for i in tree[c]["bi"]:
          ballot = self.b.packed[i]
          j = ballot.index(c)
          ballot2 = ballot[j+1:]
          self.addBallotToTree(tree[c], i, ballot2)
        tree[c]["bi"] = []

      elif c in self.winners:
        # The current candidate is an old winner, so recurse to see if
        # anything needs to be done at lower levels.
        self.updateTree(tree[c])

      # If c is in purgatory, then no updating is required.

  ###

  def updateCount(self):
    "Count ballots for one round."

    self.treeCount(self.tree, self.p)

    # compute thresh and surplus
    self.exhausted[self.R] = self.p*self.b.nBallots
    for c in self.winners + self.purgatory:
      self.exhausted[self.R] -= self.count[self.R][c]
    self.updateThresh()
    for c in self.winners + self.purgatory:
      if self.count[self.R][c] > self.thresh[self.R]:
        self.surplus[self.R] += self.count[self.R][c] - self.thresh[self.R]

    return ""
  
  ###

  def chooseCandidatesToEliminate(self):
    "Eliminate any losing candidates."
    
    desc = ""

    losers = self.getLosers()
    if self.surplus[self.R-1] == 0 and losers == []:
      (c, desc) = self.breakWeakTie(self.R-1, self.purgatory, "fewest",
                                    "candidates to eliminate")
      losers = [c]

    # Special case to prevent infinite loops caused by fixed precision
    if (losers == [] and
        self.R > 1 and
        self.count[self.R-1] == self.count[self.R-2] and
        self.f[self.R-1] == self.f[self.R-2]):
      desc = "Candidates tied within precision of computations. "
      (c, desc2) = self.breakWeakTie(self.R-1, self.purgatory, "fewest",
                                     "candidates to eliminate")
      losers = [c]
      desc += desc2

    return losers, desc
    
  ###

  def eliminateLosers(self, losers):
    "Eliminate any losing candidates."
    
    self.newLosers(losers)
    desc = "Count after eliminating %s and transferring votes. "\
           % self.joinList(losers)
    return desc

  ###

  def copyKeepValues(self):
    "Udpate the candidate keep values."

    for c in self.purgatory + self.winners:
      self.f[self.R][c] = self.f[self.R-1][c]

  ###

  def updateKeepValues(self):
    "Udpate the candidate keep values."

    if self.winners != []:
      desc = "Keep values of candidates who have exceeded the threshold: "
      list = []
    else:
      desc = ""

    for c in self.purgatory + self.winners:
      if self.count[self.R-1][c] > self.thresh[self.R-1]:
        f, r = divmod(self.f[self.R-1][c] * self.thresh[self.R-1],
                      self.count[self.R-1][c])
        if r > 0: f += 1
        self.f[self.R][c] = f
        list.append("%s, %s" % (self.b.names[c],
                                  self.displayValue(self.f[self.R][c])))
      else:
        self.f[self.R][c] = self.f[self.R-1][c]

    if self.winners != []:
      desc += self.joinList(list, convert="none") + ". "
    return desc

  ###

  def runElection(self):
    "Count the ballots using Meek STV."

    self.initialize()

    # Count first place votes
    self.R = 0
    self.allocateRound()
    self.initializeTreeAndKeepValues()
    self.updateCount()
    self.msg[self.R] += "Count of first choices. "
    desc = self.updateWinners()
    self.msg[self.R] += desc
    if self.debug: print self.generateTextResults(round=self.R)

    (done, descOver) = self.electionOver()
    while (not done):

      self.R += 1
      self.allocateRound()

      (losers, descChoose) = self.chooseCandidatesToEliminate()
      self.action[self.R] = ("eliminate", losers)
      if losers != []:
        descTrans = self.eliminateLosers(losers)
        self.msg[self.R] += descTrans + descChoose
        self.updateTree(self.tree)
        self.copyKeepValues()
        self.updateCount()
      elif self.surplus[self.R-1] > 0:
        self.msg[self.R] += "Count after transferring surplus votes. "
        self.updateTree(self.tree)
        desc = self.updateKeepValues()
        self.msg[self.R] += desc
        self.updateCount()
      else:
        assert(0)

      desc = self.updateWinners()
      self.msg[self.R] += desc
      if self.debug: print self.generateTextResults(round=self.R)
      (done, descOver) = self.electionOver()

    self.msg[self.R] += descOver
    self.msg[self.R] += self.updateStatus()

##################################################################

class MeekSTV(RecursiveSTV):
  """\
Method:
  Meek STV

Description:
  Provides very accurate proportional representation, but the count must
  be done with a computer and cannot be done by hand.

Options:
  Several variations of the quota are available.

Validation:
  Not validated."""

  def __init__(self, b):

    self.method = "Meek STV"
    RecursiveSTV.__init__(self, b)

  ###
    
  def treeCount(self, tree, remainder):
    "Traverse the tree to count the ballots."
    
    # Iterate over the next candidates on the ballots
    for c in tree.keys():
      if c == "n": continue
      if c == "bi": continue
      rrr = remainder
      self.count[self.R][c] += rrr * self.f[self.R][c] * tree[c]["n"] / self.p
      rrr = rrr * (self.p - self.f[self.R][c]) / self.p
      # If ballot not used up, keep going
      if rrr > 0:
        self.treeCount(tree[c], rrr)

##################################################################

class WarrenSTV(RecursiveSTV):
  """\
Method:
  Warren STV

Description:
  Provides very accurate proportional representation, but the count must
  be done with a computer and cannot be done by hand.

Options:
  Several variations of the quota are available.

Validation:
  Not validated."""

  def __init__(self, b):

    self.method = "Warren STV"
    RecursiveSTV.__init__(self, b)

  ###

  def treeCount(self, tree, remainder):
    # Iterate over the next candidates on the ballots
    for c in tree.keys():
      if c == "n": continue
      if c == "bi": continue
      rrr = remainder
      if self.f[self.R][c] < rrr:
        self.count[self.R][c] += self.f[self.R][c] * tree[c]["n"]
        rrr -= self.f[self.R][c]
      else:
        self.count[self.R][c] += rrr * tree[c]["n"]
        rrr = 0
      # If ballot not used up and more candidates, keep going
      if rrr > 0:
        self.treeCount(tree[c], rrr)

##################################################################
class RecursiveXSTV(RecursiveSTV):
  """Base class for all recursive STV methods.  This class defines
  functions and variables used by recursive STV methods.  It is not
  itself a complete election method and must be sub-classed and
  further defined."""

  def __init__(self, b):
    
    #
    #  A note for debugging via print:
    #  comment out the sys.stderr assignment in Frame.__init__
    #  and then print to stderr thus to send output to terminal:
    #  print >> sys.stderr, "MeekX: prec:", prec, "ties:", strongTieBreakMethod
    #
    RecursiveSTV.__init__(self, b)
    self.weakTieBreakMethod = "random"

  def initialize(self):
    RecursiveSTV.initialize(self)
    guard = (self.prec+1)/2
    self.p = 10**(self.prec+guard)
    self.g = 10**guard
    self.grnd = self.g/2  # for rounding
    self.geps = self.g/10 # epsilon (for comparison)
    self.setFields()

  def _eq_(self, a, b):
    "MeekX: return True if a == b"
    return abs(a - b) < self.geps

  def _lt_(self, a, b):
    "MeekX: return True if a < b"
    return (a < b) and not self._eq_(a, b)

  def _gt_(self, a, b):
    "MeekX: return True if a > b"
    return (a > b) and not self._eq_(a, b)

  def _le_(self, a, b):
    "MeekX: return True if a <= b"
    return (a < b) or self._eq_(a, b)

  ###
    
  def displayValue(self, value):
    "Format a value with specified precision."

    if self.prec > 0:
      gvalue = (value + self.grnd)/self.g	# round off guard digits
      return self.nfmt % (gvalue/(self.p/self.g), gvalue%(self.p/self.g))
    else:
      return self.nfmt % (value/self.p)

  ###

  def updateThresh(self):
    "MeekX: Compute the value of the winning threshold."

    assert(self.threshName[0] == "Droop")
    assert(self.threshName[1] == "Dynamic")
    assert(self.threshName[2] == "Fractional")

    threshDen = self.nSeats + 1
    threshNum = self.p * self.b.nBallots - self.exhausted[self.R]
    thresh = threshNum/threshDen
    self.thresh[self.R] = thresh
    return ""

  ###

  def updateWinners(self):
    "MeekX: Find new winning candidates."

    winners = []
    for c in self.purgatory[:]:
      if self._gt_(self.count[self.R][c], self.thresh[self.R]):
        winners.append(c)
    desc = self.newWinners(winners)
    
    return desc

  ###

  def getLosers(self, ppp = None):
    "MeekX: Return all candidates who are sure losers."

    # Return all candidates who are sure losers but do not look at previous
    # rounds to break ties.  It will be slightly underinclusive.

    # If the surplus is zero and two or more candidates are tied for
    # last place, then one candidate could
    # be a sure loser by looking at previous rounds.  Such losers will not
    # be identified here.  Such losers can be found with breakWeakTie().
    # This will not affect delaying transfer of surplus since there will
    # not be a surplus in this situation.

    if ppp == None: ppp = self.purgatory
    R = self.R - 1
    maxNumLosers = len(ppp + self.winners) - self.nSeats
    ppp.sort(key=lambda a, f=self.count[R]: f[a])
    losers = []

    s = 0
    for i in range(maxNumLosers):
      c = ppp[i]
      cNext = ppp[i+1]
      s += self.count[R][c]
      if ( (i>0  and self._le_(s + self.surplus[R], self.count[R][cNext])) or 
           (i==0 and self._lt_(s + self.surplus[R], self.count[R][cNext])) ):
        losers = ppp[:i+1]

    return losers

  ###

  def findTiedCand(self, cList, mostfewest, function):
    "MeekX: Return a list of candidates tied for first or last."

    assert(mostfewest in ["most", "fewest"])
    assert(len(cList) > 0)
    tiedCand = []

    # Find a candidate who is winning/losing.  He may be tied with others.
    if mostfewest == "most":
      cList.sort(key=lambda a, f=function: -f[a])
    elif mostfewest == "fewest":
      cList.sort(key=lambda a, f=function: f[a])
    top = cList[0] # first/last place candidate

    # Find the number of candidates who are tied with him.
    for c in cList:
      if self._eq_(function[c], function[top]):
        tiedCand.append(c)

    return tiedCand

##################################################################

class MeekXSTV(RecursiveXSTV, MeekSTV):
  """\
Method:
  Meek STV with guard bits and quasi-exact rounding

Description:
  Provides very accurate proportional representation, but the count must
  be done with a computer and cannot be done by hand.

Options:
  Precision (default 6 digits).

Validation:
  Not validated."""

  def __init__(self, b):

    self.method = "MeekX STV"
    RecursiveXSTV.__init__(self, b)

##################################################################

class WarrenXSTV(RecursiveXSTV, WarrenSTV):
  """\
Method:
  Warren STV with guard bits and quasi-exact rounding

Description:
  Provides very accurate proportional representation, but the count must
  be done with a computer and cannot be done by hand.

Options:
  Precision (default 6 digits).

Validation:
  Not validated."""

  def __init__(self, b):

    self.method = "WarrenX STV"
    RecursiveXSTV.__init__(self, b)

##################################################################
## Command line execution
##################################################################

if __name__ == '__main__':

  import getopt
  import os.path
  from  ballots import *
  
  usage = """
Usage:

    STV.py [-d] ballots.blt method
        Runs an election for the given ballots and method.  The results are
        printed to stdout.
"""

  # Parse the command line.
  try:
    (opts, args) = getopt.getopt(sys.argv[1:], "d")
  except getopt.GetoptError:
    print usage
    sys.exit(-1)

  debug = False
  for o, a in opts:
    if o == "-d":
      debug = True
      
  if len(sys.argv) != 3:
    print usage
    sys.exit(-1)

  bltFn = sys.argv[1]
  method = sys.argv[2]

  b = Ballots.loadKnown(bltFn)

  cmd = method + "(b, strongTieBreakMethod='alpha')"
  e = eval(cmd)
  e.debug = debug
  e.runElection()
  txt = e.generateTextResults()
  print txt

  del b
  del e
