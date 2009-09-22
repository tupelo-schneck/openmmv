#!/usr/bin/env python

import os, random, time, timeit
import ballots as ballots
import STV
from MethodPlugins.WarrenSTV import WarrenSTV
from LoaderPlugins.BltBallotLoader import BltBallotLoader
import sys
import projectBallots
import projectElection

class WarrenSTVNoDefaultWinners(WarrenSTV):
    """
    Changes electionOver to match MMV.
    """
#     def allocateRound(self):
#         print "STV Round " + str(self.R) + " " + str(time.clock())
#         stv.WarrenSTV.allocateRound(self)

    def getLosers(self, ppp = None):
        savedNumSeats = self.numSeats
        self.numSeats = len(self.winners) + 1
        losers = WarrenSTV.getLosers(self,ppp)
        self.numSeats = savedNumSeats
        return losers

    def electionOver(self):
        "Election is over when we know all the winners."

        # Already recognized enough winners
        if len(self.winners) == self.numSeats:
            return True

        # Every candidate has either won or been eliminated
        if self.purgatory == []:
            return True

        # Not done yet.
        return False



def print_timing(func):
    def wrapper(*arg):
        t1 = time.clock()
        res = func(*arg)
        t2 = time.clock()
        delta = (t2-t1)*1000.0
        #print '%s took %0.3f ms' % (func.func_name, delta)
        return res, delta
    return wrapper

class Test:
    def __init__(self, path="ballot_files/ICPSR_election_data/blt/",
                    max=float('inf'), file=None, randomize=False):
        self.path = path
        self.max = max
        self.file = file
        self.diff = {}
        self.times = {}
        self.randomize = randomize

    @print_timing
    def runSTV(self, file, b):
        e = WarrenSTVNoDefaultWinners(b)
        e.threshName=("Hare", "Static", "Fractional")
        e.runElection()
        winS = "STV election winners: "
        for w in e.winners:
            winS += "%s " % e.b.names[w]
        return winS

    @print_timing
    def runMMV2(self, file, b):
        try:
            e = projectElection.ProjectElection(b)
            e.runElection()
            winM2 = "MM2 election winners: "
            for w in e.winners:
                winM2 += "%s " % e.b.names[w]
        except:
            winM2 = "MM2 error!"
        return winM2

    def runTests(self):
        # for each election, run with openmmv and openstv and print results
        if self.file:
            files = [self.file]
        else:
            files = os.listdir(self.path)
        if self.randomize: random.shuffle(files)
        self.diff = {}
        self.times = {}
        cur = 0
        for file in files:
            if cur < self.max and file[-4:].lower() == ".blt":
                print "Processing file: %s..." % file
                msg = ""
                b = ballots.Ballots()
                loader = BltBallotLoader()
                loader.load(b,self.path+file)
                s, sdelta =  self.runSTV(self.path + file,b)
                m2, m2delta = self.runMMV2(self.path + file,b)
                msg += "======================================\n"
                msg += "Election file: %s\n" % file
                msg += "%s\n" % s
                msg += "%s\n\n" % m2
                #print msg
                self.times[file] = (sdelta, m2delta)
                if s[3:] != m2[3:]:
                    self.diff[file] = msg
                cur += 1
        print "Files with differing results:"
        for _, msg in sorted(self.diff.items()):
            print msg
        print "\nTimings (in milliseconds):\nFilename\tSTV time\tMMV time"
        print "========================================================"
        for t in sorted(self.times.keys()):
            s, m2 = self.times[t]
            print "%s\t\t%4.3f\t\t%4.3f" % (t, s, m2)

if __name__ == "__main__":
    t = Test(max=float('inf'),randomize=False)
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if path[-4:].lower() != ".blt":
            t.path = path
        else:
            t.path = ''
            t.file = path
    t.runTests()
