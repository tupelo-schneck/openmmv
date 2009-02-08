#!/usr/bin/env python

"""\
Module for loading and saving ballots.

Class Ballots
  Class TextBallots
  Class BltBallots
  Class CambBallots
"""

## Copyright (C) 2003-2009  Jeffrey O'Neill
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

__revision__ = "$Id: ballots.py 471 2009-01-31 19:29:20Z jco8 $"

import re
import string
import sys
import copy
import random
from warnings import warn
from array import array

##################################################################

class Ballots:
  """Class for working with ballot data.

  An instance of the Ballots class is required to provide the following
  information:

  nCand -- number of candidates
  names -- names of all candidates
  nBallots -- number of ballots
  raw -- raw (or unpacked) ballot data
  packed -- packed ballot data

  In addition, an instance may provide other information:

  nSeats -- number of seats
  title -- title of the election
  date -- date of the election
  """

  def __init__(self, fName=""):
    self.fName = ""
    self.withdrawn = []
    self.names = []
    self.nCand = 0
    self.nBallots = 0
    self.nBadBallots = 0
    self.nSeats = 1
    self.raw = []
    self.packed = []
    self.weight = []
    self.bid = []
    self.title = ""
    self.date = ""
    if fName != "":
      self.load(fName)
    
###

  @staticmethod
  def loadKnown(fName, type=""):
    if type == "txt" or (type=="" and fName[-3:] in ["txt", "TXT"]):
      return TextBallots(fName)
    elif type == "blt" or (type=="" and fName[-3:] in ["blt", "BLT"]):
      return BltBallots(fName)
    elif type == "Cambridge":
      return CambBallots(fName)
    else:
      raise RuntimeError, "Must specify the type of ballot file."

###

  @staticmethod
  def loadUnknown(fName):
    try:
      b = BltBallots(fName)
      return b
    except:
      try:
        b = TextBallots(fName)
        return b
      except:
        try:
          b = CambBallots(fName)
          return b
        except:
          raise RuntimeError, "Format of ballot file is not recognized."    
          
###

  def saveAsBlt(self, fName, packed=False):
    "Save ballots in BLT format."

    b = BltBallots()
    b.fName = fName
    b.title = self.title
    b.nCand = self.nCand
    b.nSeats = self.nSeats
    b.names = self.names
    b.packed = self.packed
    b.weight = self.weight
    b.raw = self.raw
    b.save(fName, packed)

###

  def saveAsText(self, fName, packed=False):
    "Save ballots in text format."

    b = TextBallots()
    b.fName = fName
    b.title = self.title
    b.nCand = self.nCand
    b.nSeats = self.nSeats
    b.names = self.names
    b.packed = self.packed
    b.weight = self.weight
    b.raw = self.raw
    b.save(fName, packed)

###

  def append(self, bb):
    "Append ballot data."

    if ( bb.nCand != self.nCand or
         bb.nSeats != self.nSeats or
         bb.names != self.names ):
      raise RuntimeError, "Can't append ballots.  The numbers of seats\n"\
            "and candidates and the names of the candidates must\n"\
            "be identical."
    else:
      self.raw += bb.raw
      self.nBallots = len(self.raw)
      self.pack()

###

  def display(self, packed=True):
    "Display the top 10 packed ballots."
    if packed:
      for i in range(min(10, len(self.packed))):
        print self.weight[i], self.packed[i]
    else:
      for i in range(min(10, len(self.raw))):
        print self.raw[i]

###

  def pack(self):
    "Pack the raw ballots."

    # packed ballots
    self.packed = []
    self.weight = []
    nPacked = 0
    raw2packed = {}
    for i, b in enumerate(self.raw):
      key = str(b)
      if raw2packed.has_key(key):
        index = raw2packed[key]
        self.weight[index] += 1
        self.raw[i] = self.packed[index] # save memory
      else:
        self.packed.append(b[:])
        self.weight.append(1)
        raw2packed[key] = nPacked
        self.raw[i] = self.packed[nPacked] # save memory
        nPacked += 1

###

  def shuffle(self):
    "Shuffle the raw ballots into a different order."

    random.shuffle(self.raw)

###

  def exciseCandidates(self, withdrawList=""):
    "Return a copy of the ballots without the specified candidates."

    if withdrawList == "":
      withdrawList = self.withdrawn
    if withdrawList == "":
      raise RuntimeError, "No candidates to remove from the ballots."

    # Copy basic info into new ballots
    bb = Ballots()
    bb.title = self.title
    bb.date = self.date
    bb.fName = self.fName
    bb.nSeats = self.nSeats
    bb.nBadBallots = self.nBadBallots
    bb.nCand = self.nCand - len(withdrawList)

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
        c2c[i] -= n

    # Copy the raw ballots and excise the unwanted candidates
    for i in xrange(self.nBallots):
      ballot = array("B")
      for c in self.raw[i]:
        if c not in withdrawList:
          ballot.append(c2c[c])
      if len(ballot) == 0:
        bb.nBadBallots += 1
      else:
        bb.raw.append(ballot)
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
    for c in range(self.nCand):
      cc = c2c[c]
      self.names[cc] = oldNames[c]

    # Finish up.
    self.raw = raw2
    self.pack()

##################################################################

class TextBallots(Ballots):
  "Class for ballots with a simple text format."

  def __init__(self, fName=""):
    Ballots.__init__(self, fName)

###

  def load(self, fName):
    "Load text ballot data from a file."

    self.fName = fName
    self.title = "Ballot data from %s." % self.fName
    name2index = {}

    f = open(self.fName, "r")
    x = f.readlines()
    f.close()

    count = 1
    for xx in x:
      # get optional weight
      y = re.match("\s*(\d+)\s*:", xx)
      if y == None:
        weight = 1
      else:
        weight = int(y.group(1))
        xx = xx[y.end():]

      # check ballot
      z = re.match("[\w\s]*$", xx)
      if z == None:
        raise RuntimeError, ("Bad format in text-format ballot file.\n"
                             "Candidate names must be alphanumeric and\n"
                             "separated by white space.  This line does\n"
                             "not match:\n%s" % xx)

      b = xx.split()
      if b == []: # get rid of empty ballots
        cpunt += weight
        continue

      # convert ballot from name to index
      bb = array("B")
      for c in b:
        if c not in name2index.keys():
          self.names.append(c)
          name2index[c] = self.names.index(c)
          if len(self.names) > 255:
            raise RuntimeError, "Too many candidates.  The number of"\
                  "candidates must be less than 256."
        bb.append(name2index[c])

      # append ballots corresponding to the weight
      self.raw += [bb]*weight

      # record ballot ids
      self.bid += [("Ballot %d" % i) for i in range(count, count+weight)]
      count += weight

    self.nCand = len(self.names)
    self.nBallots = len(self.raw)
    self.pack()

###

  def save(self, fName="", packed=False):
    "Save text ballots to a file."

    if fName == "" and self.fName == "":
      raise RuntimeError, "No file name given for saving ballots."
    elif fName != "":
      self.fName = fName

    for n in self.names:
      if not n.isalnum():
        raise RuntimeError, "Can't save ballots in text format.  The\n"\
              "candidates' names must be alphamumeric with no\n"\
              "white space."

    if packed:
      # sort in order of weight
      order = range(len(self.packed))
      order.sort(key=lambda a, f=self.weight: -f[a])

      f = open(self.fName, "w")
      for i in order:
        b = [self.names[c] for c in self.packed[i]]
        bb = str(self.weight[i]) + ": " + string.join(b, " ") + "\n"
        f.write(bb)
      f.close()

    else:
      f = open(self.fName, "w")
      for i in xrange(len(self.raw)):
        b = [self.names[c] for c in self.raw[i]]
        bb = string.join(b, " ") + "\n"
        f.write(bb)
      f.close()

##################################################################

class BltBallots(Ballots):
  "Class for ballots defined by ERS."

  def __init__(self, fName=""):
    self.intRE = re.compile("\s*(\d+)\s+")
    self.ballotRE = re.compile("(\d+)(.*?)\s+0\s+")
    self.stringRE = re.compile('\s*"(.*?)"\s*')
    Ballots.__init__(self, fName)

###

  def getInt(self):
    out = self.intRE.match(self.buffer, self.index)
    if out == None:
      return None
    self.index = out.end()
    return int(out.group(1))

  def getBallot(self):
    seen = [False] * self.nCand
    out = self.ballotRE.match(self.buffer, self.index)
    if out == None:
      raise RuntimeError, ("Bad format in file.  Expected a ballot but\n"
                           "file does not match:\n%s" %
                           self.buffer[self.index:self.index+80])
    self.index = out.end()
    w = int(out.group(1))
    b = out.group(2).split()
    bb = array("B")
    for c in b:
      cc = int(c) - 1
      if cc < 0 or cc > self.nCand-1:
        warn("No candidate with number %s.  Ranking skipped.\n" % c)
      elif seen[cc]:
        warn("Candidate number %s is ranked on a ballot\n"
             "more than once.  Later ranking ignored.\n" % c)
      else:
        bb.append(cc)
        seen[cc] = True
    return (w, bb)

  def getString(self):
    out = self.stringRE.match(self.buffer, self.index)
    if out == None:
      raise RuntimeError, ("Bad format in file.  Expected a string but\n"
                           "file does not match:\n%s" %
                           self.buffer[self.index:self.index+80])
    self.index = out.end()
    return out.group(1)

###

  def load(self, fName):
    "Load ERS ballot data from a file."

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
    self.nSeats = self.getInt()
    if self.nSeats == None:
      raise RuntimeError, ("Bad format in file.  Expected an integer when\n"
                           "reading the number of seats but received:%s\n"
                           % self.buffer[self.index:self.index+80])
    if self.nSeats > 254 or self.nSeats < 1:
      raise RuntimeError, "The number of seats must be between 1 and 254."

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
      (weight, b) = self.getBallot()
      # get rid of empty ballots
      if len(b) == 0:
        self.nBadBallots += weight
        count += weight
        continue
      # take care of ballot weights
      self.raw += [b]*weight
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
      self.names.append(self.getString())

    # get title
    self.title = self.getString()

    self.pack()

###

  def save(self, fName="", packed=False):
    "Save ballots in ERS format."

    if fName == "" and self.fName == "":
      raise RuntimeError, "No file name given for saving ballots."
    elif fName != "":
      self.fName = fName

    if re.search("\.dat$|\.DAT$", self.fName):
      self.fName = self.fName[:-4]
    if re.search("\.blt$|\.BLT$", self.fName) == None:
      self.fName += ".blt"

    if packed:
      # sort in order of weight
      order = range(len(self.packed))
      order.sort(key=lambda a, f=self.weight: -f[a])

      f = open(self.fName, "w")
      f.write("%d %d\n" % (self.nCand, self.nSeats))
      for i in order:
        f.write("%s" % self.weight[i])
        for c in self.packed[i]:
          f.write(" %s" % (c+1))
        f.write(" 0\n")
      f.write("0\n")
      for n in self.names:
        f.write('"%s"\n' % n)
      f.write('"%s"\n' % self.title)    
      f.close()

    else:
      f = open(self.fName, "w")
      f.write("%d %d\n" % (self.nCand, self.nSeats))
      for i in xrange(len(self.raw)):
        f.write("1")
        for c in self.raw[i]:
          f.write(" %s" % (c+1))
        f.write(" 0\n")
      f.write("0\n")
      for n in self.names:
        f.write('"%s"\n' % n)
      f.write('"%s"\n' % self.title)    
      f.close()
      
##################################################################

class CambBallots(Ballots):
  "Temporary class for ballots as used by Cambridge, MA."

  def __init__(self, fName=""):
    Ballots.__init__(self, fName)

###

  def load(self, fName):
    "Load ballot data from a file."

    self.fName = fName
    self.title = "Ballot data from %s." % self.fName
    name2index = {}

    f = open(self.fName, "r")
    x = f.readlines()
    f.close()
    x.pop(0) # remove header

    for xx in x:
      xx = xx.strip()
      y = xx.split(",")
      bid = y[0]
      b = y[2:]
      b = [re.sub("\[\d+\]", "", c) for c in y[2:]]
      if b == ['']: # get rid of empty ballots
        continue

      # convert ballot from name to index
      bb = array("B")
      for c in b:
        if c not in name2index.keys():
          self.names.append(c)
          name2index[c] = self.names.index(c)
          if len(self.names) > 255:
            raise RuntimeError, "Too many candidates.  The number of"\
                  "candidates must be less than 256."
        bb.append(name2index[c])

      # append ballots
      self.bid.append(bid)
      self.raw += [bb]

    self.nCand = len(self.names)
    self.nBallots = len(self.raw)
    self.pack()
    self.reorderCandidates()
