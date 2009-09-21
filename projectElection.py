# Note: "keep value" self.f we use to men the portion of the total amount given
# by a single supporter.  In usual STV keep value means the portion of a ballot's
# support given by a single supporter.  These are obviously related by quota.
# In our case, using portion of share would mean that keep values would change
# when adding a new funding level.  For example: suppose each of 25 supporters gives
# $4 to get a project to $100.  Then the keep value is 4%.  That percentage also
# works at $50 (each supporter give 4%, that is $2).  However, portion of ballot
# changes: if a share is $8, each supporter gives 50% of the ballot to get the
# project to $100; but 25% to get it to 50 and 25% to get it from 50 to 100.

# New: split preferences.  Maybe we give $10 to A at preference 1, then $10 to B,
# then $10 more to A at preference 3 (for a total of $20).  The amount shown on the
# ballot will be $10 (that is, the amount given, not $20, the total desired at that
# point, as I had previously imagined).

# TODO: how we choose project to be eliminated
# TODO: epsilons & fudge factors --- including surplusLimit from OpenSTV
# TODO: ties



import itertools

from STV import *
from plugins import MethodPlugin
import projectBallots

class ProjectElection(RecursiveSTV,MethodPlugin):
    methodName = "MMV"
    longMethodName = "MMV (Movable Money Votes)"
    enabled = True

    htmlBody = """
<p>Description goes here.</p>
"""

    htmlHelp = (MethodPlugin.htmlBegin % (longMethodName, longMethodName)) +\
               htmlBody + MethodPlugin.htmlEnd


    def __init__(self, b):
        RecursiveSTV.__init__(self, b)
        if not isinstance(b,projectBallots.ProjectBallots):
            projectBallots.upgradeBallot(b)
        self.countingMethod = "Warren"
        self.createUIoptions(["countingMethod","prec"])

###

    # Unfortunate hacky dealing with the Elections Options Dialog with changing numSeats
    def getNumSeats(self):
        if hasattr(self,"b"):
            return self.b.numSeats
        return self._numSeats
    def setNumSeats(self,n):
        self._numSeats = n
    numSeats = property(getNumSeats,setNumSeats)

    def createUIoptions(self, list):
        for option in list:
            if option == "thresh0": list.remove(option)
            elif option == "thresh1": list.remove(option)
            elif option == "thresh2": list.remove(option)
            elif option == "countingMethod":
                self.UIoptions.append( ("""
label = wx.StaticText(self, -1, "Counting Method:")
control = wx.Choice(self, -1, choices = ["Meek", "Warren"])
control.SetStringSelection("%s")""" % (self.countingMethod),
                                "GetStringSelection()",
                                "countingMethod") )
                list.remove(option)
        MethodPlugin.createUIoptions(self,list)

###
    def displayAmountValue(self,value):
        "Format a value with specified precision."
        if self.amountPrec == 0:
            return str(value/self.p)
        nfmt = "%d.%0" + str(self.amountPrec) + "d" # %d.%0_d
        frac = value % self.p
        p = 10**(self.prec - self.amountPrec)
        f = frac/p
        if frac%p >= p/2: f+=1
        frac = f
        return nfmt % (value/self.p, frac)

    def preCount(self):
        """Called at start of election."""
        RecursiveSTV.preCount(self)
        self.threshName=("Hare", "Static", "Fractional")
        # round amounts to the nearest integer
        # Note: probably ballot should be checked to comply with this, if it is ever larger than self.p
        self.amountPrec = 1 # show tenths
        self.amountEpsilon = self.p
        # Meek or Warren?
        self.meek = self.countingMethod == "Meek"
        self.optionsMsg = "Counting method: %s." % self.countingMethod
        # Each ballot's share of the resources --- rounded down!
        self.share = self.p * self.b.numSeats / self.b.numBallots
        # Largest portion of a project that one supporter can pay.
        # Rounded up... that seems important.
        self.supportLimit = self.p
        if self.b.supportObligation!=None and self.b.supportObligation > 0:
            self.supportLimit = self.p * 100 / self.b.numBallots / self.b.supportObligation + 1
        if self.supportLimit > self.p:
            self.supportLimit = self.p
        # Copy of project min and max at precision specified by self.p
        self.minimum = [self.p*self.b.minimum[c] for c in xrange(self.b.numCandidates)]
        self.maximum = [self.p*self.b.maximum[c] for c in xrange(self.b.numCandidates)]
        # For these, see allocateRound
        self.winAmount = []
        self.eliminatedAbove = []
        self.resourcesWanted = []
        self.eliminableResources = []
        self.countDict = []

###

    def checkMinRequirements(self):
        """Called from Election.preCount to abort silly elections.
        MMV removes most requirements.
        """
        if self.b.numSeats < 1:
            raise RuntimeError, "Not enough resources to run an election."

###

    def allocateRound(self):
        """Called each iteration to set up data structures for the coming round (self.R)."""
        RecursiveSTV.allocateRound(self)
        # countDict : round -> candidate -> amount -> support
        #     it shows how much of that part of the amount is supported
        # f (factor) : round -> candidate -> amount -> fraction of the amount
        #     to be given by each supporter 
        self.countDict.append([0] * self.b.numCandidates)
        for c in xrange(self.b.numCandidates):
            self.countDict[self.R][c] = {}
            self.f[self.R][c] = {}
        # winAmount : round -> candidate -> what amount has already won
        # eliminatedAbove : round -> candidate -> highest amount not eliminated
        if self.R == 0:
            self.winAmount = [[0] * self.b.numCandidates]
            self.eliminatedAbove = [[self.maximum[p] for p in xrange(self.b.numCandidates)]]
        else:
            self.winAmount.append(self.winAmount[self.R-1][:])
            self.eliminatedAbove.append(self.eliminatedAbove[self.R-1][:])
        # resourcesWanted : round -> candidate -> how many more resources the candidate
        #     needs to be funded at the highest level suggested for it so far
        # eliminableResources : round -> candidate -> how much would be obtained
        #     by completely eliminating the candidate
        self.resourcesWanted.append([0] * self.b.numCandidates)
        self.eliminableResources.append([0] * self.b.numCandidates)

###

    def initializeTreeAndKeepValues(self):
        """Called at start of election to set up tree of ballots and keep values self.f."""
        RecursiveSTV.initializeTreeAndKeepValues(self)
        self.tree["bi"] = []
        self.tree["i"] = []
        for c in xrange(self.b.numCandidates):
            self.f[0][c] = {}

###

    def updateCount(self):
        """Called at end of each iteration to set count, exhausted, thresh, surplus."""

        # maxKeep: temporary round-to-round track of largest fraction of amount
        # actually given by any supporter.  This may be less than the calculated fraction f,
        # in which case we can take a (sometimes massive) shortcut and truncate f to this.
        self.maxKeep = [0] * self.b.numCandidates
        for c in xrange(self.b.numCandidates):
            self.maxKeep[c] = {}
        self.treeCount(self.tree, self.share)

        # compute thresh and surplus
        # Note: MMV doesn't actually use exhausted or thresh.
        self.exhausted[self.R] = self.share*self.b.numBallots
        for c in self.winners + self.purgatory:
		for v in self.countDict[self.R][c].values():
                   self.exhausted[self.R] -= v
        self.updateThresh()
        for c in self.winners + self.purgatory:
            prior = 0
            for amount in sorted(self.countDict[self.R][c].keys()):
                if self.countDict[self.R][c][amount] >= amount - prior:
                    self.surplus[self.R] += self.countDict[self.R][c][amount] - (amount - prior)
                prior = amount

    	return ""

###

    def updateWinners(self):
        """Called after updateCount to set winners and losers.
        MMV adds winAmount, eliminatedAbove, resourcesWanted, and eliminableResources.
        """
        winners = []
        winnersAmounts = {}
        desc = ""
        for c in self.purgatory:
            prior = 0
            for amount in sorted(self.countDict[self.R][c].keys()):
                if amount <= self.eliminatedAbove[self.R][c]:
                    if self.countDict[self.R][c][amount] >= amount - prior:
                        self.winAmount[self.R][c] = amount
                        winnersAmounts[c] = amount
                    else:
                        self.resourcesWanted[self.R][c] += amount - prior - self.countDict[self.R][c][amount]
                        self.eliminableResources[self.R][c] += self.countDict[self.R][c][amount]
                else:
                    break
                prior = amount

            if self.winAmount[self.R][c] == self.eliminatedAbove[self.R][c]:
                winners.append(c)

        self.newWinners(winners) # ignore returned string
        winners = winnersAmounts.keys()
        if len(winners) == 0:
            return ""
        elif len(winners) == 1:
            desc = "Candidate %s has reached the threshold and is elected. "\
                % self.b.joinList(["%s(%s)" % (self.b.names[w],self.displayAmountValue(winnersAmounts[w])) \
                                       for w in winners], convert="none")
        else:
            desc = "Candidates %s have reached the threshold and are elected. "\
                % self.b.joinList(["%s(%s)" % (self.b.names[w],self.displayAmountValue(winnersAmounts[w])) \
                                       for w in winners], convert="none")
        return desc

###

    def electionOver(self):
        """Called before each iteration."""

        if len(self.purgatory) <= 0:
            desc = "The election is over since all projects have won or been eliminated.  "
            self.msg[self.R] += desc
            return True

        # possible shortcut...?
        spent = 0
        for amount in self.winAmount[self.R]:
            spent += amount
        if spent >= self.share * self.b.numBallots:
            desc = "The election is over since all resources are spent. "
            self.msg[self.R] += desc
            return True

        # Not done yet.
        return False

###

    def getLosers(self, ppp = None):
        """Called at start of each iteration, via RecursiveSTV.chooseCandidatesToEliminate.
        Returns sure losers.
        MMV also sets resourcesWantedOfLeastNonLoser, in order to determine
        correct funding level at which to eliminate greatest loser.
        In MMV we eliminate first the projects which need the most resources;
        unlike OpenSTV this isn't the same as projects with the least count.
        """
        if ppp == None: ppp = self.purgatory
        R = self.R - 1
        ppp.sort(key=lambda a: -self.resourcesWanted[R][a])
        losers = []

        s = 0
        self.resourcesWantedOfLeastNonLoser = 0
        for i in xrange(len(ppp)):
            c = ppp[i]
            if i<len(ppp)-1:
                nextResourcesWanted = self.resourcesWanted[R][ppp[i+1]]
            else:
                nextResourcesWanted = 0 # TODO: make this some epsilon---in case we're willing to elect "close enough" projects
            # If you gave c all eliminable resources from even worse projects (s),
            # and all of the surplus, would it still want more than the next project?
            # If so c and all worse projects are sure losers.
            if self.resourcesWanted[R][c] - s - self.surplus[R] > nextResourcesWanted:
                losers = ppp[:i+1]
                self.resourcesWantedOfLeastNonLoser = nextResourcesWanted
            s += self.eliminableResources[R][c]

        return losers

###

    def breakWeakTie(self, R, cList, mostfewest, what=""):
        """If there are no sure losers, we'll need to pick somebody.
        We do this by looking at prior rounds to see which one was doing worse recently,
        if any.  If that doesn't work we call breakStrongTie and choose randomly.
        In order to reuse the OpenSTV code which looks at self.count, we maneuver
        self.resourcesWanted into self.count and look for the biggest.
        """
        savedcount = self.count
        self.count = self.resourcesWanted
        fewestmost = "most"
        if mostfewest == "most":
            fewestmost = "fewest"
        res = RecursiveSTV.breakWeakTie(self,R,cList,fewestmost,what)
        self.count = savedcount
        # This is important, as res isn't a sure loser, so we should just eliminate
        # a little bit.
        self.resourcesWantedOfLeastNonLoser = None
        return res

###

    def eliminateLosers(self, losers):
        """Perform an elimination.
        We have to work a lot harder than OpenSTV in order to figure out and set the
        eliminated funding levels.  The key is resourcesWantedOfLeastNonLoser.
        """
        R = self.R-1
        extraDesc = ""
        if self.resourcesWantedOfLeastNonLoser == None:
            # We chose a loser, who wasn't a sure loser.  Just eliminate a little.
            assert(len(losers)==1)
            amounts = [self.eliminatedAbove[R][losers[0]] - self.amountEpsilon]
            if amounts[0] < self.minimum[losers[0]]:
                amounts = [0]
        else:
            # All in losers are sure losers; all but the last should be
            # fully eliminated, and the last should eliminate just enough
            # that it can't want more than resourcesWantedOfLeastNonLoser
            amounts = []
            lastLoser = losers[len(losers)-1]
            allButLastEliminated = 0
            for l in losers[:-1]:
                amounts.append(self.winAmount[R][l])
                allButLastEliminated += self.eliminableResources[R][l]

            lastLoserAmount = self.eliminatedAbove[R][lastLoser] - \
                              (self.resourcesWanted[R][lastLoser] - self.surplus[R] - \
                               allButLastEliminated - self.resourcesWantedOfLeastNonLoser)
            lastLoserAmount = (lastLoserAmount / self.amountEpsilon) * self.amountEpsilon
            if lastLoserAmount < self.minimum[lastLoser] or lastLoserAmount <= self.winAmount[R][lastLoser]:
                lastLoserAmount = self.winAmount[R][lastLoser]
            else:
                extraDesc = ", and partially %s(>%s)," % (self.b.names[lastLoser],self.displayAmountValue(lastLoserAmount))
            amounts.append(lastLoserAmount)

        totalLosers = []
        winners = []
        for c, amount in itertools.izip(losers,amounts):
            self.eliminatedAbove[self.R][c] = amount
            if self.winAmount[self.R][c] == self.eliminatedAbove[self.R][c]:
                if self.winAmount[self.R][c] == 0:
                    totalLosers.append(c)
                else:
                    winners.append(c)

        self.newWinners(winners)
        self.newLosers(totalLosers)
        if len(totalLosers+winners) > 0 :
            desc = "Count after eliminating %s%s and transferring votes. "\
               % (self.b.joinList(["%s(>%s)" % (self.b.names[c],\
                                                    self.displayAmountValue(self.eliminatedAbove[self.R][c]))\
                                       for c in totalLosers+winners], convert="none"),  extraDesc)
        return desc

###

    def copyKeepValues(self):
        """Called after an elimination."""
        for c in self.purgatory + self.winners:
            self.f[self.R][c] = self.f[self.R-1][c].copy()
            for amount in self.maxKeep[c].keys():
                if amount > self.winAmount[self.R-1][c]:
                    continue
                if self.f[self.R][c].get(amount,self.supportLimit) > self.maxKeep[c][amount]:
                    self.f[self.R][c][amount] = self.maxKeep[c][amount]
            # only keys for winners, so no need to look at eliminateds

###

    def updateKeepValues(self):
        """Called in a non-eliminating round."""

        if self.winners != []:
            desc = "Keep values of candidates who have exceeded the threshold: "
            list = []
        else:
            desc = ""

        for c in self.purgatory + self.winners:
            prior = 0
            for amount in sorted(self.countDict[self.R-1][c].keys()):
                if amount > self.winAmount[self.R-1][c]:
                    break
                oldf = self.f[self.R-1][c].get(amount,self.supportLimit)
                if oldf > self.maxKeep[c].get(amount,self.p):
                    oldf = self.maxKeep[c][amount]
                # round up calculation of new f
                f, r = divmod(oldf * (amount - prior),
                      self.countDict[self.R-1][c][amount])
                if r > 0: f += 1
                self.f[self.R][c][amount] = f
                prior = amount
                list.append("%s(%s), %s" % (self.b.names[c], self.displayAmountValue(amount),
                                  self.displayValue(f)))

        if list != []:
            desc += self.b.joinList(list, convert="none") + ". "
        else:
            desc += "None (shouldn't happen?) "
        return desc

###

    def addBallotToTree(self, tree, ballotIndex, start=0):
        """Part of tree counting.  Adds one ballot to this tree."""

        weight, ballot, amounts = self.b.getWeightedProjectBallot(ballotIndex)
        ballot = ballot
        amounts = amounts

        nextStart = start + 1
        prior = [0] * self.b.numCandidates
        for i, (c, bamount) in enumerate(itertools.izip(ballot,amounts)):
            if i >= start:
                nextStart = i + 1
            if c in self.purgatory + self.winners and prior[c] < self.eliminatedAbove[self.R][c]:
                if i >= start:
                    amount = bamount * self.p + prior[c]
                    amount = min(amount, self.eliminatedAbove[self.R][c])
                    break
                prior[c] += bamount * self.p
        else:
            # This will happen if the ballot contains only winning and losing
            # candidates.  The ballot index will not need to be transferred
            # again so it can be thrown away.
            return

        key = (c, amount, prior[c])

        # Create space if necessary.
        if not key in tree:
            tree[key] = {}
            tree[key]["n"] = 0
            tree[key]["i"] = [] # for each ballot in bi, which index to start at?
            tree[key]["bi"] = []

        tree[key]["n"] += weight
        tree[key]["bi"].append(ballotIndex) # we lazily instantiate the tree
        tree[key]["i"].append(nextStart)

###

    def updateTree(self, tree):
        """This is called each round before counting to modify the tree to deal with
        new winners and new losers.
        """
        for key in tree.keys():
            if key == "n": continue
            if key == "i": continue
            if key == "bi": continue

            self.updateTree(tree[key])
            c, bamount, prior = key
            newAmount = self.eliminatedAbove[self.R][c]
            if bamount <= newAmount: continue
            if newAmount < self.minimum[c] or newAmount <= prior:
                treeToMerge = tree[key]
                del tree[key]
                self.mergeTree(treeToMerge,tree)
            else:
                newKey = (c,newAmount,prior)
                if newKey in tree:
                    tree[newKey]["n"] += tree[key]["n"]
                    treeToMerge = tree[key]
                    del tree[key]
                    self.mergeTree(treeToMerge,tree[newKey])
                else:
                    tree[newKey] = tree[key]
                    del tree[key]

###

    def mergeTree(self,treeToMerge,tree):
        """Merges two trees.  Doesn't deal with weight n at top level."""
        tree["bi"] += treeToMerge["bi"]
        tree["i"] += treeToMerge["i"]
        for key in treeToMerge.keys():
            if key == "n": continue
            if key == "i": continue
            if key == "bi": continue

            if key in tree:
                tree[key]["n"] += treeToMerge[key]["n"]
                self.mergeTree(treeToMerge[key],tree[key])
            else:
                tree[key] = treeToMerge[key]
            del treeToMerge[key]

###

    def treeCount(self, tree, remainder):
        """Called from updateCount to traverse the ballot tree.  Recursive."""
        for bi, i in itertools.izip(tree["bi"],tree["i"]):
            self.addBallotToTree(tree, bi, i)
        tree["bi"] = []
        tree["i"] = []

        # Iterate over the next candidates on the ballots
        for key in tree.keys():
            if key == "n": continue
            if key == "i": continue
            if key == "bi": continue

            c, bamount, bprior = key
            if bamount > self.eliminatedAbove[self.R][c]: bamount = self.eliminatedAbove[self.R][c]
            rrr = remainder
            if bamount >= self.minimum[c] and bamount > bprior: # not fully eliminated
                # if we haven't seen this amount before, add it to f, if we've seen a larger amount
                for amount in sorted(self.f[self.R][c].keys()):
                    if amount == bamount: break
                    if amount > bamount:
                        self.f[self.R][c][bamount] = self.f[self.R][c][amount]
                        break
                # add this amount to countDict, taking from a larger amount if needed
                if not bamount in self.countDict[self.R][c]:
                    nextamount = 0
                    prior = 0
                    for nextamount in sorted(self.countDict[self.R][c].keys()):
                        if nextamount > bamount: break
                        prior = nextamount
                    if nextamount < bamount: self.countDict[self.R][c][bamount] = 0
                    else:
                        # round up how much the new smaller amount will get
                        d,r = divmod(self.countDict[self.R][c][nextamount] * (bamount - prior),\
                                         nextamount - prior)
                        if r>0: d+=1
                        self.countDict[self.R][c][bamount] = d
                        self.countDict[self.R][c][nextamount] -= d

                # now calculate contribution at every level between bprior and bamount
                contrib = {}
                contribTot = 0
                prior = bprior
                for amount in sorted(self.countDict[self.R][c].keys()):
                    if amount <= bprior:
                        continue
                    if amount > bamount:
                        break
                    f = self.f[self.R][c].get(amount, self.supportLimit)
                    # round up the contribution
                    d, r = divmod(f * (amount - prior), self.p)
                    if r > 0: d += 1
                    contrib[amount] = d
                    contribTot += d
                    prior = amount

                # overContrib: we tried to contribute more than share (Meek) or remainder (Warren)
                # shouldContrib: multiplier to each contribution to fix.  Rounded down.
                if self.meek:
                    overContrib = contribTot > self.share
                else:
                    overContrib = contribTot > rrr
                if overContrib:
                    shouldContrib = rrr * self.p / contribTot
                prior = bprior
                for amount in sorted(contrib.keys()):
                    if overContrib:
                        # calculate maxKeep... round up
                        if amount <= self.winAmount[self.R][c]:
                            f = (shouldContrib+1) * contrib[amount] / (amount - prior) + 1
                            if f > self.p: f = self.p
                            if f > self.maxKeep[c].get(amount,0):
                                self.maxKeep[c][amount] = f
                        # calculate new contribution... round down, but see below
                        newamount = shouldContrib * contrib[amount] / self.p
                    else:
                        if amount <= self.winAmount[self.R][c]:
                            self.maxKeep[c][amount] = self.p
                        newamount = contrib[amount]
                        if self.meek:
                            # round up the Meek calculation
                            newamount, r = divmod(newamount * rrr, self.share)
                            if r > 0: newamount += 1
                    self.countDict[self.R][c][amount] += tree[key]["n"] * newamount
                    self.count[self.R][c] += tree[key]["n"] * newamount
                    rrr -= newamount
                    prior = amount
                if overContrib and rrr > 0:
                    # we rounded down new fixed contributions... but we had something left over
                    # give it to the lowest contribution level
                    amount = sorted(contrib.keys())[0]
                    self.countDict[self.R][c][amount] += tree[key]["n"] * rrr
                    self.count[self.R][c] += tree[key]["n"] * rrr
                    rrr = 0

            # If ballot not used up and more candidates, keep going
            if rrr > 0:
                self.treeCount(tree[key], rrr)

###

    def updateCandidateStatus(self):
        """Called at end of each election, to eliminate any trailing funding levels.
        Originally was: Update the status of winners who haven't reached the threshold.
        """

        desc = ""
        self.nRounds = self.R+1

        winners = []
        losers = []
        for c in self.purgatory:
            self.eliminatedAbove[self.R][c] = self.winAmount[self.R][c]
            if self.winAmount[self.R][c] > 0:
                winners.append(c)
            else:
                losers.append(c)
        desc += self.newWinners(winners, "under")
        self.newLosers(losers)

        return desc

###
