#!/usr/bin/env python

import operator
import bltp
import pycamlmmv

class FundingLevel:
    """
    A specific funding level of a project.  Variables include:
    amount (float)      - The dollar amount
    size (float)        - How much in this funding level (amount - size = prior amount)
    vote (float)        - How much voters have contributed; wins when vote >= size
    lastVote (float)    - How much had been contributed last iteration
    support (float)     - How much support voters have given this
    lastSupport (float) - How much support last iteration
    """
    def __init__(self, amount, size, vote=0., lastVote = 0., support = 0., lastSupport = 0.):
        self.amount = float(amount)
        self.size = float(size)
        self.vote = float(vote)
        self.lastVote = float(lastVote)
        self.support = float(support)
        self.lastSupport = float(lastSupport)
    
    def __str__(self):
        return "$%.2f/$%.2f support at $%.2f" % (self.vote, self.size, self.amount)

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
        self.set_priors()

    def set_priors(self):
        priors = {}
        for rank in sorted(self.ballotItems.keys()):
            for item in self.ballotItems[rank]:
                if priors.has_key(item.projectId):
                    item.priorProposedFunding = priors[item.projectId]
                else:
                    item.priorProposedFunding = 0.0
                priors[item.projectId] = item.proposedFunding
    
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
    election (Election instance) - the election we come from
    list (list)     - list of (project ID, funding, is_winner:bool) tuples
    *** The list is stored in reverse order
    """
    
    def __init__(self, election, list):
        self.election = election
        self.list = list
    
    def __str__(self):
        str = "-----ELECTION RESULTS-----\nProject\t\t\tFunding Level\n"
        for p in self.winners():
            str += "%s\t\t\t%.2f\n" % (self.election.projects[p[0]].name, p[1])
        str += "\n\n"
        return str

    def winners(self): 
        res = [x for x in self.list if x[2]]
        res.reverse()
        return res

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
        self.results = Results(self,[])
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
        self.results.list = []
        bltp.import_bltp(self, filename)
        for b in self.ballots.values():
            b.set_priors()

    def export_bltp(self, filename):
        bltp.export_bltp(self, filename)
    
    def step_election(self):
        # run one election step
        pass
    
    def run_election(self):
        self.results.list = []
        for p in self.projects.values():
            p.eliminated = float("inf")
            p.fundings = []
        pycamlmmv.run_election(self)
    
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
