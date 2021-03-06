from projectBallots import *
from BltpBallotLoader import *
from projectElection import *
from report import TextReport
b = Ballots()
loader = BltpBallotLoader()
loader.load(b,"ballot_files/otra2009/2009final.bltp")
b.numSeats += 0#320
origmax = b.maximum[:]
if False:
    for i in [1,2,3,4,5,7,9,26,27,29,30,35,36,38,39,40,42,43]:
        b.maximum[i-1] = 0
if False:
    b.maximum[6-1]=150
    b.maximum[8-1]=200
    b.maximum[10-1]=100
    b.maximum[11-1]=250
    b.maximum[12-1]=20
    b.maximum[13-1]=200
    b.maximum[14-1]=200
    b.maximum[16-1]=100
    b.maximum[17-1]=68
    b.maximum[18-1]=200
    b.maximum[19-1]=200
    b.maximum[21-1]=50
    b.maximum[22-1]=70
    b.maximum[25-1]=80
    b.maximum[28-1]=60
    b.maximum[32-1]=100
    b.maximum[34-1]=125
    b.maximum[37-1]=1500
if False:
    b.maximum[15-1]=0
    b.maximum[20-1]=0
    b.maximum[23-1]=0
    b.maximum[24-1]=0
    b.maximum[31-1]=0
    b.maximum[33-1]=0
    b.maximum[41-1]=0
#    b.maximum[23-1]=b.minimum[23-1]
#    b.maximum[24-1]=b.minimum[24-1]
#    b.maximum[41-1]=b.minimum[41-1]
if False:
    b.maximum[6-1] = 113
    b.minimum[6-1] = 113
if False:
    for i in range(len(b.maximum)):
        if i in  [1,2,3,4,5,7,9,26,27,29,30,35,36,38,39,40,42,43]:
            continue
        b.maximum[i-1] = b.maximum[i-1] * 11 / 10
for i in range(len(b.maximum)):
    if b.maximum[i-1] > origmax[i-1]:
        b.maximum[i-1] = origmax[i-1]
e = ProjectElection(b)
#e.countingMethod = "Meek"

def run():
    e.runElection()
    e.R += 1
    e.allocateRound()
    e.msg[e.R] += "Count after transferring surplus votes. "
    e.updateTree(e.tree)
    e.msg[e.R] += e.updateKeepValues()
    e.updateCount()
    e.msg[e.R] += e.updateWinners()
    e.nRounds += 1
    checkLosers(True)

def checkLosers(printAll):
    for c in range(e.b.numCandidates):
      if c+1 in [1,2,3,4,5,7,9,26,27,29,30,35,36,38,39,40,42,43]:
          continue
      if printAll or e.winAmount[e.R-1][c] < e.maximum[c]:
        print "%s: %s" % (e.b.names[c],e.displayValue(e.winAmount[e.R-1][c]))

def prin():
    r = TextReport(e,maxWidth=179)
    print r.generateReport()

def showBallot(f,cands,amts,R):
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
        if prior < bamount and prior < e.eliminatedAbove[R][c]:
            thisf = e.supportLimit
            amount = min(bamount,e.eliminatedAbove[R][c])
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

def showBallots(R):
    f = e.f[R]
    for i in xrange(e.b.numWeightedBallots):
        w, cands, amts = e.b.getWeightedProjectBallot(i)
        print "Weight: %d" % w
        print "Hours: %d" % sum(amts)
        showBallot(f,cands,amts,R)
        print

def showWinners():
    f = e.f[e.R]
    for c in e.winners:
        print "%s: %s hours" % (e.b.names[c], e.displayAmountValue(e.winAmount[e.R][c]))
        for amount in sorted(f[c].keys()):
            print "          %s hrs: %s players" % (e.displayAmountValue(amount),str(round(e.p*1.0/f[c][amount],1)))

#e.surplusLimit = 40000
run()
