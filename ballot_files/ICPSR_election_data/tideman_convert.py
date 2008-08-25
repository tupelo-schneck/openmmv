from bltp import *

def normalize(thedict):
    items = sorted(thedict.items())
    newrank = 0
    oldrank = 0
    newdict = {}
    for (rank,val) in items:
        if rank == oldrank:
            newdict[newrank] = newdict[newrank] + val
        else:
            oldrank = rank
            newrank = newrank + 1
            newdict[newrank] = val
    return newdict

def import_tideman(e,filename,name):
    e.reset()
    e.name = name
    f = open(filename,'r')
    try:
        strs = f.readline().split()
        while strs[0] != 'ELECT':
            strs = strs[1:]
        strs = strs[1:]
        tmp = strs[0]
        if tmp[0] == '(': tmp = tmp[1:-1]
        if tmp[0] == '>': tmp = tmp[1:]
        if tmp[0:2] == '3+': tmp = str(3+int(tmp[2:]))
        e.totalResources = float(tmp)
        strs = strs[1:]
        while not strs[0].isdigit():
            strs = strs[1:]
        numprojects = int(strs[0])
        e.quota = 0.0
        e.roundToNearest = 1.0
        e.categories[0] = elections.Category(0,"None")
        i = 0
        while i < numprojects:
            i = i + 1
            e.projects[i] = elections.Project(i,chr(64+i),1.0,1.0,0)

        i = 0
        strs = f.readline().split()
        while len(strs)>1:
            strs = strs[2:]
            i = i + 1
            b = elections.Ballot(i,'',1.0)
            
            j = 0
            for s in strs:
                j = j + 1
                if s == '99':
                    continue
                if s.isdigit():
                    rank = int(s)
                    project = j
                else:
                    rank = j
                    project = ord(s) - 64
                amount = 1.0
                if b.ballotItems.has_key(rank):
                    b.ballotItems[rank].append(elections.BallotItem(project,amount))
                else:
                    b.ballotItems[rank] = [elections.BallotItem(project,amount)]
            b.ballotItems = normalize(b.ballotItems)
            e.ballots[i] = b
            strs = f.readline().split()
    finally:
        f.close()

import os
e = elections.Election()
for f in os.listdir('ICPSR_election_data/elections'):
  print f
  import_tideman(e,'ICPSR_election_data/elections/' + f,f)
  e.export_bltp('ICPSR_election_data/bltp/' + f + '.bltp')
