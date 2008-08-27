#!/usr/bin/env python

import os, random, time, timeit
import openstv.ballots as ballots
import openstv.STV as stv
import elections

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
                    max=float('inf'), file=None):
        self.path = path
        self.max = max
        self.file = file
        self.diff = {}
        self.times = {}
    
    @print_timing
    def runSTV(self, file):
        b = ballots.Ballots()
        b.load(file)
        e = stv.MeekSTV(b, threshName=("Hare", "Dynamic", "Fractional"))
        e.runElection()
        winS = "STV election winners: "
        for w in e.winners:
            winS += "%s " % b.names[w]
        return winS

    @print_timing
    def runMMV(self, file):
        e = elections.Election(file)
        e.run_election()
        winM = "MMV election winners: "
        for item in e.results.list:
            winM += "%s " %item[1]
        return winM

    def runRandomTests(self):
        # for each election, run with openmmv and openstv and print results
        if self.file:
            files = [self.file]
        else:
            files = os.listdir(self.path)
        random.shuffle(files)
        self.diff = {}
        self.times = {}
        cur = 0
        for file in files:
            if cur < self.max and file[-4:] == ".blt":
                print "Processing file: %s..." % file
                msg = ""
                s, sdelta =  self.runSTV(self.path + file)
                m, mdelta =  self.runMMV(self.path + file)
                msg += "======================================\n"
                msg += "Election file: %s\n" % file
                msg += "%s\n" % s
                msg += "%s\n\n" % m
                #print msg
                self.times[file] = (sdelta, mdelta)
                if s != m:
                    self.diff[file] = msg
                cur += 1
        print "Files with differing results:"
        for msg in self.diff.values():
            print msg
        print "\nTimings (in milliseconds):\nFilename\tSTV time\tMMV time\tSTV-MMV"
        print "========================================================"
        for t in self.times.keys():
            s, m = self.times[t]
            print "%s\t\t%4.3f\t\t%4.3f\t\t%4.3f" % (t, s, m, s-m)

if __name__ == "__main__":
    t = Test(max=4)
    t.runRandomTests()
