# The bltp format:
# Hash sign # marks a comment until end of line.
# Blank lines or comment lines are ignored.
#
# <num_categories>:<num_projects> <total_resources> <quota_pct> <round_to_nearest>
# -<project_to_eliminate>
# -<project_to_eliminate>
# ...
# <ballot_name> <ballot_weight> <ballot_item> <ballot_item> ... 0
# <ballot_name> <ballot_weight> <ballot_item> <ballot_item> ... 0
# ...
# 0
# <category_name>
# <category_name>
# ...
# <category>:<project_name> <minimum> <maximum>
# <category>:<project_name> <minimum> <maximum>
# ...
# <election_name>
#
# The form of <ballot_item> is <ballot_rank>:<project>(<amount>)
#
# Projects and categories can be referenced either by index (starts at 1) or name.
# Almost everything can be omitted:
# <num_categories> defaults to 0 (also omit the colon)
# <quota_pct> defaults to 0
# <round_to_nearest> defaults to 1
# <ballot_name> defaults to ''
# <ballot_rank> defaults to next in rank order
# <amount> defaults to project maximum
# <minimum> defaults to 1
# <maximum> defaults to minimum
# <category> defaults to 0 for 'None' (also omit the colon)

import elections

def find_end_quote(s,n):
    i = n
    bs = False
    while i < len(s):
        if s[i] == '\\':
            bs = not bs
        elif s[i] == '"':
            if bs:
                bs = False
            else:
                return i
        else:
            bs = False
        i = i + 1
    raise SyntaxError, "non-terminated string"

def unquote_if_needed(s):
    if s == '' or s[0] != '"': return s
    i = 1
    bs = False
    while i < len(s):
        if s[i] == '\\':
            if bs:
                s = s[:i-1] + s[i:]
                bs = False
            else:
                bs = True
                i = i + 1
        elif s[i] == '"':
            if bs:
                s = s[:i-1] + s[i:]
                bs = False
            else:
                if i + 1 < len(s): raise SyntaxError, "extra characters past end quote: " + s
                return s[1:i]
        else:
            bs = False
            i = i + 1
    raise SyntaxError, "non-terminated string"

# understands double-quoted strings and comments
def savvy_split(s):
    res = []
    s = s.strip()
    while s != '':
        if s[0] == '#':
            return res
        i = 0
        while i < len(s):
            if s[i] == '#':
                res.append(s[:i])
                return res
            if s[i].isspace():
                res.append(s[:i])
                s = s[i:].lstrip()
                break
            elif s[i] == '"':
                i = find_end_quote(s,i+1) + 1
            else:
                i = i + 1
        else:
            res.append(s)
            return res
    return res

def parse_ballot_item(s):
    rank = None
    if s == '': raise SyntaxError, "blank ballot item?"
    if s[0] != '"':
        colon = s.find(':')
        if colon >= 0:
            rank = int(s[0:colon])
        s = s[colon+1:]
        if s == '': raise SyntaxError, "ballot item with only rank?"
    if s[0] == '"':
        end_quote = find_end_quote(s,1)
        name = s[0:end_quote+1]
        s = s[end_quote+1:]
    else:
        if s.find('"') >= 0: raise SyntaxError, "misplaced quote"
        paren = s.find('(')
        if paren < 0:
            name = s
            s = ''
        else:
            name = s[0:paren]
            s = s[paren:]
    if s == '':
        return (rank,name,None)
    if s[0] != '(' or s[-1] != ')':
        raise SyntaxError, "badly formed amount"
    return (rank,name,float(s[1:-1]))

def is_weight(s):
    for ch in s:
        if not ch.isdigit() and not ch == '.': return False
    return True

def import_bltp(e,filename):
  e.reset()
  f = open(filename,'r')
  try:    
    strs = []
    while strs == []:
        line = f.readline()
        if line == '': raise SyntaxError, "never found first line"
        strs = savvy_split(line)
    if len(strs) < 2:
        raise SyntaxError, "badly formed first line"
    substrs = strs[0].split(':')
    if len(substrs) == 1:
        numcats = 0
        numprojects = int(strs[0])
    elif len(substrs) == 2:
        numcats = int(substrs[0])
        numprojects = int(substrs[1])
    else:
        raise SyntaxError, "badly formed cats:projects count"
    
    e.totalResources = float(strs[1])
    if len(strs) >= 3:
        e.quota = float(strs[2])
    else:
        e.quota = 0.0
    if len(strs) >= 4:
        e.roundToNearest = float(strs[3])
    else:
        e.roundToNearest = 1.0
    if len(strs) >= 5:
        raise SyntaxError, "badly formed first line"        
    
    strs = []
    while ['0'] != strs:
        line = f.readline()
        if line == '': raise SyntaxError, "never found end of ballots"
        strs = savvy_split(line)

    i = 0
    e.categories[0] = elections.Category(0,"None")
    while i < numcats:
        i = i + 1
        strs = []
        while strs == []:
            line = f.readline()
            if line == '': raise SyntaxError, "expecting another category"
            strs = savvy_split(line)
        if len(strs) != 1: raise SyntaxError, "extra information with category"
        name = unquote_if_needed(strs[0])
        e.categories[i] = elections.Category(i,name)

    i = 0
    while i < numprojects:
        i = i + 1
        strs = []
        while strs == []:
            line = f.readline()
            if line == '': raise SyntaxError, "expecting another project"
            strs = savvy_split(line)
        if strs[0][0] == '"':
            colon = find_end_quote(strs[0],1) + 1
            if colon == len(strs[0]): colon = -1
        else:
            colon = strs[0].find(':')
        if colon == -1:
            cat = 0
            name = unquote_if_needed(strs[0])
        else:
            name = unquote_if_needed(strs[0][colon+1:])
            catName = strs[0][:colon]
            if catName.isdigit():
                cat = int(catName)
            else:
                catName = unquote_if_needed(catName)
                for cat in e.categories.values():
                    if catName == cat.name:
                        cat = cat.id
                        break
                else:
                    raise SyntaxError, "couldn't find category: " + catName
        if len(strs) >= 2:
            minB = float(strs[1])
        else:
            minB = 1.0
        if len(strs) >= 3:
            maxB = float(strs[2])
        else:
            maxB = minB
        e.projects[i] = elections.Project(i,name,minB,maxB,cat)

    strs = []
    while strs == []:
        line = f.readline()
        if line == '': raise SyntaxError, "never found election title"
        strs = savvy_split(line)
    if len(strs)>1: raise SyntaxError, "badly formed title"
    e.name = unquote_if_needed(strs[0])
    while line != '':
        line = f.readline()
        if savvy_split(line) != []: raise SyntaxError, "garbage after title"
    
    f.seek(0)
    strs = []
    while strs == []:
        line = f.readline()
        strs = savvy_split(line)
    while True:
        strs = []
        while strs == []:
            line = f.readline()
            strs = savvy_split(line)
        if len(strs)>1 or strs[0][0]!='-': break
        name = strs[0][1:]
        if name.isdigit():
            project = int(name)
        else:
            name = unquote_if_needed(name)
            for p in e.projects.values():
                if p.name == name:
                    project = p.id
                    break
            else:
                raise SyntaxError, "couldn't find project named " + name
        e.projects[project].eliminated = 0
        
    i = 0
    while True:
        if ['0'] == strs: break
        i = i + 1

        if '0' != strs[-1]: raise SyntaxError, "expecting 0 at end of ballot"
        if len(strs) < 2: raise SyntaxError, "badly formed ballot"
        if is_weight(strs[0]):
            name = ''
            weight = float(strs[0])
            strs = strs[1:-1]
        else:
            name = unquote_if_needed(strs[0])
            weight = float(strs[1])
            strs = strs[2:-1]
        b = elections.Ballot(i,name,weight) 

        defaultRank = 1
        for bis in strs:
            (rank, name, amount) = parse_ballot_item(bis)
            if rank == None:
                rank = defaultRank
                defaultRank = defaultRank + 1
            else:
                rank = int(rank)
                defaultRank = max(defaultRank,rank+1)
            if name.isdigit():
                project = int(name)
            else:
                name = unquote_if_needed(name)
                for p in e.projects.values():
                    if p.name == name:
                        project = p.id
                        break
                else:
                    raise SyntaxError, "couldn't find project named " + name
            if amount == None:
                amount = e.projects[project].maximumBudget
            else:
                amount = float(amount)
            if b.ballotItems.has_key(rank):
                b.ballotItems[rank].append(elections.BallotItem(project,amount))
            else:
                b.ballotItems[rank] = [elections.BallotItem(project,amount)]

        e.ballots[b.id] = b

        strs = []
        while strs == []:
            line = f.readline()
            strs = savvy_split(line)
  finally:
    f.close()

def quote(s):
    return '"' + s.replace('\\','\\\\').replace('"','\\"') + '"'

def str_float(f):
    if f == int(f):
        return str(int(f))
    else:
        return str(f)

def export_bltp(e,filename):
    f = open(filename,'w')
    try:
        numcats = len(e.categories)
        if 0 in e.categories.keys():
            numcats = numcats - 1
        if numcats > 0:
            f.writelines([str(numcats),':'])
        f.writelines([str(len(e.projects)),' ',str_float(e.totalResources)])
        if e.quota > 0.0 or e.roundToNearest != 1.0:
            f.writelines([' ',str_float(e.quota)])
        if e.roundToNearest != 1.0:
            f.writelines([' ',str_float(e.roundToNearest)])
        f.write('\n')

        projectKeys = sorted(e.projects.keys())
        def new_id(key): return projectKeys.index(key) + 1

        for b in e.ballots.values():
            if b.name != '': f.writelines([quote(b.name),' '])
            f.writelines([str_float(b.weight),' '])
            defaultRank = 1
            items = sorted(b.ballotItems.items())
            for (rank, bis) in items:
              for bi in bis:
                if rank != defaultRank or len(b.ballotItems[rank]) > 1:
                    f.writelines([str(rank),':'])
                f.write(str(new_id(bi.projectId)))
                p = e.projects[bi.projectId]
                if p.minimumBudget != p.maximumBudget:
                    f.writelines(['(',str_float(bi.proposedFunding),')'])
                f.write(' ')
                if rank == defaultRank:
                    defaultRank = defaultRank + 1
                else:
                    defaultRank = max(defaultRank, rank+1)
            f.write ('0\n')

        f.write ('0\n')

        for c in e.categories.values():
            if c.id != 0:
                f.writelines([quote(c.name),'\n'])

        catKeys = sorted(e.categories.keys())
        try:
            catKeys.remove(0)
        except:
            pass
        def new_id(key): return catKeys.index(key) + 1

        for p in e.projects.values():
            if p.category != 0:
                f.writelines([str(new_id(p.category)),':'])
            f.write(quote(p.name))
            if p.minimumBudget != 1.0:
                f.writelines([' ',str_float(p.minimumBudget)])
            if p.maximumBudget > p.minimumBudget:
                f.writelines([' ',str_float(p.maximumBudget)])
            f.write('\n')

        f.writelines([quote(e.name),'\n'])
    finally:
        f.close()
