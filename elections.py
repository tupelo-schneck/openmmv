#!/usr/bin/env python

import operator
import pycamlmmv
import bltp

class FundingLevel:
    """
    A specific funding level of a project.  Variables include:
    amount (float)      - The dollar amount
    support (float)     - The number of supporters at that dollar amount
    nweSupport (float)  - A holding variable used during vote counting
    """
    def __init__(self, amount, support, prevSupport=None):
        self.amount = float(amount)
        self.support = float(support)
        self.prevSupport = float(prevSupport)
    
    def __str__(self):
        return "%.2f support at $%.2f" % (self.support, self.amount)

class Project:
    """
    Projects to be voted upon.  Variables include:
    id (int)                - An automatically generated id number.  Used internally
    name (string)           - Name of the project
    minimumBudget (float)   - Lowest amount this project is requesting
    maximumBudegt (float)   - Highest amount this project is requesting
    category (int)          - Id of cateogry this project belongs to (0 for none)
    eliminated (float)      - Dollar amount at which a funding level is
                              eliminated.  Starts at infinity, drops as election is run
    fundings (list)         - A list of FundingLevel objects for this project.
                               Generally generated as election is run
    """
    def __init__(self, id, name, min, max, cat=0, elim=float("inf"), fund=[]):
        self.id = int(id)
        self.name = str(name)
        self.minimumBudget = float(min)
        self.maximumBudget = float(max)
        self.category = int(cat)
        self.eliminated = float(elim)
        self.fundings = fund
    
    def __str__(self):
        return self.name

class BallotItem:
    """
    A line item on a ballot.  Variables include:
    projectId (int)             - Id number of project this ballot item is for
    proposedFunding (float)     - Amount voter is wants projet to have (at this rank)
    priorProposedFunding (float)- Proposed funding from a higher rank
    actualTotalFunding (float)  - Amount project is actually funded
    voterSupprt (float)         - How much voter support gives at this funding level
    voterFunding (float)        - How much voter support gives at this funding level
    """
    def __init__(self, id, funding):
        self.projectId = int(id)
        self.proposedFunding = float(funding)
        self.priorProposedFunding = None
        self.actualTotalFunding = None
        self.voterSupport = None
        self.voterFunding = None
    
    def __str__(self):
        return "Fund Project #%i at %.2f" % (self.projectId, self.proposedFunding)

class Ballot:
    """
    A complete ballot.  Variables include:
    id (int)     - Unique Id number for each ballot.  Used internally only.
    name (str)    - Can be a name, anonymous number, group, whatever
    ballotItems (dict)  - dict of lists of BallotItem instances.  Keyed by rank (int)
    """
    def __init__(self, id, name="", weight=1.0):
        self.id = int(id)
        self.name = str(name)
        self.weight = float(weight)
        self.ballotItems = {}
    
    def __str__(self):
        return self.name
    
    def change_rank(self, item, oldRank, newRank):
        """Change rank of given ballotItem"""
        oldRank = int(oldRank)
        newRank = int(newRank)
        # add to new rank
        try:
            self.ballotItems[newRank].append(item)
        except KeyError:
            self.ballotItems[newRank] = [item]
        # remove from old rank
        try:
            self.ballotItems[oldRank].remove(item)
        except:
            print "change BI rank error: oldRank invalid"
    
    def create_nest_list(self):
        """Creates a list of lists of BallotItems, ordered by rank"""
        itemsFinal = []
        keys = self.ballotItems.keys()
        keys.sort()
        for key in keys:
            itemsFinal.append(self.ballotItems[key])        
        return itemsFinal
            
class Category:
    """
    A project category.  Variable include:
    id (int)    - category id number
    name (str)  - category name
    """
    def __init__(self, id, name=""):
        self.id = int(id)
        self.name = str(name)
    
    def __str__(self):
        return self.name

class Results:
    """
    Results of an election.  This is a class mostly to take advantage of the
    string formatting functions of python.  Variables include:
    list (list)     - list of (project ID, project name, final funding) tuples
    """
    
    def __init__(self, list):
        self.list = list
    
    def __str__(self):
        str = "-----ELECTION RESULTS-----\nProject\t\t\tFunding Level\n"
        for p in self.list:
            str += "%s\t\t\t%.2f\n" % (p[1], p[2])
        str += "\n\n"
        return str

class Election:
    """
    An election, including functions to run said election.  Variables include:
    name (str)         - name for this election
    ballots (dict)     - a dict of Ballot instances, keyed by id
    projects (dict)    - same as above, for projects
    categories (dict)  - same as above, for categories
    totalResources (float)  - total amount of money to be allocated
    quota (float)   - number of votes a project needs to get funded
    roundToNearest (float)  - smallest change in resources we care about
    results (Results instance)   - a results instance of outcome of current election
    """
    
    def __init__(self, bltp=None):
        self.name = ""
        self.ballots = {}    # {id: Ballot instance}
        self.projects = {}   # {id: Project instance}
        self.categories = {} # {id: Cateory instance}
        self.totalResources = 0.0
        self.quota = 0.0
        self.roundToNearest = 0.0
        self.results = None
        if bltp is not None:
            self.import_bltp(bltp)
    
    def reset(self):
        self.name = ""
        self.ballots = {}
        self.projects = {}
        self.categories = {}
        self.totalResources = 0.0
        self.quota = 0.0
        self.roundToNearest = 0.0
    
    def import_bltp(self, filename):
        bltp.import_bltp(self, filename)

    def export_bltp(self, filename):
        bltp.export_bltp(self, filename)
    
    def run_election(self):
        for p in self.projects.values():
            p.eliminated = float("inf")
            p.fundings = []
        pycamlmmv.run_election(self)
        self.store_results()
    
    def store_results(self):
        # create self.results
        r = []
        for project in self.projects.values():
            try:
                topLevel = project.fundings[-1]
            except:
                continue
            if topLevel.support > (self.quota / 100):
                funding = (project.id, project.name, topLevel.amount)
                r.append(funding)
        print "before: \n%s" % self.results
        self.results = None
        print "none: \n%s" % self.results
        self.results = Results(r)
        print "after: \n%s" % self.results
    
    def get_item_by_name(self, name, itemDict):
        """Search given itemDict for named item and return the instance"""
        try:
            if itemDict not in [self.ballots, self.categories, self.projects]:
                raise TypeError("Supplied dict is not ballots, categories, or projects dict")
            p  = [k for k, v in itemDict.iteritems() if v.name.lower() == name.lower()][0]
            return itemDict[p]
        except IndexError:
            return None

    def list_items_by_name(self, itemDict):
        """Given a dict of ballots, project, or categories, return list of names"""
        l = []
        if itemDict not in [self.ballots, self.categories, self.projects]:
            raise TypeError("Supplied dict is not ballots, categories, or projects dict")
        else:
            for item in itemDict.values():
                l.append(item.name)
        return l
        
