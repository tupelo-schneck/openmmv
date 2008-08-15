#!/usr/bin/env python

import operator

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
    def __init__(self, id, name=""):
        self.id = int(id)
        self.name = str(name)
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
    results (TBD)   - results in some format i haven't decided on yet
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
        # FIXME: this whole function needs error checking stuff.
        self.reset()
        f = open(filename,"r")
        # deal with first line (resources, quota percentage, rounding, name)
        line1 = f.readline()
        line = line1.strip().split(" ", 3)
        self.totalResources = float(line[0])
        self.quota = float(line[1])
        self.roundToNearest = float(line[2])
        self.name = str(line[3])
        print "Imported resources, quota, rounding info, and name."
        
        print "Import categories..."
        line = f.readline().strip()
        while line != "--START PROJECTS--":
            k, v = line.split(" ", 1)
            c = Category(int(k), str(v))
            self.categories[int(k)] = c
            print "Catergory %s imported." % self.categories[int(k)]
            line = f.readline().strip()
        
        # import projects.  loops until it encounters the beginning
        # of ballots (which is marked in bltp file)
        print "Importing projects..."
        projectId = 0
        line = f.readline().strip()
        while line != "--START BALLOTS--":
            list = line.split(" ",3)
            min, max, cat, name = float(list[0]), float(list[1]), int(list[2]), str(list[3])
            p = Project(projectId, name, min, max, cat)
            self.projects[projectId] = p
            print "Project '%s' imported." % p.name
            projectId += 1
            line = f.readline().strip()
        
        # import ballots
        print "Importing ballots..."
        moreBallots = True
        ballotId = 0
        while moreBallots:
            line = f.readline()[:-1]
            if line == "EOF":
                moreBallots = False
            else:
                # create ballot instance
                b = Ballot(ballotId, str(line))
                # read in all ballot items first, then create final list
                itemsDict = {}
                line = f.readline()
                while line != "0\n":
                    rank, id, funding = line.strip().split()
                    rank = int(rank)
                    id = int(id) - 1
                    funding = float(funding)
                    try:
                        itemsDict[rank]
                    except KeyError:
                        itemsDict[rank] = [BallotItem(id, funding)]
                    else:
                        itemsDict[rank].append(BallotItem(id, funding))
                    line = f.readline()
                """
                itemsFinal = []
                for key, val in itemsDict.iteritems():
                    itemsFinal.append(val)
                b.ballotItems = itemsFinal
                """
                b.ballotItems = itemsDict
                self.ballots[b.id] = b
                print "Ballot for %s imported." % b.name
                ballotId += 1
        f.close()
        print "\nImport of file %s successful!" % filename
        print "%i categories imported" % len(self.categories)
        print "%i projects imported" % len(self.projects)
        print "%i ballots imported" % len(self.ballots)
        print "qouta percentage = %.2f" % self.quota
        print "resources available = %.2f" % self.totalResources
        print "rounding_to_nearest = %.2f" % self.roundToNearest
    
    def export_bltp(self, filename):
        f = open(filename,"w")
        print "Saving resources, quota, rounding info, and name..."
        f.write("%.2f %.2f %.2f %s\n"
                % (self.totalResources, self.quota, self.roundToNearest, self.name))
        print "Saving Categories..."
        for k, v in self.categories.iteritems():
            f.write("%i %s\n" % (k, v.name))
            print "Category %s saved." % v.name
        print "Saving Projects..."
        f.write("--START PROJECTS--\n")
        for p in self.projects.values():
            f.write("%.2f %.2f %i %s\n" %
                   (p.minimumBudget, p.maximumBudget, p.category, p.name))
            print "Project %s saved." % p.name
        print "Saving Ballots..."
        f.write("--START BALLOTS--\n")
        for b in self.ballots.values():
            f.write("%s\n" % b.name)
            for rank, items in b.ballotItems.iteritems():
                for item in items:
                    f.write("%i %i %.2f\n" %
                           (rank, item.projectId + 1.0, item.proposedFunding))
                rank += 1
            f.write("0\n")
            print "Ballot %s saved." %  b.name
        f.write("EOF\n")
        print "Export complete!"
        f.close()
    
    def run_election(self):
        # FIXME: results should be stored in self.results in some format
        import pycamlmmv
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
        
