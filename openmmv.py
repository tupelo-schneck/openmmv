#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, operator, string
import wx, wx.grid
import  wx.lib.mixins.listctrl  as  listmix
from wx.lib.mixins import treemixin
import elections

class ProjectDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        # begin wxGlade: ProjectDialog.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.THICK_FRAME
        wx.Dialog.__init__(self, *args, **kwds)
        self.label_1 = wx.StaticText(self, -1, "Project Name: ")
        self.txtName = wx.TextCtrl(self, -1, "")
        self.label_2 = wx.StaticText(self, -1, "Category: ")
        self.listCategories = wx.ListBox(self, -1, choices=[], style=wx.LB_SINGLE)
        self.butAddCategory = wx.Button(self, -1, "Add Category")
        self.label_3 = wx.StaticText(self, -1, "Minimum Budget: ")
        self.txtMin = wx.TextCtrl(self, -1, "")
        self.label_4 = wx.StaticText(self, -1, "Maximum Budget: ")
        self.txtMax = wx.TextCtrl(self, -1, "")
        self.ProjectCancel = wx.Button(self, wx.ID_CANCEL, "")
        self.ProjectOk = wx.Button(self, wx.ID_OK, "")
        
        self.parent = args[0]

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onNewProjectAddCat, self.butAddCategory)
        
        self.PopulateCatList()

    def __set_properties(self):
        self.SetTitle("Add New Project")
        self.SetSize((422, 284))

    def __do_layout(self):
        # begin wxGlade: ProjectDialog.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2.Add(self.label_1, 0, 0, 0)
        sizer_2.Add(self.txtName, 0, 0, 0)
        sizer_1.Add(sizer_2, 0, wx.EXPAND, 0)
        sizer_3.Add(self.label_2, 0, 0, 0)
        sizer_3.Add(self.listCategories, 1, wx.EXPAND, 0)
        sizer_3.Add(self.butAddCategory, 0, 0, 0)
        sizer_1.Add(sizer_3, 1, wx.EXPAND, 0)
        sizer_4.Add(self.label_3, 0, wx.LEFT|wx.RIGHT, 3)
        sizer_4.Add(self.txtMin, 0, 0, 0)
        sizer_4.Add(self.label_4, 0, wx.LEFT|wx.RIGHT, 5)
        sizer_4.Add(self.txtMax, 0, 0, 0)
        sizer_1.Add(sizer_4, 0, wx.EXPAND, 0)
        sizer_5.Add(self.ProjectCancel, 0, wx.EXPAND, 0)
        sizer_5.Add(self.ProjectOk, 0, wx.EXPAND, 0)
        sizer_1.Add(sizer_5, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()

    def PopulateCatList(self):
        self.listCategories.Clear()
        catList = []
        for c in self.parent.election.categories.values():
            catList.append(c.name)
        catList.sort()
        self.listCategories.InsertItems(catList,0)

    def onNewProjectAddCat(self, event):
        self.parent.OnAddCategory(event)
        self.PopulateCatList()

class BallotListCtrl(wx.ListCtrl,
                   listmix.ListCtrlAutoWidthMixin,
                   listmix.TextEditMixin):

    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)

        listmix.ListCtrlAutoWidthMixin.__init__(self)
        
        self.InsertColumn(0, "Rank")
        self.InsertColumn(1, "Project")
        self.InsertColumn(2, "Proposed Funding")
        self.SetColumnWidth(0, 50)
        self.SetColumnWidth(1, 100)
        self.SetColumnWidth(2, wx.LIST_AUTOSIZE)
        
        listmix.TextEditMixin.__init__(self)
    
    def SetStringItem(self, index, col, data):
        litem = self.GetItem(index)
        dataId = litem.GetData()
        item = MainFrame.listDataDict[dataId]
        Debug("SetStringItem: item => %s" % item)
        oldRank = self.getColumnText(index, 0)
        wx.ListCtrl.SetStringItem(self, index, col, data)
        newRank = self.getColumnText(index, 0)
        if MainFrame.needUpdateBallotList == True:
            item.proposedFunding = float(self.getColumnText(index, 2))
            ballot = MainFrame.election.ballots[MainFrame.currentBallot]
            if oldRank != newRank:
                ballot.change_rank(item, oldRank, newRank)
            MainFrame.needUpdateBallotList = False
        Debug("SetStringItem: %s, %s, %s, %s\n" %
                           (index,
                            self.GetItemText(index),
                            self.getColumnText(index, 1),
                            self.getColumnText(index, 2)))
    
    def getColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()

class ProjectTreeCtrl(wx.TreeCtrl, treemixin.DragAndDrop):    
    def OnDrop(self, dropItem, dragItem):
        print dropItem, dragItem
    
    def OnBeginDrag(self, event):
        Debug("begin mixin drag")
    
    def OnEndDrag(self, event):
        Debug("end mixin drag")

class Output:
    """
    This is used to capture stdout/stderr from the backend and send
    it to a wxPython window.
    """
    def __init__(self, console):
        self.console = console
    def write(self, txt):
        self.console.AppendText(txt)

# Validator Flags
ALPHA_ONLY = 1
DIGIT_ONLY = 2
FLOAT_ONLY = 3

class FieldValidator(wx.PyValidator):
    def __init__(self, flag=None, pyVar=None):
        wx.PyValidator.__init__(self)
        self.flag = flag
        self.dotted = False
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        return FieldValidator(self.flag)

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
        
        if self.flag == ALPHA_ONLY:
            for x in val:
                if x not in string.letters:
                    return False

        elif self.flag == DIGIT_ONLY:
            for x in val:
                if x not in string.digits:
                    return False

        elif self.flag == FLOAT_ONLY:
            for x in val:
                if x not in string.digits + ".":
                    return False
                if x == ".":
                    if self.dotted == False:
                        self.dotted = True
                    else:
                        return False

        return True


    def OnChar(self, event):
        key = event.GetKeyCode()

        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
            return

        if self.flag == ALPHA_ONLY and chr(key) in string.letters:
            event.Skip()
            return

        if self.flag == DIGIT_ONLY and chr(key) in string.digits:
            event.Skip()
            return

        if self.flag == FLOAT_ONLY and chr(key) in string.digits + ".":
            if chr(key) == ".":                
                if self.dotted == False:
                    self.dotted = True
                    event.Skip()
                    return
                else:
                    pass
            else:
                event.Skip()
                return

        if not wx.Validator_IsSilent():
            wx.Bell()

        return

class ListCtrlValidator(wx.PyValidator):
    def __init__(self, flag=None, pyVar=None):
        wx.PyValidator.__init__(self)
        self.flag = flag
        self.dotted = False
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        return FieldValidator(self.flag)

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
        
        if self.flag == ALPHA_ONLY:
            for x in val:
                if x not in string.letters:
                    return False

        elif self.flag == DIGIT_ONLY:
            for x in val:
                if x not in string.digits:
                    return False

        elif self.flag == FLOAT_ONLY:
            for x in val:
                if x not in string.digits + ".":
                    return False
                if x == ".":
                    if self.dotted == False:
                        self.dotted = True
                    else:
                        return False

        return True


    def OnChar(self, event):
        key = event.GetKeyCode()

        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
            return

        if self.flag == ALPHA_ONLY and chr(key) in string.letters:
            event.Skip()
            return

        if self.flag == DIGIT_ONLY and chr(key) in string.digits:
            event.Skip()
            return

        if self.flag == FLOAT_ONLY and chr(key) in string.digits + ".":
            if chr(key) == ".":                
                if self.dotted == False:
                    self.dotted = True
                    event.Skip()
                    return
                else:
                    pass
            else:
                event.Skip()
                return

        if not wx.Validator_IsSilent():
            wx.Bell()

        return

class ProjectDropObject(wx.PyDataObjectSimple):
    def __init__(self, projectId=None):
        wx.PyDataObjectSimple.__init__(self, wx.CustomDataFormat('ProjectDD'))
        self.data = ""
        self.projectId = projectId
    
    def GetDataSize(self):
        return len(self.data)
    
    def GetDataHere(self):
        return self.data  # returns a string  
    
    def SetData(self, data):
        self.data = data
        return True

class ProjectDropTarget(wx.PyDropTarget):
    def OnData(self):
        pass

class MainFrame(wx.Frame):
    def __init__(self, *args, **kwds):        
        # begin wxGlade: MainFrame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.MainNotebook = wx.Notebook(self, -1, style=0)
        self.MainNotebook_console = wx.Panel(self.MainNotebook, -1)
        self.MainNotebook_results = wx.Panel(self.MainNotebook, -1)
        self.MainNotebook_pane_1 = wx.Panel(self.MainNotebook, -1)
        self.panel_1 = wx.ScrolledWindow(self.MainNotebook_pane_1, -1, style=wx.TAB_TRAVERSAL)
        self.notebookBallot = wx.Notebook(self.panel_1, -1, style=0)
        self.notebookBallotAdvanced = wx.ScrolledWindow(self.notebookBallot, -1, style=wx.TAB_TRAVERSAL)
        self.notebookBallotSimple = wx.ScrolledWindow(self.notebookBallot, -1, style=wx.TAB_TRAVERSAL)
        self.window_1 = wx.SplitterWindow(self.notebookBallotSimple, -1, style=wx.SP_3D|wx.SP_BORDER)
        self.window_1_pane_2 = wx.Panel(self.window_1, -1)
        self.window_1_pane_1 = wx.Panel(self.window_1, -1)
        
        # Menu Bar
        self.MainFrame_menubar = wx.MenuBar()
        wxglade_tmp_menu = wx.Menu()
        self.new_election = wx.MenuItem(wxglade_tmp_menu, 101, "&New Election", "Create new Election", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendItem(self.new_election)
        self.load_election = wx.MenuItem(wxglade_tmp_menu, 102, "&Load Election", "Load previously saved Election", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendItem(self.load_election)
        self.save_election = wx.MenuItem(wxglade_tmp_menu, 103, "&Save Election", "Save current Election", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendItem(self.save_election)
        wxglade_tmp_menu.AppendSeparator()
        self.run_election = wx.MenuItem(wxglade_tmp_menu, 104, "&Run Election", "Run current Election", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendItem(self.run_election)
        wxglade_tmp_menu.AppendSeparator()
        self.results_html = wx.MenuItem(wxglade_tmp_menu, 105, "Save Results as html", "Save Election results as a webpage", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendItem(self.results_html)
        self.results_txt = wx.MenuItem(wxglade_tmp_menu, 106, "Save Results as txt", "Save Election results as plain text", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendItem(self.results_txt)
        self.results_csv = wx.MenuItem(wxglade_tmp_menu, 107, "Save Results as csv", "Save Election results as a comma-delimited file", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendItem(self.results_csv)
        wxglade_tmp_menu.AppendSeparator()
        self.add_category = wx.MenuItem(wxglade_tmp_menu, 108, "Add Project &Category", "Add a project category to current Election", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendItem(self.add_category)
        self.add_project = wx.MenuItem(wxglade_tmp_menu, 109, "Add &Project", "Add a project to the current Election", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendItem(self.add_project)
        self.add_ballot = wx.MenuItem(wxglade_tmp_menu, 110, "Add &Ballot", "Add a ballot to the current Election", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendItem(self.add_ballot)
        wxglade_tmp_menu.AppendSeparator()
        self.quit = wx.MenuItem(wxglade_tmp_menu, 200, "&Quit", "Quit OpenMMV", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendItem(self.quit)
        self.MainFrame_menubar.Append(wxglade_tmp_menu, "&File")
        self.SetMenuBar(self.MainFrame_menubar)
        # Menu Bar end
        
        self.MainFrame_statusbar = self.CreateStatusBar(1, 0)
        self.label_2 = wx.StaticText(self.MainNotebook_pane_1, -1, "Election Name: ")
        self.txtElectionName = wx.TextCtrl(self.MainNotebook_pane_1, -1, "", style=wx.TE_PROCESS_ENTER)
        self.label_4 = wx.StaticText(self.MainNotebook_pane_1, -1, "Quota Percent: ")
        self.txtQuota = wx.TextCtrl(self.MainNotebook_pane_1, -1, "", validator=FieldValidator(FLOAT_ONLY), style=wx.TE_PROCESS_ENTER)
        self.label_3 = wx.StaticText(self.MainNotebook_pane_1, -1, "Total Resources: ")
        self.txtResources = wx.TextCtrl(self.MainNotebook_pane_1, -1, "", validator=FieldValidator(FLOAT_ONLY), style=wx.TE_PROCESS_ENTER)
        self.label_5 = wx.StaticText(self.MainNotebook_pane_1, -1, "Round to Nearest: ")
        self.txtRound = wx.TextCtrl(self.MainNotebook_pane_1, -1, "", validator=FieldValidator(FLOAT_ONLY), style=wx.TE_PROCESS_ENTER)
        self.ballotsHead = wx.StaticText(self.MainNotebook_pane_1, -1, "Ballot ID of TOTAL - NAME")
        self.gridBallot = wx.grid.Grid(self.notebookBallotAdvanced, -1, size=(1, 1))
        self.butFirstBallot = wx.Button(self.MainNotebook_pane_1, -1, "<< First")
        self.butPrevBallot = wx.Button(self.MainNotebook_pane_1, -1, "< Previous")
        self.txtSearch = wx.SearchCtrl(self.MainNotebook_pane_1, -1, style=wx.TE_PROCESS_ENTER)
        self.butNextBallot = wx.Button(self.MainNotebook_pane_1, -1, "Next >")
        self.butLastBallot = wx.Button(self.MainNotebook_pane_1, -1, "Last >>")
        self.console = wx.TextCtrl(self.MainNotebook_console, -1, "", style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        self.ResultsConsole = wx.TextCtrl(self.MainNotebook_results, -1, "", style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)

        # temporarily separated out so i can find and play with these for dnd
        self.treeProjects = ProjectTreeCtrl(self.window_1_pane_1, -1, style=wx.TR_HAS_BUTTONS|wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.SUNKEN_BORDER)
        # needs validator > validator=ListCtrlValidator(FLOAT_ONLY)
        self.listProjects = BallotListCtrl(self.window_1_pane_2, -1, style=wx.LC_REPORT|wx.SUNKEN_BORDER)

        self.__set_properties()
        self.__do_layout()

        wx.EVT_CLOSE(self, self.OnClose)
        self.treeProjects.Bind(wx.EVT_TREE_BEGIN_DRAG, self.treeProjects.OnBeginDrag)
        self.treeProjects.Bind(wx.EVT_TREE_END_DRAG, self.treeProjects.OnEndDrag)
        self.treeProjects.Bind(wx.EVT_LEFT_DCLICK, self.onTreeDClick)
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginEditProjectList, self.listProjects)
        self.Bind(wx.EVT_MENU, self.OnNewElection, self.new_election)
        self.Bind(wx.EVT_MENU, self.OnLoadElection, self.load_election)
        self.Bind(wx.EVT_MENU, self.OnSaveElection, self.save_election)
        self.Bind(wx.EVT_MENU, self.OnRunElection, self.run_election)
        self.Bind(wx.EVT_MENU, self.OnSaveHtml, self.results_html)
        self.Bind(wx.EVT_MENU, self.OnSaveTxt, self.results_txt)
        self.Bind(wx.EVT_MENU, self.OnSaveCsv, self.results_csv)
        self.Bind(wx.EVT_MENU, self.OnAddCategory, self.add_category)
        self.Bind(wx.EVT_MENU, self.OnAddProject, self.add_project)
        self.Bind(wx.EVT_MENU, self.OnAddBallot, self.add_ballot)
        self.Bind(wx.EVT_MENU, self.OnQuit, self.quit)
        self.Bind(wx.EVT_BUTTON, self.onClickFirst, self.butFirstBallot)
        self.Bind(wx.EVT_BUTTON, self.onClickPrev, self.butPrevBallot)
        self.Bind(wx.EVT_BUTTON, self.onClickNext, self.butNextBallot)
        self.Bind(wx.EVT_BUTTON, self.onClickLast, self.butLastBallot)
        self.Bind(wx.EVT_TEXT_ENTER, self.onSearch, self.txtSearch)
        self.Bind(wx.EVT_TEXT_ENTER, self.onUpdateElectionName, self.txtElectionName)
        self.Bind(wx.EVT_TEXT_ENTER, self.onUpdateQuota, self.txtQuota)
        self.Bind(wx.EVT_TEXT_ENTER, self.onUpdateResources, self.txtResources)
        self.Bind(wx.EVT_TEXT_ENTER, self.onUpdateRound, self.txtRound)        
        self.txtElectionName.Bind(wx.EVT_KILL_FOCUS, self.onUpdateElectionName, self.txtElectionName)
        self.txtQuota.Bind(wx.EVT_KILL_FOCUS, self.onUpdateQuota, self.txtQuota)
        self.txtResources.Bind(wx.EVT_KILL_FOCUS, self.onUpdateResources, self.txtResources)
        self.txtRound.Bind(wx.EVT_KILL_FOCUS, self.onUpdateRound, self.txtRound)
        # end wxGlade
        
        # initialize variables
        self.election = None
        self.bltp = None
        self.currentBallot = None
        self.needToSave = False
        self.debug = True
        self.listDataDict = {}
        self.needUpdateBallotList = False
        
        # hook up console
        self.output = Output(self.console)
        sys.stdout = self.output
        if self.debug:
            sys.stderr = self.output

    def __set_properties(self):
        # begin wxGlade: MainFrame.__set_properties
        self.SetTitle("Movable Money Voting")
        self.MainFrame_statusbar.SetStatusWidths([-1])
        # statusbar fields
        MainFrame_statusbar_fields = ["Welcome to OpenMMV!"]
        for i in range(len(MainFrame_statusbar_fields)):
            self.MainFrame_statusbar.SetStatusText(MainFrame_statusbar_fields[i], i)
        self.notebookBallotSimple.SetScrollRate(10, 10)
        self.gridBallot.CreateGrid(10, 3)
        self.gridBallot.SetColLabelValue(0, "Rank")
        self.gridBallot.SetColLabelValue(1, "Project")
        self.gridBallot.SetColLabelValue(2, "Proposed Funding")
        self.gridBallot.SetColSize(2, 150)
        self.gridBallot.SetColMinimalWidth(2, 150)
        self.notebookBallotAdvanced.SetScrollRate(10, 10)
        self.panel_1.SetScrollRate(10, 10)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MainFrame.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_results = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_13 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_21 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_22 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_24 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_23 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_8 = wx.BoxSizer(wx.VERTICAL)
        sizer_12 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_10 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_7 = wx.BoxSizer(wx.VERTICAL)
        sizer_11 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_9 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_9.Add(self.label_2, 0, 0, 0)
        sizer_9.Add(self.txtElectionName, 0, 0, 0)
        sizer_7.Add(sizer_9, 1, wx.EXPAND, 0)
        sizer_11.Add(self.label_4, 0, 0, 0)
        sizer_11.Add(self.txtQuota, 0, 0, 0)
        sizer_7.Add(sizer_11, 1, wx.EXPAND, 0)
        sizer_6.Add(sizer_7, 1, wx.EXPAND, 0)
        sizer_10.Add(self.label_3, 0, 0, 0)
        sizer_10.Add(self.txtResources, 0, 0, 0)
        sizer_8.Add(sizer_10, 1, wx.EXPAND, 0)
        sizer_12.Add(self.label_5, 0, 0, 0)
        sizer_12.Add(self.txtRound, 0, 0, 0)
        sizer_8.Add(sizer_12, 1, wx.EXPAND, 0)
        sizer_6.Add(sizer_8, 1, wx.EXPAND, 0)
        sizer_4.Add(sizer_6, 0, wx.EXPAND, 0)
        sizer_4.Add(self.ballotsHead, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        sizer_23.Add(self.treeProjects, 1, wx.EXPAND, 0)
        self.window_1_pane_1.SetSizer(sizer_23)
        sizer_24.Add(self.listProjects, 1, wx.EXPAND, 0)
        self.window_1_pane_2.SetSizer(sizer_24)
        self.window_1.SplitVertically(self.window_1_pane_1, self.window_1_pane_2)
        sizer_22.Add(self.window_1, 1, wx.EXPAND, 0)
        self.notebookBallotSimple.SetSizer(sizer_22)
        sizer_21.Add(self.gridBallot, 1, wx.EXPAND, 0)
        self.notebookBallotAdvanced.SetSizer(sizer_21)
        self.notebookBallot.AddPage(self.notebookBallotSimple, "Simple")
        self.notebookBallot.AddPage(self.notebookBallotAdvanced, "Advanced")
        sizer_13.Add(self.notebookBallot, 1, wx.EXPAND, 0)
        self.panel_1.SetSizer(sizer_13)
        sizer_13.SetSizeHints(self.panel_1)
        sizer_4.Add(self.panel_1, 1, wx.EXPAND, 0)
        sizer_5.Add(self.butFirstBallot, 0, 0, 0)
        sizer_5.Add(self.butPrevBallot, 0, 0, 0)
        sizer_5.Add(self.txtSearch, 0, wx.EXPAND, 0)
        sizer_5.Add(self.butNextBallot, 0, 0, 0)
        sizer_5.Add(self.butLastBallot, 0, 0, 0)
        sizer_4.Add(sizer_5, 0, wx.EXPAND, 0)
        sizer_2.Add(sizer_4, 1, wx.EXPAND, 0)
        self.MainNotebook_pane_1.SetSizer(sizer_2)
        sizer_3.Add(self.console, 1, wx.EXPAND, 0)
        self.MainNotebook_console.SetSizer(sizer_3)
        sizer_results.Add(self.ResultsConsole, 1, wx.EXPAND, 0)
        self.MainNotebook_results.SetSizer(sizer_results)
        self.MainNotebook.AddPage(self.MainNotebook_pane_1, "Current Election")
        self.MainNotebook.AddPage(self.MainNotebook_console, "Console")
        self.MainNotebook.AddPage(self.MainNotebook_results, 'Election Results')
        sizer_1.Add(self.MainNotebook, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        sizer_1.SetSizeHints(self)
        self.SetMinSize((550, 450))
        self.Layout()
        # end wxGlade
    
    def onTreeDClick(self, event):
        item = self.treeProjects.GetSelection()
        project = self.treeProjects.GetPyData(item)
        # add ballotItem to ballot's ballotItems dict
        # default rank == -1, default fundingLevel == 0.00
        ballotItem = elections.BallotItem(project.id, 0.00)
        ballot = self.election.ballots[self.currentBallot]
        try:
            ballot.ballotItems[-1].append(ballotItem)
        except KeyError:
            ballot.ballotItems[-1] = [ballotItem]
        # add project to listctrl
        index = self.listProjects.InsertStringItem(sys.maxint, str(project.id))
        self.listProjects.SetStringItem(index, 0, "-1")
        self.listProjects.SetStringItem(index, 1, str(project.name))
        self.listProjects.SetStringItem(index, 2, "%.2f" % 0.00)
        self.listProjects.SetItemData(index, project.id)
    
    def OnBeginEditProjectList(self, event):
        if event.m_col == 1:
            Debug("OnBeginEditProjectList: vetoing edit")
            event.Veto()
            return
        self.needUpdateBallotList = True
        event.Skip()
    
    def onProjectBeginDrag(self, event):
        Debug("drag began")
    
    def onProjectEndDrag(self, event):
        Debug("drag ended")
    
    def AskToSave(self):
        if self.needToSave == True:
            dlg = wx.MessageDialog(self,
                             'Do you want to save the current election?',
                             'Warning', wx.YES_NO | wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES:
                self.OnSaveElection(None)
                self.needToSave = False
            dlg.Destroy()
    
    def DiscardWarning(self):
        if self.election != None and self.needToSave:
            dlg = wx.MessageDialog(self,
                             'Current election will be discarded.  '
                             'Would you like to continue?',
                             'Warning', wx.YES_NO | wx.ICON_WARNING)
            if dlg.ShowModal() == wx.ID_NO:
                dlg.Destroy()
                return False
            dlg.Destroy()
        return True

    def OnNewElection(self, event):
        self.AskToSave() 
        if self.DiscardWarning() == False:
            return       
        dlg = wx.TextEntryDialog(self, 
                "Election name: ", "Start New Election", style=wx.OK|wx.CANCEL)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        name = dlg.GetValue()
        dlg.Destroy()        
        self.listProjects.DeleteAllItems()
        self.treeProjects.DeleteAllItems()
        self.election = elections.Election()
        self.election.name = name
        Debug("Started new election.")
        self.Populate()
        self.needToSave = False

    def OnLoadElection(self, event):
        self.AskToSave()       
        if self.DiscardWarning() == False:
            return
        # FIXME: needs error checking.
        wildcard = "Election Files (*.bltp)|*.bltp|All Files|*.*"
        dlg = wx.FileDialog(self, "Open Election File",
                        os.getcwd(), "", wildcard, style=wx.OPEN|wx.CHANGE_DIR)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        self.bltp = dlg.GetPath()
        dlg.Destroy()
        self.election = elections.Election()
        self.election.import_bltp(self.bltp)
        self.Populate()
        self.needToSave = False

    def OnSaveElection(self, event):
        wildcard = "Election Files (*.bltp)|*.bltp"
        dlg = wx.FileDialog(self, "Save Election",
                        os.getcwd(), "", wildcard, style=wx.SAVE|wx.CHANGE_DIR)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        self.bltp = dlg.GetPath()
        dlg.Destroy()
        self.election.export_bltp(self.bltp)
        self.needToSave = False

    def OnRunElection(self, event):
        if self.election == None:
            dlg = wx.MessageDialog(self,
                             'No election to run!\n\n'
                             'Please create an election first.',
                             'Warning', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
            return
        self.election.run_election()
        # display self.election.results in results tab on main notebook
        self.ResultsConsole.AppendText("%s" % self.election.results)
        Debug("%s" % self.election.results)

    def OnSaveHtml(self, event): # wxGlade: MainFrame.<event_handler>
        Debug("Event handler `OnSaveHtml' not implemented!")
        event.Skip()

    def OnSaveTxt(self, event): # wxGlade: MainFrame.<event_handler>
        Debug("Event handler `OnSaveTxt' not implemented!")
        event.Skip()

    def OnSaveCsv(self, event): # wxGlade: MainFrame.<event_handler>
        Debug("Event handler `OnSaveCsv' not implemented!")
        event.Skip()

    def OnAddCategory(self, event):
        if self.election == None:
            self.election = elections.Election()
            self.needToSave = True
        dlg = wx.TextEntryDialog(self, 
                "Category name: ", "Add New Category", style=wx.OK|wx.CANCEL)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        name = dlg.GetValue()
        dlg.Destroy()
        id = len(self.election.categories) + 1
        self.election.categories[id] = elections.Category(id, name)
        self.needToSave = True
        Debug("added cateogry: %d - %s" % (id, name))
        self.PopulateBallot(self.currentBallot)

    def OnAddProject(self, event):
        if self.election == None:
            self.election = elections.Election()
            self.needToSave = True
        dlg = ProjectDialog(self, -1, "")
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        name = dlg.txtName.GetValue()
        catName = dlg.listCategories.GetStringSelection()
        cat = self.election.get_item_by_name(catName, self.election.categories)
        min = float(dlg.txtMin.GetValue())
        max = float(dlg.txtMax.GetValue())
        dlg.Destroy()
        id = len(self.election.projects)
        self.election.projects[id] = elections.Project(id, name, min, max, cat.id)
        self.needToSave = True
        Debug("added project: %d - %s" % (id, name))
        self.PopulateBallot(self.currentBallot)

    def OnAddBallot(self, event):
        if self.election == None:
            self.election = elections.Election()
            self.needToSave = True
        dlg = wx.TextEntryDialog(self, 
                "Ballot name: ", "Add New Ballot", style=wx.OK|wx.CANCEL)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        name = dlg.GetValue()
        dlg.Destroy()
        id = len(self.election.ballots)
        self.election.ballots[id] = elections.Ballot(id, name)
        self.needToSave = True
        Debug("added ballot: %d - %s" % (id, name))
        self.PopulateBallot(id)

    def OnClose(self, event): 
        self.AskToSave()       
        if self.DiscardWarning() == False:
            return
        self.Destroy()

    def OnQuit(self, event):
        self.Close()

    def onSearch(self, event):
        name = event.GetString()
        b = self.election.get_item_by_name(name, self.election.ballots)
        if b == None:
            dlg = wx.MessageDialog(self, 
                'Ballot "%s" not found' % name, "Error", style=wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            self.txtSearch.SetValue("")
        else:
            Debug("populate ballot %d - %s" % (b.id+1, b.name))
            self.PopulateBallot(b.id)
            self.txtSearch.SetValue("")

    def onClickFirst(self, event):
        if self.currentBallot in [0, None]:
            pass
        else:
            self.PopulateBallot(0)

    def onClickPrev(self, event):
        if self.currentBallot in [0, None]:
            pass
        else:
            self.PopulateBallot(self.currentBallot - 1)

    def onClickNext(self, event):
        if self.currentBallot in [None, len(self.election.ballots) - 1]:
            pass
        else:
            self.PopulateBallot(self.currentBallot + 1)

    def onClickLast(self, event):
        if self.currentBallot in [None, len(self.election.ballots) - 1]:
            pass
        else:
            self.PopulateBallot(len(self.election.ballots) - 1)
    
    def onUpdateElectionName(self, event):
        if self.election == None:
            self.election = elections.Election()
            self.needToSave = True
        val = self.txtElectionName.GetValue()
        if self.election.name == str(val):
            return
        self.election.name = str(val)
        self.needToSave = True
        Debug("new election value: name == %s" % self.election.name)
    
    def onUpdateQuota(self, event):
        if self.election == None:
            self.election = elections.Election()
            self.needToSave = True
        val = self.txtQuota.GetValue()
        if val in [None, ""]:
            return
        try:
            if float(val) == self.election.quota:
                return
            self.election.quota = float(val)
            self.needToSave = True
            Debug("new election value: quota == %.2f" % self.election.quota)
        except ValueError:
            dlg = wx.MessageDialog(self, 
                "Quota must be a number", "Error", style=wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            self.txtQuota.SetValue("")
            self.txtQuota.SetFocus()
    
    def onUpdateResources(self, event):
        if self.election == None:
            self.election = elections.Election()
            self.needToSave = True
        val = self.txtResources.GetValue()
        if val in [None, ""]:
            return
        try:
            if float(val) == self.election.totalResources:
                return
            self.election.totalResources = float(val)
            self.needToSave = True
            Debug("new election value: resources == %.2f" % self.election.totalResources)
        except ValueError:
            dlg = wx.MessageDialog(self, 
                "Resources must be a number", "Error", style=wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            self.txtResources.SetValue("")
            self.txtResources.SetFocus()
    
    def onUpdateRound(self, event):
        if self.election == None:
            self.election = elections.Election()
            self.needToSave = True
        val = self.txtRound.GetValue()
        if val in [None, ""]:
            return
        try:
            if float(val) == self.election.roundToNearest:
                return
            self.election.roundToNearest = float(val)
            self.needToSave = True
            Debug("new election value: round == %.2f" % self.election.roundToNearest)
        except ValueError:
            dlg = wx.MessageDialog(self, 
                "Resources must be a number", "Error", style=wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            self.txtRound.SetValue("")
            self.txtRound.SetFocus()
            
    def PopulateBallotSimple(self, ballot):
        self.listProjects.DeleteAllItems()
        self.treeProjects.DeleteAllItems()
        # Fill in availble projects tree
        catIdDict = {}
        root = self.treeProjects.AddRoot("Root")
        if len(self.election.categories) > 0:
            dict = sorted(self.election.categories.values(), key=operator.attrgetter("name"))
            for v in dict:
                child = self.treeProjects.AppendItem(root, "%s" % v.name)
                self.treeProjects.SetPyData(child, v)
                catIdDict[v.id] = child
            dict = sorted(self.election.projects.values(), key=operator.attrgetter("name"))
            for v in dict:
                root = catIdDict[v.category]
                child = self.treeProjects.AppendItem(root, "%s" % v.name)
                self.treeProjects.SetPyData(child, v)
        elif len(self.election.categories) == 0:
            # case for uncategorized projects
            dict = sorted(self.election.projects.values(), key=operator.attrgetter("name"))
            for v in dict:
                child = self.treeProjects.AppendItem(root, "%s" % v.name)
                self.treeProjects.SetPyData(child, v)
        # fill in ballot vote list control
        for rank, items in ballot.ballotItems.iteritems():
            for item in items:
                Debug("item: %s" % item)
                dataId = wx.NewId()
                self.listDataDict[dataId] = item
                Debug("listData id# %i => %s" %(dataId, item))
                index = self.listProjects.InsertStringItem(sys.maxint, str(rank))
                self.listProjects.SetItemData(index, dataId)
                Debug("new item data => %s" % self.listProjects.GetItemData(index))
                self.listProjects.SetStringItem(index, 0, str(rank))
                self.listProjects.SetStringItem(index, 1, str(self.election.projects[item.projectId].name))
                self.listProjects.SetStringItem(index, 2, "%.2f" % item.proposedFunding)
        self.listProjects.currentItem = 0
        self.listProjects.SetColumnWidth(0, 50)
        self.listProjects.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.listProjects.SetColumnWidth(2, wx.LIST_AUTOSIZE)
    
    def PopulateBallotAdvanced(self, ballot):
        self.gridBallot.ClearGrid()
        row = 0
        for id, item in ballot.ballotItems.iteritems():
            for v in item:
                self.gridBallot.SetCellValue(row, 0, str(id))
                self.gridBallot.SetCellValue(row, 1, str(self.election.projects[v.projectId].name))
                self.gridBallot.SetCellValue(row, 2, "%.2f" % v.proposedFunding)
                row += 1
        self.gridBallot.AutoSizeColumns()
    
    def PopulateBallot(self, id):
        Debug("populating ballot id = %d" % id)
        try:
            self.currentBallot = id
            b = self.election.ballots[id]
            self.PopulateBallotAdvanced(b)
            self.PopulateBallotSimple(b)
            bid = b.id + 1
            name = b.name
            total = len(self.election.ballots)
            self.ballotsHead.SetLabel("Ballot %d of %d - %s" % (bid, total, name))
        except KeyError:
            Debug("No ballots in current election.")
            self.ballotsHead.SetLabel("Ballot 0 of 0")
            self.gridBallot.ClearGrid()
            self.listProjects.DeleteAllItems()
            self.treeProjects.DeleteAllItems()
        
    def Populate(self):
        """Populate gui with data from loaded election"""
        # Load name, quota, resources, rounding
        self.txtElectionName.SetValue(str(self.election.name))
        self.txtQuota.SetValue("%.2f" % self.election.quota)
        self.txtResources.SetValue("%.2f" % self.election.totalResources)
        self.txtRound.SetValue("%.2f" % self.election.roundToNearest)
        # Load and populate first ballot
        self.PopulateBallot(0)

# end of class MainFrame

def Debug(msg):
    if MainFrame.debug == True:
        print msg

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    MainFrame = MainFrame(None, -1, "")
    app.SetTopWindow(MainFrame)
    MainFrame.Show()
    app.MainLoop()
