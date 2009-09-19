from STV import *
from MeekSTV import MeekSTV
from Condorcet import Condorcet
from plugins import MethodPlugin

class LERPlugin(MeekSTV,MethodPlugin):
    methodName = "LER"
    longMethodName = "Loring Ensemble Rule"
    enabled = True

    htmlBody = """
<p>The Loring Ensemble Rule chooses a Condorcet winner
and then uses STV (Meek, in this case) to find other winners.
It could be used, for example, to elect a committee where
a central chair is desired (the Condorcet winner) as well
as more extreme representatives (the other winners).</p>

<p>Using option LERa, the Condorcet winner still goes through
the STV iterations (and thus takes votes from others), but
can't be eliminated.  Using option LERb, the Condorcet winner
is removed from the ballots before performing the STV
calculation.  LERab takes both (the Condorcet winner is the
LERb winner, then the Condorcet winner of the remaining
is the LERa winner).  Note that although a LERa winner can't
be eliminated, it could potentially still lose
in the STV stage if enough
other candidates are elected first!</p>
"""

    htmlHelp = (MethodPlugin.htmlBegin % (longMethodName, longMethodName)) +\
        htmlBody + MethodPlugin.htmlEnd

    def __init__(self, b):
        MeekSTV.__init__(self, b)
        self.LERoption = "LERa"
        self.completion = "Schwartz Sequential Dropping"
        self.createUIoptions(["completionMethod","LERoption"])

    def createUIoptions(self, list):
        for option in list:
            if option == "LERoption":
                self.UIoptions.append( ("""
label = wx.StaticText(self, -1, "LER option:")
control = wx.Choice(self, -1, choices = ["LERa", "LERb", "LERab"])
control.SetStringSelection("%s")""" % (self.LERoption),
                                "GetStringSelection()",
                                "LERoption") )
                list.remove(option)
        MethodPlugin.createUIoptions(self,list)

    def preCount(self):
        self.LERa = self.LERoption == "LERa" or self.LERoption == "LERab"
        self.LERb = self.LERoption == "LERb" or self.LERoption == "LERab"
        self.optionsMsg = "LER option: %s. \n" % self.LERoption
        self.optionsMsg += "Using %s for the completion method." % self.completion
        condorcetElection = Condorcet(self.dirtyBallots)
        condorcetElection.completion = self.completion
        condorcetElection.withdrawn = self.withdrawn[:]
        condorcetElection.runElection()
        self.LERaWinner = None
        self.LERbWinner = None
        if self.LERb:
            self.LERbWinner = condorcetElection.b.names[condorcetElection.winner]
            if self.LERa and self.dirtyBallots.numSeats > 1:
                condorcetElection2 = Condorcet(self.dirtyBallots)
                condorcetElection2.completion = self.completion
                condorcetElection2.withdrawn = self.withdrawn[:]
                condorcetElection2.withdrawn.append(self.dirtyBallots.names.index(self.LERbWinner))
                condorcetElection2.runElection()
                self.LERaWinner = condorcetElection2.b.names[condorcetElection2.winner]
        else:
            self.LERaWinner = condorcetElection.b.names[condorcetElection.winner]
        MeekSTV.preCount(self)
        # adapt names to indices, now that withdrawals are finalized
        if self.LERaWinner != None:
            self.LERaWinner = self.b.names.index(self.LERaWinner)
        if self.LERbWinner != None:
            print "evil %s in %s" % (self.LERbWinner , self.b.names)
            self.LERbWinner = self.b.names.index(self.LERbWinner)
            # temporarily mark LERbWinner as a loser.
            self.purgatory.remove(self.LERbWinner)
            self.losers.append(self.LERbWinner)
            self.lostAtRound[self.LERbWinner] = 0
            self.numSeats -= 1

    def initializeTreeAndKeepValues(self):
        # This is just to get a message into the first round.
        if self.LERbWinner != None:
            self.msg[self.R] += "LERb winner is " + self.b.names[self.LERbWinner] + ". "
        if self.LERaWinner != None:
            self.msg[self.R] += "LERa winner is " + self.b.names[self.LERaWinner] + ". "
        MeekSTV.initializeTreeAndKeepValues(self)

    # LERa winner can't be eliminated.  It can, however, still lose if enough
    # other candidates reach the threshold first...
    def breakWeakTie(self, R, cList, mostfewest, what=""):
        newCList = cList[:]
        if what == "candidates to eliminate":
            try:
                newCList.remove(self.LERaWinner)
            except ValueError:
                pass
        return MeekSTV.breakWeakTie(self,R,newCList,mostfewest,what)

    def getLosers(self, ppp = None):
        if ppp == None: ppp = self.purgatory
        ppp = ppp[:]
        try:
            ppp.remove(self.LERaWinner)
        except ValueError:
            pass
        return MeekSTV.getLosers(self,ppp)

    def runElection(self):
        MeekSTV.runElection(self)
        if self.LERbWinner != None:
            self.numSeats += 1
            self.losers.remove(self.LERbWinner)
            self.winners.append(self.LERbWinner)
            self.lostAtRound[self.LERbWinner] = None
            self.wonAtRound[self.LERbWinner] = 0
