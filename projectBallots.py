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

def upgradeBallot(b):
  b.__class__ = ProjectBallots
  b.supportObligation = None
  b.minimum = [1] * b.numCandidates
  b.maximum = [1] * b.numCandidates
  amtss = []
  for cands in b._b:
    amtss.append([1] * len(cands))
  b._a = amtss

class ProjectBallots(Ballots):
  """Class for working with project ballot data.

    numCandidates
    numSeats
    withdrawn
    names[]
    date
    title

    numBallots
    numWeightedBallots
    getWeightedProjectBallot(i)
    getWeight(i)
    setWeightedProjectBallot(i,w,cands,amts)
    appendProjectBallot(weight,cands,amts)
    
    supportObligation -- also 'quota', percentage of ballots required to support a project (int)
    minimum -- minimum amounts for each project (int list)
    maximum -- maximum amounts for each project (int list)

    copy()
    cleanBallots(...)
    unpack()
    pack()
    joinList([])
    getTopChoiceFromWeightedBallot(i,[])
    """

  def __init__(self):
        Ballots.__init__(self)
        self.projectSpecificInit()

  def projectSpecificInit(self):
        self.supportObligation = None
        self.minimum = []
        self.maximum = []
        self._a = []

  ###

  def copy(self):
    ballotList = ProjectBallots()
    ballotList.title = self.title
    ballotList.date = self.date
    ballotList.numSeats = self.numSeats
    ballotList.supportObligation = self.supportObligation
    ballotList.names = self.names[:]
    ballotList.minimum = self.minimum[:]
    ballotList.maximum = self.maximum[:]
    ballotList.withdrawn = self.withdrawn[:]
    for i in xrange(self.numWeightedBallots):
      weight, cands, amts = self.getWeightedProjectBallot(i)
      ballotList.appendProjectBallot(weight, cands, amts)
    # Don't want the copy to save to the same file as the original
    ballotList.loader = None

    return ballotList
  
  ###

  def setNumCandidates(self, numCandidates):
    assert(self.names == [])
    for i in range(numCandidates):
      self.names.append("Candidate No. %d" % (i+1))
      self.minimum.append(1)
      self.maximum.append(1)

  numCandidates = property(Ballots.getNumCandidates, setNumCandidates)

  ###

  def newWeightedProjectBallot(self, weight, cands, amts):

    # Store candidate numbers as efficiently as possible to save memory
    # and speed up execution time.

    # Perform error checking
    if weight != int(weight) or int(weight) <= 0:
      raise RuntimeError, "Ballot weight must be a positive integer."
    assert(self.numCandidates < 65535)
    for c in cands:
      if c < 0 or c > self.numCandidates - 1:
        raise RuntimeError, ("No candidate with number %d." % c)
    largest = 0
    for i in xrange(len(amts)):
      if amts[i] is None:
        largest = None
        break
      if amts[i] > largest: largest = amts[i]

    if largest is None:
      amtsarr = amts
    elif largest < 255:
      amtsarr = array("B",amts)
    elif largest < 65535:
      amtsarr = array("H",amts)
    else:
      amtsarr = array("i",amts)
    
    if self.numCandidates < 255:
      return int(weight), array("B", cands), amtsarr # Bytes
    else:
      return int(weight), array("H", cands), amtsarr # Shorts (two-bytes)

  ###

  def appendProjectBallot(self, weight, ballot, amts):
    "Append a project ballot to this Ballots object."
    weight, ballot, amts = self.newWeightedProjectBallot(weight, ballot, amts)
    self._w.append(weight)
    self._b.append(ballot)
    self._a.append(amts)

  ###

  def appendBallot(self, weight, ballot):
    "Append a ballot to this Ballots object."
    weight, ballot = self.newWeightedBallot(weight, ballot)
    self._w.append(weight)
    self._b.append(ballot)
    amts = []
    for i in xrange(len(ballot)):
      amts.append(self.maximum[ballot[i]])
    self._a.append(amts)

  ###

#  def getWeight(self, i):

  ###

  def getWeightedProjectBallot(self, i):
    return self._w[i], self._b[i], self._a[i]

  ###

  def setWeightedProjectBallot(self, i, weight, ballot,amts):
    weight, ballot, amts = self.newWeightedProjectBallot(weight, ballot, amts)
    self._w[i] = weight
    self._b[i] = ballot
    self._a[i] = amts

  ###
    
  def setWeightedBallot(self, i, weight, ballot):
    weight, ballot, amts = self.newWeightedBallot(weight, ballot)
    self._w[i] = weight
    self._b[i] = ballot
    amts = []
    for i in xrange(len(ballot)):
      amts.append(self.maximum[ballot[i]])
    self._a[i] = amts

  ###

  def getWeightedProjectBallots(self):
    "Get a list of tuples with the weights and ballots and amounts."    
    return zip(self._w, self._b, self._a) 

  ###

  def deleteWeightedBallot(self, i):
    self._w.pop(i)
    self._b.pop(i)
    self._a.pop(i)

  ###

  def deleteBallots(self):
    self._w = []
    self._b = []
    self._a = []

  ###

  def getTopChoiceFromWeightedProjectBallot(self, i, choices=None):
    """Return the top choice on a ballot among candidates still in the running.
    Return candidate, amount."""

    if choices is None:
      choices = range(self.numCandidates)
    for c,a in zip(self._b[i],self._a[i]):
      if c in choices:
        return c,a
    return None

  ###

  def pack(self):
    "Pack the ballots."

    numBallots = self.numBallots # Remember this for error checking

    # Determine unique ballots and number of each
    uniqueBallots = {}
    for i in xrange(self.numWeightedBallots):
      w, b, a = self.getWeightedProjectBallot(i)
      key = str((b,a))
      if uniqueBallots.has_key(key):
        uniqueBallots[key][0] += w
      else:
        uniqueBallots[key] = [w, b, a]

    # Create the packed ballots
    self.deleteBallots()
    keys = uniqueBallots.keys()
    keys.sort(key=lambda x: uniqueBallots[x][0], reverse=True)
    for key in keys:
      self.appendProjectBallot(uniqueBallots[key][0], uniqueBallots[key][1], uniqueBallots[key][2])

    assert(self.numBallots == numBallots)

  ###

  def unpack(self):

    numBallots = self.numBallots # Remember this for error checking

    oldWeightedBallots = self.getWeightedProjectBallots()
    self.deleteBallots()
    
    for w, b, a in oldWeightedBallots:
      for i in xrange(w):
        self.appendBallot(1, b[:], a[:])

    assert(self.numBallots == numBallots)

  ###

  def cleanBallots(self, withdrawn=[], removeEmpty=False, removeDupes=False):
    "Remove withdrawn candidates and empty ballots."

    # Set up a translation list for candidate numbers for removing
    # withdrawn candidates
    c2c = range(self.numCandidates)
    n = 0
    for i in range(self.numCandidates):
      if i in withdrawn:
        c2c[i] = None
        n += 1
      else:
        c2c[i] -= n

    # Loop over ballots and perform requested cleaning
    oldWeightedBallots = self.getWeightedProjectBallots()
    self.deleteBallots()
    for w, b, a in oldWeightedBallots:
      b2 = [] # This will be a cleaned version of b
      a2 = []
      for c,a in zip(b,a):
        c2 = c2c[c] # Candidate number after removing withdrawn candidates
        # Candidate may have to pass two tests to get in the cleaned ballots.
        # First, candidate must not be withdrawn.
        # Second, candidate must not already be on the ballot when removeDupes
        # is true.
        if not ( (c in withdrawn) or (False and removeDupes and c2 in b2) ):
          b2.append(c2)
          a2.append(a)
      if not removeEmpty or len(b2) > 0:
        self.appendProjectBallot(w, b2, a2)

    # Remove the withdrawn candidates names
    self.names = [self.names[c] for c in range(self.numCandidates)
                  if c not in withdrawn]
    self.minimum = [self.minimum[c] for c in range(self.numCandidates)
                  if c not in withdrawn]
    self.maximum = [self.maximum[c] for c in range(self.numCandidates)
                  if c not in withdrawn]

  ###

  def appendFile(self, fName):
    "Append ballot data from a file."

    ballotList = ProjectBallots()
    ballotList.loadUnknown(fName)
    
    if (ballotList.numSeats != self.numSeats or ballotList.names != self.names or
        ballotList.supportObligation != self.supportObligation or
        ballotList.minimum != self.minimum or ballotList.maximum != self.maximum):
      raise RuntimeError, "Can't append ballots.  The numbers of seats\n"\
            "and candidates, and the support obligation,\n"\
            "and the names amd amounts of the candidates must\n"\
            "be identical."

    for i in xrange(ballotList.numWeightedBallots):
      w, b, a = ballotList.getWeightedProjectBallot(i)
      self.appendBallot(w, b)

    self.withdrawn += ballotList.withdrawn

  ###

#  def save(self):

  ###

  def saveAs(self, fName):
    "Create a new ballot loader and save ballots"
    
    extension = os.path.splitext( fName )[1][1:]
    loaderClass = getLoaderPluginClass(extension)
    if loaderClass is None:
      # If we don't know then the default is bltp format
      loaderClass = getLoaderPluginClass("bltp")
    self.loader = loaderClass()
    self.loader.save(self, fName)

  ###

  def reorderCandidates(self, order=[]):
    "Reorder candidates in alphabetical order or the order specified."

    if order == []:
      # Default is alphabetical order
      order = range(self.numCandidates)
      order.sort(key=lambda c: self.names[c])

    # Check to make sure that all candidates are included
    check = order[:]
    check.sort()
    if check != range(self.numCandidates):
      raise RuntimeError, "Must specify all the candidates when reordering."

    # Set up a translation list.
    # order gives the desired candidate order, e.g., [4 0 3 1 2]
    # Thus, we want 4->0, 0->1, 3->2, 1->3, and 2-> 4
    # c2c does this translation
    c2c = [0] * self.numCandidates
    for i, c in enumerate(order):
      c2c[c] = i

    # Copy the ballots with the new candidate indices.
    oldWeightedBallots = self.getWeightedProjectBallots()
    self.deleteBallots()
    for weight, ballot, amts in oldWeightedBallots:
      ballot2 = []
      for c in ballot:
        ballot2.append(c2c[c])
      self.appendProjectBallot(weight, ballot2,amts)

    # Put the names in the right order
    oldNames = self.names[:]
    oldMinimum = self.minimum[:]
    oldMaximum = self.maximum[:]
    for c in range(self.numCandidates):
      cc = c2c[c]
      self.names[cc] = oldNames[c]
      self.minimum[cc] = oldMinimum[c]
      self.maximum[cc] = oldMaximum[c]

  ###

  def getFileName(self):
    "The name of the last file I was saved or loaded from"
    fName = Ballots.getFileName(self)
    if (fName is None):
      return ""
    else:
      return fName
