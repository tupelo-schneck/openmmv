#!/usr/bin/env python
# TODO: re-think use of zip

"""\
Module for loading and saving project ballots.

Class ProjectBallots
"""

from ballots import *
import random
import re
from array import array

class ProjectBallots(BltBallots):
  """Class for working with project ballot data.

    nProj/nCand -- number of projects/candidates (int)
    names -- names of all projects/candidates (string list)
    nBallots -- number of ballots(int)
    raw -- raw (or unpacked) ballot data (int list list)
    packed -- packed ballot data (int list list)
    weight -- weight of each ballot in packed (int list)

    In raw and packed candidates are indexed 0 to nCand - 1

    fName -- filename (string)
    nResources/nSeats -- number of seats (int)
    title -- title of the election (string)
    date -- date of the election (?)

    nBadBallots -- number of empty ballots (int list)
    withdrawn -- withdrawn candidates (int list)
    bid -- list of ballot ids (string list)

    rawAmounts -- proposed funding (int list)
    packedAmounts -- proposed funding (int list)
    supportObligation -- also 'quota', percentage of ballots required to support a project (int)
    minimum -- minimum amounts for each project (int list)
    maximum -- maximum amounts for each project (int list)
    """

    # change names of nCand and nSeats to nProj and nResources
  def __getattr__(self,name):
        if name == 'nProj':
            return self.nCand
        if name == 'nResources':
            return self.nSeats
        raise AttributeError, name

    # change names of nCand and nSeats to nProj and nResources
  def __setattr__(self,name,value):
        if name == 'nProj':
            self.nCand = value
        elif name == 'nResources':
            self.nSeats = value
        elif hasattr(BltBallots,"__setattr__"):
            BltBallots.__setattr__(self,name,value)
        else:
            self.__dict__[name] = value

  def __init__(self, fName=""):
        BltBallots.__init__(self,fName=fName)
        self.rawAmounts = []
        self.packedAmounts = []
        self.supportObligation = None
        self.minimum = []
        self.maximum = []
        self.intParenRE = re.compile("\s*(\d+)(\(\d+\)|)\s*")
        self.stringParenRE = re.compile('\s*"(.*?)"(\((\d+)(,(\d+)|)\)|)\s*')

###

  def append(self,bb):
        "Append ballot data."
        
        if ( bb.nCand != self.nCand or
             bb.nSeats != self.nSeats or
             bb.names != self.names or
             bb.supportObligation != self.supportObligation or
             bb.minimum != self.minimum or
             bb.maximum != self.maximum):
            raise RuntimeError, "Can't append ballots.  The numbers of seats\n"\
                  "and candidates and the names of the candidates must\n"\
                  "be identical."
        else:
            self.raw += bb.raw
            self.nBallots = len(self.raw)
            self.rawAmounts += bb.rawAmounts
            self.nBadBallots += bb.nBadBallots
            self.withdrawn += bb.withdrawn
            self.pack()

###

    # display: boring

###
    
  def pack(self):
        "Pack the raw ballots."
        
        # packed ballots
        self.packed = []
        self.weight = []
        self.packedAmounts = []
        nPacked = 0
        raw2packed = {}
        for i, (b,a) in enumerate(zip(self.raw,self.rawAmounts)):
            key = str((b,a))
            if raw2packed.has_key(key):
                index = raw2packed[key]
                self.weight[index] += 1
                self.raw[i] = self.packed[index] # save memory
                self.rawAmounts[i] = self.packedAmounts[index]
            else:
                self.packed.append(b[:])
                self.packedAmounts.append(a[:])
                self.weight.append(1)
                raw2packed[key] = nPacked
                self.raw[i] = self.packed[nPacked] # save memory
                self.rawAmounts[i] = self.packedAmounts[nPacked]
                nPacked += 1
###

  def shuffle(self):
      "Shuffle the raw ballots into a different order."

      random.shuffle(self.raw)
      random.shuffle(self.rawAmounts)

###

  def exciseCandidates(self, withdrawList=""):
    "Return a copy of the ballots without the specified candidates."

    if withdrawList == "":
      withdrawList = self.withdrawn
    if withdrawList == "":
      raise RuntimeError, "No candidates to remove from the ballots."

    # Copy basic info into new ballots
    bb = ProjectBallots()
    bb.title = self.title
    bb.date = self.date
    bb.fName = self.fName
    bb.nSeats = self.nSeats
    bb.nBadBallots = self.nBadBallots
    bb.nCand = self.nCand - len(withdrawList)
    bb.supportObligation = self.supportObligation

    # Set up a translation list for candidate numbers and copy
    # candidate names
    c2c = range(self.nCand)
    n = 0
    for i in range(self.nCand):
      if i in withdrawList:
        c2c[i] = None
        n += 1
      else:
        bb.names.append(self.names[i])
        bb.minimum.append(self.minimum[i])
        bb.maximum.append(self.maximum[i])
        c2c[i] -= n

    # Copy the raw ballots and excise the unwanted candidates
    for i in xrange(self.nBallots):
      ballot = array("B")
      ballotAmounts = array("l")
      for c, a in zip(self.raw[i],self.rawAmounts[i]):
        if c not in withdrawList:
          ballot.append(c2c[c])
          ballotAmounts.append(a)
      if len(ballot) == 0:
        bb.nBadBallots += 1
      else:
        bb.raw.append(ballot)
        bb.rawAmounts.append(ballotAmounts)
        bb.bid.append(self.bid[i])

    # Finish up
    bb.nBallots = len(bb.raw)
    bb.pack()
    assert(bb.nBallots + bb.nBadBallots == self.nBallots + self.nBadBallots)
    
    return bb

###

  def reorderCandidates(self, order=[]):
    "Reorder candidates in alphabetical order or the order specified."

    if order == []:
      order = range(self.nCand)
      order.sort(key=lambda c, f=self.names: f[c])
    foo = order[:]
    foo.sort()
    if foo != range(self.nCand):
      raise RuntimeError, "Must specify all the candidates when reordering."

    # Set up a translation list.
    # order gives the desired candidate order, e.g., [4 0 3 1 2]
    # Thus, we want 4->0, 0->1, 3->2, 1->3, and 2-> 4
    # c2c does this translation
    c2c = [0] * self.nCand
    for i, c in enumerate(order):
      c2c[c] = i

    # Copy the raw ballots with the new candidate indices.
    raw2 = []
    for i in xrange(self.nBallots):
      ballot = array("B")
      for c in self.raw[i]:
        ballot.append(c2c[c])
      raw2.append(ballot)

    # Put the names in the right order
    oldNames = self.names[:]
    oldMin = self.minimum[:]
    oldMax = self.maximum[:]
    for c in range(self.nCand):
      cc = c2c[c]
      self.names[cc] = oldNames[c]
      self.minimum[cc] = oldMin[c]
      self.maximum[cc] = oldMax[c]
      
    # Finish up.
    self.raw = raw2
    self.pack()

###

  def getBallot(self):
#    seen = [False] * self.nCand
    out = self.ballotRE.match(self.buffer, self.index)
    if out == None:
      raise RuntimeError, ("Bad format in file.  Expected a ballot but\n"
                           "file does not match:\n%s" %
                           self.buffer[self.index:self.index+80])
    self.index = out.end()
    w = int(out.group(1))
    b = out.group(2).split()
    bb = array("B")
    ba = array("l")
    for c in b:
      out = self.intParenRE.match(c)
      if out == None or out.end()<len(c):
          raise RuntimeError, ("Bad format in file.  Expected a ballot but\n"
                           "file does not match:\n%s" %
                           self.buffer[self.index:self.index+80])
      cc = int(out.group(1)) - 1
      amt = -1
      if out.group(2)!=None and out.group(2)!="":
          amt = int(out.group(2)[1:-1])
      cc = int(c) - 1
      if cc < 0 or cc > self.nCand-1:
        warn("No candidate with number %s.  Ranking skipped.\n" % c)
#      elif seen[cc]:
#        warn("Candidate number %s is ranked on a ballot\n"
#             "more than once.  Later ranking ignored.\n" % c)
      else:
        bb.append(cc)
        ba.append(amt)
#        seen[cc] = True
    return (w, bb, ba)

###

  def load(self, fName):
    "Load BLTP ballot data from a file."

    self.index = 0
    self.fName = fName
    f = open(self.fName, "r")
    self.buffer = f.read()
    f.close()

    # get nCand and nSeats
    self.nCand = self.getInt()
    if self.nCand == None:
      raise RuntimeError, ("Bad format in file.  Expected an integer when\n"
                           "reading the number of candidates but received:%s\n"
                           % self.buffer[self.index:self.index+80])
    if self.nCand > 255 or self.nCand < 2:
      raise RuntimeError, "The number of candidates must be between 2 and 255."
    out = self.intParenRE.match(self.buffer,self.index)
    if out == None:
      raise RuntimeError, ("Bad format in file.  Expected an integer when\n"
                           "reading the number of seats but received:%s\n"
                           % self.buffer[self.index:self.index+80])
    else:
        self.index = out.end()
        self.nSeats = int(out.group(1))
        if out.group(2)==None or out.group(2)=="":
            self.supportObligation = None
        else:
            self.supportObligation = int(out.group(2)[1:-1])
    if self.nSeats < 1:
      raise RuntimeError, "The amount of resources must be greater than 0."

    # get withdrawn candidates
    while self.buffer[self.index] == "-":
      self.index += 1
      c = self.getInt()
      if self.nCand == None:
        raise RuntimeError, ("Bad format in file.  Expected an integer when\n"
                             "reading withdrawn candidate but received:%s\n"
                             % self.buffer[self.index-1:self.index+80])
      self.withdrawn.append(c-1)

    # get ballots
    count = 1
    while self.buffer[self.index] != "0":
      (weight, b, bamts) = self.getBallot()
      # get rid of empty ballots
      if len(b) == 0:
        self.nBadBallots += weight
        count += weight
        continue
      # take care of ballot weights
      self.raw += [b]*weight
      self.rawAmounts += [bamts]*weight
      # record ballot ids
      self.bid += [("Ballot %d" % i) for i in range(count, count+weight)]
      count += weight

    self.nBallots = len(self.raw)

    # get end of ballot marker
    self.getInt()
    if self.nCand == None:
      raise RuntimeError, ("Bad format in file.  Expected the end of ballots\n"
                           "marker but received:%s\n"
                           % self.buffer[self.index:self.index+80])
    
    # get candidate names and election title
    for i in range(self.nCand):
      out = self.stringParenRE.match(self.buffer, self.index)
      if out == None:
          raise RuntimeError, ("Bad format in file.  Expected a string but\n"
                           "file does not match:\n%s" %
                           self.buffer[self.index:self.index+80])
      self.index = out.end()
      self.names.append(out.group(1))
      if out.group(3) == None or out.group(3) == "":
          self.minimum.append(1)
          self.maximum.append(1)
      else:
          theMin = int(out.group(3))
          self.minimum.append(theMin)
          if out.group(5) == None or out.group(5) == "":
              self.maximum.append(theMin)
          else:
              self.maximum.append(int(out.group(5)))

    # deal with ballot items without marked amounts
    for b, bamts in zip(self.raw,self.rawAmounts):
        for i, (p, amt) in enumerate(zip(b,bamts)):
            if amt<0:
                bamts[i] = self.maximum[p]

    # get title
    self.title = self.getString()

    self.pack()

###

  def save(self, fName="", packed=False):
    "Save ballots in BLTP format."

    if fName == "" and self.fName == "":
      raise RuntimeError, "No file name given for saving ballots."
    elif fName != "":
      self.fName = fName

#    if re.search("\.dat$|\.DAT$", self.fName):
#      self.fName = self.fName[:-4]
    if re.search("\.bltp?$|\.BLTP?$", self.fName) == None:
      self.fName += ".bltp"

    if packed:
      # sort in order of weight
      order = range(len(self.packed))
      order.sort(key=lambda a, f=self.weight: -f[a])

      f = open(self.fName, "w")
      f.write("%d %d" % (self.nCand, self.nSeats))
      if self.supportObligation == None or self.supportObligation == 0:
          f.write("\n")
      else:
          f.write("(%d)\n" % (self.supportObligation))
      for i in order:
        f.write("%s" % self.weight[i])
        for c,a in zip(self.packed[i],self.packedAmounts[i]):
          f.write(" %s" % (c+1))
          if a!=self.maximum[c]:
              f.write("(%d)" % a)
        f.write(" 0\n")
      f.write("0\n")
      for n,theMin,theMax in zip(self.names,self.minimum,self.maximum):
        f.write('"%s"' % n)
        if theMin!=1 or theMax!=theMin:
            f.write("(%d" % theMin)
            if theMax!=theMin:
                f.write(",%d)" % theMax)
            else:
                f.write(")")
        f.write("\n")
      f.write('"%s"\n' % self.title)    
      f.close()

    else:
      f = open(self.fName, "w")
      f.write("%d %d" % (self.nCand, self.nSeats))
      if self.supportObligation == None or self.supportObligation == 0:
          f.write("\n")
      else:
          f.write("(%d)\n" % (self.supportObligation))
      for i in xrange(len(self.raw)):
        f.write("1")
        for c,a in zip(self.raw[i],self.rawAmounts[i]):
          f.write(" %s" % (c+1))
          if a!=self.maximum[c]:
              f.write("(%d)" % a)
        f.write(" 0\n")
      f.write("0\n")
      for n,theMin,theMax in zip(self.names,self.minimum,self.maximum):
        f.write('"%s"' % n)
        if theMin!=1 or theMax!=theMin:
            f.write("(%d" % theMin)
            if theMax!=theMin:
                f.write(",%d)" % theMax)
            else:
                f.write(")")
        f.write("\n")
      f.write('"%s"\n' % self.title)    
      f.close()
      
