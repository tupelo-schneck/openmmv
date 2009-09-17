import itertools

from STV import *
from plugins import MethodPlugin
import projectBallots

class OldAndBusted(NonIterative,MethodPlugin):
    methodName = "OldAndBusted"
    longMethodName = "Old and Busted OTRA System"
    enabled = True

    htmlBody = """
<p>Description goes here.</p>
"""
  
    htmlHelp = (MethodPlugin.htmlBegin % (longMethodName, longMethodName)) +\
               htmlBody + MethodPlugin.htmlEnd

    def __init__(self,b):
        NonIterative.__init__(self,b)
        if not isinstance(b,projectBallots.ProjectBallots):
            projectBallots.upgradeBallot(b)

    # Unfortunate hacky dealing with the Elections Options Dialog with changing numSeats
    def getNumSeats(self):
        if hasattr(self,"b"):
            return self.b.numSeats
        return self._numSeats
    def setNumSeats(self,n):
        self._numSeats = n
    numSeats = property(getNumSeats,setNumSeats)

    def preCount(self):
        NonIterative.preCount(self)
        self.prec = 1
        self.p = 10**self.prec
        self.amount = [0] * self.b.numCandidates

    def checkMinRequirements(self):
        """Called from Election.preCount to abort silly elections.
        MMV removes most requirements.
        """
        if self.b.numSeats < 1:
            raise RuntimeError, "Not enough resources to run an election."

    def countBallots(self):
        self.nRounds = 1

        exhaustedCount = 0
        
        for i in xrange(self.b.numWeightedBallots):
            weight, cands, amts = self.b.getWeightedProjectBallot(i)
            sofar = 0
            for c,a in itertools.izip(cands,amts):
                if sofar + a <= self.b.numSeats:
                    self.count[c] += self.p * weight
                    self.amount[c] += self.p * weight * a
                elif sofar + self.b.minimum[c] <= self.b.numSeats:
                    a = self.b.numSeats - sofar
                    self.count[c] += self.p * weight
                    self.amount[c] += self.p * weight * a
                else:
                    continue
                sofar += a
                if sofar >= self.b.numSeats: break
            if sofar < self.b.numSeats:
                exhaustedCount += 1
                self.exhausted += weight * (self.b.numSeats - sofar)

        useable = self.p * self.b.numSeats
        candsWithCounts = [ (count, cand) for (cand, count) in enumerate(self.count) ]
        candsWithCounts.sort(reverse=True)
        sortedCands = [ cand for (_, cand) in candsWithCounts ]

        index = 0
        self.winners = []
        done = False
        while index < len(sortedCands) and not done:
            tiedCands = [sortedCands[index]]
            index += 1
            while index < len(sortedCands) and \
                      self.count[sortedCands[index]]==self.count[sortedCands[index-1]]:
                tiedCands.append(sortedCands[index])
                index += 1
            thisAmount = sum(self.p * self.amount[c] / self.count[c] for c in tiedCands)
            if exhaustedCount==self.count[tiedCands[0]]:
                thisAmount += self.exhausted
            multiplier = self.p
            if thisAmount > useable:
                multiplier = self.p * useable / thisAmount
                print useable
                print thisAmount
                print multiplier
                done = True
            for c in tiedCands:
                self.winners.append(c)
                winningAmount = multiplier * self.amount[c] / self.count[c]
                useable -= winningAmount
                self.msg += "Candidate %s wins with %s%s.\n" % (self.b.names[c], \
                                                                self.displayValue(winningAmount),\
                                                                " (truncated)" if done else "")
            if exhaustedCount==self.count[tiedCands[0]]:
                winningAmount = multiplier * self.exhausted / exhaustedCount
                useable -= winningAmount
                winningAmount /= self.p
                self.msg += "Exhaustion removes %s%s.\n" % (self.b.names[c], \
                                                                self.displayValue(winningAmount),\
                                                                " (truncated)" if done else "")
