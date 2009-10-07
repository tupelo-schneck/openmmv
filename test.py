from projectBallots import *
from BltpBallotLoader import *
from projectElection import *
from report import TextReport
b = Ballots()
loader = BltpBallotLoader()
loader.load(b,"ballot_files/otra2009/2009-10-05unsuspend.bltp")
e = ProjectElection(b)
#e.countingMethod = "Meek"

def run():
    e.runElection()

def prin():
    r = TextReport(e)
    print r.generateReport()

def showBallot(f,cands,amts):
    rrr = e.share
    priors = [0] * (max(cands)+1)
    for (c,bamount) in itertools.izip(cands,amts):
        bamount = bamount * e.p
        prior = priors[c]
        contrib = {}
        contribTot = 0
        for amount in sorted(f[c].keys()):
            if amount <= prior:
                continue
            if amount > bamount:
                break
            thisf = f[c].get(amount)
            d, r = divmod(thisf * (amount - prior), e.p)
            if r > 0: d += 1
            contrib[amount] = d
            contribTot += d
            prior = amount

        if e.meek:
            overContrib = contribTot > e.share
        else:
            overContrib = contribTot > rrr
        if overContrib:
            shouldContrib = rrr * e.p / contribTot
        prior = priors[c]
        for amount in sorted(contrib.keys()):
            if overContrib:
                # calculate new contribution... round down, but see below
                newamount = shouldContrib * contrib[amount] / e.p
            else:
                newamount = contrib[amount]
                if e.meek:
                    # round up the Meek calculation
                    newamount, r = divmod(newamount * rrr, e.share)
                    if r > 0: newamount += 1
            print "%d(%s): %s" % (c,e.displayValue(amount),e.displayValue(newamount))
            rrr -= newamount
            prior = amount
        if overContrib and rrr > 0:
            # we rounded down new fixed contributions... but we had something left over
            # give it to the lowest contribution level
            amount = sorted(contrib.keys())[0]
            print "%d(%s): %s" % (c,e.displayValue(amount),e.displayValue(rrr))
            rrr = 0
        if prior < min(bamount,e.maximum[c]):
            print "%d(%s): 0" % (c,e.displayValue(min(bamount,e.maximum[c]))) 
        if rrr <= 0:
            break
    if rrr > 0:
        print "Exhausted: %s" % e.displayValue(rrr)

def showBallots():
    f = e.f[e.R]
    for i in xrange(e.b.numWeightedBallots):
        w, cands, amts = e.b.getWeightedProjectBallot(i)
        print "Weight: %d" % w
        print "Hours: %d" % sum(amts)
        showBallot(f,cands,amts)
        print 
