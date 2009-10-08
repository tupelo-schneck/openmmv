from projectBallots import *
from BltpBallotLoader import *
from projectElection import *
from report import TextReport
b = Ballots()
loader = BltpBallotLoader()
loader.load(b,"ballot_files/otra2009/2009final.bltp")
b.numSeats += 000
origmax = b.maximum[:]
for i in [42,9,29,7,26,40,43,35,27,36,38,39]:
    b.maximum[i-1] = 0
b.maximum[11-1]=250
b.maximum[18-1]=200
b.maximum[13-1]=200
b.maximum[25-1]=80
b.maximum[28-1]=60
b.maximum[32-1]=100
b.maximum[6-1]=150
b.maximum[10-1]=0
b.maximum[41-1]=20
b.maximum[33-1]=0
b.maximum[17-1]=70
b.maximum[14-1]=200
b.maximum[31-1]=0
b.maximum[21-1]=191 #*** 232
b.maximum[24-1]=70
b.maximum[12-1]=20
b.maximum[20-1]=0
b.maximum[19-1]=200
b.maximum[15-1]=60
b.maximum[23-1]=0 #***
b.maximum[16-1]=100
b.maximum[37-1]=1350 #*** 1397
for i in [14-1,16-1,21-1,37-1]:
    if b.maximum[i] > 0:
        b.maximum[i] += 0
        if b.maximum[i] > origmax[i]: b.maximum[i] = origmax[i]
e = ProjectElection(b)
#e.countingMethod = "Meek"

def run():
    e.runElection()
    e.R += 1
    e.allocateRound()
    e.updateTree(e.tree)
    e.updateKeepValues()
    e.updateCount()
    e.updateWinners()
    e.nRounds += 1

def prin():
    r = TextReport(e)
    print r.generateReport()

def showBallot(f,cands,amts):
    rrr = e.share
    accum = 0
    priors = [0] * (max(cands)+1)
    for (c,bamount) in itertools.izip(cands,amts):
        accum += bamount * e.p
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
        if prior == 0 or prior < min(bamount,e.maximum[c]):
            print "%d(%s): 0" % (c,e.displayValue(min(bamount,e.maximum[c]))) 
        if rrr <= 0:
            break
    if rrr > 0:
        print "Exhausted: %s" % e.displayValue(rrr)
    else:
        print "Spent: %s" % e.displayValue(accum)

def showBallots():
    f = e.f[e.R]
    for i in xrange(e.b.numWeightedBallots):
        w, cands, amts = e.b.getWeightedProjectBallot(i)
        print "Weight: %d" % w
        print "Hours: %d" % sum(amts)
        showBallot(f,cands,amts)
        print 
