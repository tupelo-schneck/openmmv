from NonSTV import Condorcet
from STV import MeekSTV

class LER(MeekSTV):
    def __init__(self, b):
        MeekSTV.__init__(self, b)
        self.method = "LER"
        self.LERa = True
        self.LERb = False
        self.options = " with %s threshold" % string.join(self.threshName, "-")
        self.options = ("a" if self.LERa else "") + ("b" if self.LERb else "") + self.options

    def setOptions(self, debug=None, strongTieBreakMethod=None, prec=None,
                 threshName=None, LERa=None, LERb=None):
        MeekSTV.setOptions(self, debug, strongTieBreakMethod, prec)
        if LERa != None:
            self.LERa = LERa
        if LERb != None:
            self.LERb = LERb
        self.options = " with %s threshold" % string.join(self.threshName, "-")
        self.options = ("a" if self.LERa else "") + ("b" if self.LERb else "") + self.options

    def initialize(self):
        condorcetElection = Condorcet(self.b)
        condorcetElection.runElection()
        # handle withdrawals gracefully
        self.b = condorcetElection.b
        self.LERaWinner = None
        self.LERbWinner = None
        if self.LERb:
            self.LERbWinner = condorcetElection.winner
            if self.LERa and self.b.nSeats > 1:
                condorcetElection = Condorcet(self.b)
                condorcetElection.withdrawn.append(self.LERbWinner)
                condorcetElection.runElection()
                self.LERaWinner = self.b.names.index(condorcetElection.b.names[condorcetElection.winner])
        else:
            self.LERaWinner = condorcetElection.winner
        MeekSTV.initialize(self)
        if self.LERbWinner != None:
            # temporarily mark LERbWinner as a loser.
            self.purgatory.remove(self.LERbWinner)
            self.losers.append(self.LERbWinner)
            self.lostAtRound[self.LERbWinner] = 0
            self.nSeats -= 1

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
            self.nSeats += 1
            self.losers.remove(self.LERbWinner)
            self.winners.append(self.LERbWinner)
            self.lostAtRound[self.LERbWinner] = None
            self.wonAtRound[self.LERbWinner] = 0

    def generateTextResults(self, maxWidth=80, style="full"):
        res = MeekSTV.generateTextResults(self)
        if self.LERbWinner != None:
            res += "\nLERb winner is " + self.b.names[self.LERbWinner] + ". "
        if self.LERaWinner != None:
            res += "\nLERa winner is " + self.b.names[self.LERaWinner] + ". "
        return res

class LERa(LER):
    def __init__(self,b):
        LER.__init__(self,b)
        self.setOptions(LERa=True,LERb=False)

class LERb(LER):
    def __init__(self,b):
        LER.__init__(self,b)
        self.setOptions(LERa=False,LERb=True)

class LERab(LER):
    def __init__(self,b):
        LER.__init__(self,b)
        self.setOptions(LERa=True,LERb=True)
