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
        self.fractionHad = []
        self.eliminableResources = []
        self.countDict = []
        self.maxKeep = []
        losers = []
        for c in self.purgatory:
            if self.maximum[c] == 0:
                losers.append(c)
        self.newLosers(losers)

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
        self.maxKeep.append([0] * self.b.numCandidates)
        for c in xrange(self.b.numCandidates):
            self.countDict[self.R][c] = {}
            self.f[self.R][c] = {}
            self.maxKeep[self.R][c] = {}
        # winAmount : round -> candidate -> what amount has already won
        # eliminatedAbove : round -> candidate -> highest amount not eliminated
        if self.R == 0:
            self.winAmount = [[0] * self.b.numCandidates]
            self.eliminatedAbove = [[self.maximum[p] for p in xrange(self.b.numCandidates)]]
        else:
            self.winAmount.append(self.winAmount[self.R-1][:])
            self.eliminatedAbove.append(self.eliminatedAbove[self.R-1][:])
        # fractionHad : round -> candidate -> what fraction the candidate has of
        #     the resources needed to take it to its not-yet-eliminated
        # eliminableResources : round -> candidate -> how much would be obtained
        #     by completely eliminating the candidate
        self.fractionHad.append([0] * self.b.numCandidates)
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

        self.treeCount(self.tree, self.share)

        for c in self.winners + self.purgatory:
            prior = 0
            for amt in sorted(self.countDict[self.R][c].keys()):
                if amt > self.winAmount[self.R][c]:
                    continue
                if self.countDict[self.R][c][amt] + 100 < amt - prior:
                    print "WARNING: self.countDict[%d][%d][%d] too low for winner" % (self.R, c, amt)
                prior = amt

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
        MMV adds winAmount, eliminatedAbove, and eliminableResources.
        """
        winners = []
        winnersAmounts = {}
        desc = ""
        for c in self.purgatory:
            prior = 0
            for amount in sorted(self.countDict[self.R][c].keys()):
                if amount <= self.eliminatedAbove[self.R][c]:
                    if amount > self.winAmount[self.R][c]:
                        if self.countDict[self.R][c][amount] >= amount - prior:
                            self.winAmount[self.R][c] = amount
                            print "New winner: %d %d %d" % (self.R, c, amount)
                            winnersAmounts[c] = amount
                        else:
                            self.eliminableResources[self.R][c] += self.countDict[self.R][c][amount]
                else:
                    break
                prior = amount

            if self.winAmount[self.R][c] == self.eliminatedAbove[self.R][c]:
                winners.append(c)
            else:
                self.fractionHad[self.R][c] = self.eliminableResources[self.R][c] * self.p / (self.eliminatedAbove[self.R][c] - self.winAmount[self.R][c])
#                print "%s: %s: %s/(%s-%s)=%s" % (self.R,self.b.names[c],self.displayValue(self.eliminableResources[self.R][c]),self.displayValue(self.eliminatedAbove[self.R][c]),self.displayValue(self.winAmount[self.R][c]),self.displayValue(self.fractionHad[self.R][c]))


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
        MMV also sets fractionHadOfLeastNonLoser, in order to determine
        correct funding level at which to eliminate greatest loser.
        In MMV we eliminate first the projects which need the most resources;
        unlike OpenSTV this isn't the same as projects with the least count.
        Multiple exclusion is tricky with projects of differing amounts---care is required.
        """
        if ppp == None: ppp = self.purgatory
        R = self.R - 1
        ppp.sort(key=lambda a: self.fractionHad[R][a])
        losers = []

        self.eliminableResourcesOfLosers = 0
        for i in xrange(len(ppp)):
            if len(ppp) > i+1:
                self.fractionHadOfLeastNonLoser = self.fractionHad[R][ppp[i+1]]
            else:
                self.fractionHadOfLeastNonLoser = self.p # TODO: make this some epsilon---in case we're willing to elect "close enough" projects
            self.eliminableResourcesOfLosers += self.eliminableResources[R][ppp[i]]
            # For everything so far, if you gave all eliminable resources from all the others,
            # and all of the surplus, would it still want more than the next project?
            # If so you can eliminate all of them.
            theyLose = True
            for c in ppp[:i+1]:
                if (self.eliminableResourcesOfLosers + self.surplus[R]) * self.p / (self.eliminatedAbove[R][c] - self.winAmount[R][c]) >= self.fractionHadOfLeastNonLoser:
                    theyLose = False
                    break
            if theyLose:
                return ppp[:i+1]

        return []

###

    def breakWeakTie(self, R, cList, mostfewest, what=""):
        """If there are no sure losers, we'll need to pick somebody.
        We do this by looking at prior rounds to see which one was doing worse recently,
        if any.  If that doesn't work we call breakStrongTie and choose randomly.
        In order to reuse the OpenSTV code which looks at self.count, we maneuver
        self.fractionHad into self.count and look for the biggest.
        """
        savedcount = self.count
        self.count = self.fractionHad
        res = RecursiveSTV.breakWeakTie(self,R,cList,mostfewest,what)
        self.count = savedcount
        # This is important, as res isn't a sure loser, so we should just eliminate
        # a little bit.
        self.fractionHadOfLeastNonLoser = None
        return res

###

    def eliminateLosers(self, losers):
        """Perform an elimination.
        We have to work a lot harder than OpenSTV in order to figure out and set the
        eliminated funding levels.  The key is fractionHadOfLeastNonLoser.
        """
        R = self.R-1
        extraDesc = ""
        if self.fractionHadOfLeastNonLoser == None:
            # We chose a loser, who wasn't a sure loser.  Just eliminate a little.
            assert(len(losers)==1)
            amounts = [self.eliminatedAbove[R][losers[0]] - self.amountEpsilon]
            if amounts[0] < self.minimum[losers[0]]:
                amounts = [0]
        else:
            # All in losers are sure losers; should eliminate just enough
            # that none can want more than fractionHadOfLeastNonLoser
            amounts = []
            for l in losers:
                amount = (self.eliminableResourcesOfLosers + self.surplus[R]) * self.p / self.fractionHadOfLeastNonLoser + self.winAmount[R][l]
                amount = (amount / self.amountEpsilon) * self.amountEpsilon
                if amount < self.minimum[l] or amount <= self.winAmount[R][l]:
                    amount = self.winAmount[R][l]
                amounts.append(amount)

        totalLosers = []
        winners = []
        for c, amount in itertools.izip(losers,amounts):
            self.eliminatedAbove[self.R][c] = amount
            if self.R > 10000: print "Eliminated %d %d %d" % (self.R, c, amount)
            if self.winAmount[self.R][c] == self.eliminatedAbove[self.R][c]:
                if self.winAmount[self.R][c] == 0:
                    totalLosers.append(c)
                else:
                    winners.append(c)

        self.newWinners(winners)
        self.newLosers(totalLosers)
        desc = "Count after eliminating %s and transferring votes. "\
            % self.b.joinList(["%s(>%s)" % (self.b.names[c],\
                                                 self.displayAmountValue(self.eliminatedAbove[self.R][c]))\
                                    for c in losers], convert="none")
#        print desc
        return desc

###

    def copyKeepValues(self):
        """Called after an elimination."""
        for c in self.purgatory + self.winners:
            self.f[self.R][c] = self.f[self.R-1][c].copy()
            # only keys for winners, so no need to look at eliminateds

###

    def updateKeepValues(self):
        """Called in a non-eliminating round."""

        desc = "Keep values of candidates who have exceeded the threshold: "
        list = []

        for c in sorted(self.purgatory + self.winners):
            prior = 0
            for amount in sorted(self.countDict[self.R-1][c].keys()):
                if amount > self.winAmount[self.R-1][c]:
                    break
                oldf = self.f[self.R-1][c].get(amount,self.supportLimit)
                if oldf > self.maxKeep[self.R-1][c].get(amount,self.p):
                    oldf = self.maxKeep[self.R-1][c][amount]
                # round up calculation of new f
                f, r = divmod(oldf * (amount - prior),
                      self.countDict[self.R-1][c][amount])
                if r > 0: f += 1
                self.f[self.R][c][amount] = f
                if self.f[self.R][c][amount] > oldf+10:
                    print "WARNING: f[%d][%d][%d] increased" % (self.R, c, amount)
                prior = amount
                list.append("%s(%s), %s" % (self.b.names[c], self.displayAmountValue(amount),
                                  self.displayValue(f)))

        if list != []:
            desc += self.b.joinList(list, convert="none") + ". "
        else:
#            desc += "None (shouldn't happen?) "
            desc = ""
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
            if c in self.purgatory + self.winners and prior[c] < self.eliminatedAbove[self.R][c] and bamount > 0:
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
                keys = self.countDict[self.R][c].keys()
                for k in self.f[self.R][c].keys():
                    if k not in keys: keys.append(k)
                for amount in sorted(keys):
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

                # calculate maxKeep
                # just an optimization (sometimes important, e.g. for running normal candidate elections)
                # but it only works if every funding level is a winner!
                # TODO: we could probably still do *something* when there are higher levels...
                # we just need to account for them.  Basically they cause us to reduce yet further, due
                # to the overContrib effect.  So we need to plan that into our number...
                if self.eliminatedAbove[self.R][c] == self.winAmount[self.R][c]:
                    if not bamount in self.maxKeep[self.R][c]:
                        for maxKeepKey in sorted(self.maxKeep[self.R][c].keys()):
                            if maxKeepKey > bamount:
                                self.maxKeep[self.R][c][bamount] = self.maxKeep[self.R][c][maxKeepKey]
                    prior = bprior
                    for amount in sorted(contrib.keys()):
                        if overContrib:
                            # contrib[amount] = f * (amount - prior) / self.p
                            # so correct_f = correct_contrib * self.p / (amount - prior)
                            thisMaxKeep = (shouldContrib + 1) * contrib[amount] / (amount - prior) + 1
                            prevMaxKeep = self.maxKeep[self.R][c].get(amount,0)
                            if thisMaxKeep > prevMaxKeep:
                                self.maxKeep[self.R][c][amount] = thisMaxKeep
                        else:
                            self.maxKeep[self.R][c][amount] = self.p
                        prior = amount

                prior = bprior
                for amount in sorted(contrib.keys()):
                    if overContrib:
                        # calculate new contribution... round down, but see below
                        newamount = shouldContrib * contrib[amount] / self.p
                    else:
                        newamount = contrib[amount]
                        if self.meek:
                            # round up the Meek calculation
                            newamount, r = divmod(newamount * rrr, self.share)
                            if r > 0: newamount += 1
                    self.countDict[self.R][c][amount] = self.countDict[self.R][c].get(amount,0) + tree[key]["n"] * newamount
                    self.count[self.R][c] += tree[key]["n"] * newamount
                    rrr -= newamount
                    prior = amount
                if overContrib and rrr > 0:
                    # we rounded down new fixed contributions... but we had something left over
                    # give it to the lowest contribution level
                    amount = sorted(contrib.keys())[0]
                    self.countDict[self.R][c][amount]  = self.countDict[self.R][c].get(amount,0) + tree[key]["n"] * rrr
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
  # need to remove asserion
    def newWinners(self, winners, status="over"):
        "Perform basic accounting when a new winner is found."
        
        if len(winners) == 0: return ""
    
        winners.sort()
        for c in winners:
            #      assert(self.count[self.R][c] > 0)
            self.purgatory.remove(c)
            self.winnersOver.append(c)
            self.wonAtRound[c] = self.R
            self.winners = self.winnersOver + self.winnersEven
    
        if len(winners) == 1 and status == "over":
            desc = "Candidate %s has reached the threshold and is elected. "\
                % self.b.joinList(winners)
        elif len(winners) == 1 and status == "under":
            desc = "Candidate %s is elected. " % self.b.joinList(winners)
        elif status == "over":
            desc = "Candidates %s have reached the threshold and are elected. "\
                % self.b.joinList(winners)
        elif status == "under":
            desc = "Candidates %s are elected. " % self.b.joinList(winners)
        elif status == "none":
            desc = ""
            
        return desc

    ### MMV needs to check being equal to two round before
    def chooseCandidatesToEliminate(self):
        "Eliminate any losing candidates."

        desc = ""

        losers = self.getLosers()
        if self.surplus[self.R-1] < self.surplusLimit and losers == []:
          (c, desc) = self.breakWeakTie(self.R-1, self.purgatory, "fewest",
                                        "candidates to eliminate")
          losers = [c]

        # Special case to prevent infinite loops caused by fixed precision
        if (losers == [] and
            self.R > 1 and
            ((self.count[self.R-1] == self.count[self.R-2] and
              self.f[self.R-1] == self.f[self.R-2]) or
             (self.count[self.R-1] == self.count[self.R-3] and
              self.f[self.R-1] == self.f[self.R-3]))):
          desc = "Candidates tied within precision of computations. "
          (c, desc2) = self.breakWeakTie(self.R-1, self.purgatory, "fewest",
                                         "candidates to eliminate")
          losers = [c]
          desc += desc2

        return losers, desc
