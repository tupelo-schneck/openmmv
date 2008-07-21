#!/usr/bin/env python

import operator, election

class FundingLevel:
    """
    A specific funding level of a project.  Variables include:
    amount (float)      - The dollar amount
    support (float)     - The number of supporters at that dollar amount
    nweSupport (float)  - A holding variable used during vote counting
    """
    def __init__(self, amount, support, newsupport=None):
        self.amount = amount
        self.support = support
        self.newSupport = newsupport

class Project:
    """
    Projects to be voted upon.  Variables include:
    id (int)                - An automatically generated id number.  Used internally
    name (string)           - Name of the project
    minimumBudget (float)   - Lowest amount this project is requesting
    maximumBudeget (float)  - Highest amount this project is requesting
    category (int)          - Id of cateogry this project belongs to (0 for none)
    eliminated (float)      - Dollar amount at which a funding level is
                              eliminated.  Starts at infinity, drops as election is run
    fundings (list)         - A list of FundingLevel objects for this project.
                               Generally generated as election is run
    """
    def __init__(self, id, name, min, max, cat=0, elim=float("inf"), fund=[]):
        self.id = id
        self.name = name
        self.minimumBudget = min
        self.maximumBudget = max
        self.category = cat
        self.eliminated = elim
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
        self.projectId = id
        self.proposedFunding = funding
        self.priorProposedFunding = None  # FIXME: write a function to figure this out
        self.actualTotalFunding = None  # as determined by program
        self.voterSupport = None    # voter's share of total support
        self.voterFunding = None    # voter's share of total funding
    
    def __str__(self):
        return "Fund %i at %.2f" % (self.projectId, self.proposedFunding)

class Ballot:
    """
    A complete ballot.  Variables include:
    balllotId (int)     - Unique Id number for each ballot.  Used internally only.
    ballotName (str)    - Can be a name, anonymous number, group, whatever
    ballotItems (dict)  - dict of lists of BallotItem instances.  Keyed by rank (int)
    """
    def __init__(self, id, name=""):
        self.ballotId = id
        self.ballotName = str(name)
        self.ballotItems = {}
    
    def __str__(self):
        return self.ballotName
    
    def create_nest_list(self):
        """Creates a list of lists of BallotItems, ordered by rank"""
        itemsFinal = []
        keys = self.ballotItems.keys()
        keys.sort()
        for key in keys:
            itemsFinal.append(self.ballotItems[key])

class Election:
    """
    An election, including functions to run said election.  Varibles include:
    ballots (dict)     - a dict of Ballot instances, keyed by ballotId
    projects (dict)    - same as above, for projects
    categories (dict)  - same as above, for categories
    totalResources (float)  - total amount of money to be allocated
    quota (float)   - number of votes a project needs to get funded
    roundToNearest (float)  - smallest change in resources we care about
    """
    ballots = {}    # {ballotId: Ballot instance}
    projects = {}   # {id: Project instance}
    categories = {} # {id: "category name"}
    totalResources = 0.0
    quota = 0.0
    roundToNearest = 0.0
    
    def import_bltp(self, filename):
        # FIXME: this whole function needs error checking stuff.
        f = open(filename,"r")
        # deal with first line (resources, quota percentage, rounding)
        line1 = f.readline()
        line = line1.strip().split()
        self.totalResources = float(line[0])
        self.quota = float(line[1]) / 100
        self.roundToNearest = float(line[2])
        print "Imported resources, quota, and rounding info."
        
        print "Import categories..."
        line = f.readline().strip()
        while line != "--START PROJECTS--":
            k, v = line.split(" ", 1)
            self.categories[int(k)] = str(v)
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
                self.ballots[b.ballotId] = b
                print "Ballot for %s imported." % b.ballotName
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
        print "Saving resources, quota and rounding info..."
        f.write("%.2f %.2f %.2f\n"
                % (self.totalResources, self.quota * 100, self.roundToNearest))
        print "Saving Categories..."
        for k, v in self.categories.iteritems():
            f.write("%i %s\n" % (k, v))
            print "Category %s saved." % v
        print "Saving Projects..."
        f.write("--START PROJECTS--\n")
        for p in self.projects.values():
            f.write("%.2f %.2f %i %s\n" %
                   (p.minimumBudget, p.maximumBudget, p.category, p.name))
            print "Project %s saved." % p.name
        print "Saving Ballots..."
        f.write("--START BALLOTS--\n")
        for b in self.ballots.values():
            f.write("%s\n" % b.ballotName)
            for rank, items in b.ballotItems.iteritems():
                for item in items:
                    f.write("%i %i %.2f\n" %
                           (rank, item.projectId + 1.0, item.proposedFunding))
                rank += 1
            f.write("0\n")
            print "Ballot %s saved." %  b.ballotName
        f.write("EOF\n")
        print "Export complete!"
        f.close()
    
    def run_election(self):
        # FIXME: results should be stored in self.results in some format
        input = self.pack_ocaml_election()
        output = str(election.product(2,2)) # call ocaml function here
        results = self.unpack_ocaml_election(output)
        print "You win!"
    
    def pack_ocaml_election(self):
        """Packs election info into a string to by processed by ocaml"""
        pass
    
    def unpack_ocaml_eleciton(self):
        """Unpack election results string returned from ocaml"""
        pass
    
    def get_ballot_by_name(self, name):
        try:
            b  = [k for k, v in self.ballots.iteritems() if v.ballotName == name][0]
            return self.ballots[b]
        except KeyError:
            return None
    
    def get_project_by_name(self, name):
        try:
            p  = [k for k, v in self.projects.iteritems() if v.name == name][0]
            return self.projects[p]
        except KeyError:
            return None
            
    def get_category_by_name(self, name):
        try:
            p  = [k for k, v in self.categories.iteritems() if v.name == name][0]
            return self.categories[p]
        except KeyError:
            return None

    def print_ballots(self):
        if len(self.ballots) == 0:
            print "No ballots"
        else:
            for ballot in self.ballots.values():
                print ballot
                
    def print_projects(self):
        if len(self.projects) == 0:
            print "No projects"
        else:
            for project in self.projects.values():
                print project
