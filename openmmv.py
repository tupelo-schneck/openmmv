#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, operator
import wx, wx.grid
import  wx.lib.mixins.listctrl  as  listmix
import elections

class ProjectDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        # begin wxGlade: ProjectDialog.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.THICK_FRAME
        wx.Dialog.__init__(self, *args, **kwds)
        self.label_7 = wx.StaticText(self, -1, "Project Name: ")
        self.textProjName = wx.TextCtrl(self, -1, "")
        self.label_8 = wx.StaticText(self, -1, "Category: ")
        self.listProjCat = wx.ListBox(self, -1, choices=["Item 1", "Item 2"])
        self.butProjAddCat = wx.Button(self, -1, "Add Category")
        self.butProjectCancel = wx.Button(self, wx.ID_CANCEL, "")
        self.butProjectOk = wx.Button(self, wx.ID_OK, "")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnAddCategory, self.butProjAddCat)
        self.Bind(wx.EVT_BUTTON, self.onProjCancel, self.butProjectCancel)
        self.Bind(wx.EVT_BUTTON, self.onProjOk, self.butProjectOk)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: ProjectDialog.__set_properties
        self.SetTitle("Add a new Project")
        self.listProjCat.SetSelection(0)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: ProjectDialog.__do_layout
        sizer_17 = wx.BoxSizer(wx.VERTICAL)
        sizer_20 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_19 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_18 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_18.Add(self.label_7, 1, 0, 0)
        sizer_18.Add(self.textProjName, 2, 0, 0)
        sizer_17.Add(sizer_18, 1, wx.EXPAND, 0)
        sizer_19.Add(self.label_8, 0, 0, 0)
        sizer_19.Add(self.listProjCat, 1, 0, 0)
        sizer_19.Add(self.butProjAddCat, 0, 0, 0)
        sizer_17.Add(sizer_19, 1, wx.EXPAND, 0)
        sizer_20.Add(self.butProjectCancel, 1, wx.EXPAND, 0)
        sizer_20.Add(self.butProjectOk, 1, wx.EXPAND, 0)
        sizer_17.Add(sizer_20, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_17)
        sizer_17.Fit(self)
        self.Layout()
        # end wxGlade

    def OnAddCategory(self, event): # wxGlade: ProjectDialog.<event_handler>
        dialog = CategoryDialog(self, -1, "")
        dialog.Show()
        event.Skip()

    def onProjCancel(self, event): # wxGlade: ProjectDialog.<event_handler>
        Debug("Event handler `onProjCancel' not implemented!")
        event.Skip()

    def onProjOk(self, event): # wxGlade: ProjectDialog.<event_handler>
        Debug("Event handler `onProjOk' not implemented!")
        event.Skip()

# end of class ProjectDialog

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
        
# This is used to capture stdout/stderr from STV.py and send
# it to a wxPython window.

class Output:
    """
    This is used to capture stdout/stderr from the backend and send
    it to a wxPython window.
    """
    def __init__(self, console):
        self.console = console
    def write(self, txt):
        self.console.AppendText(txt)

class MainFrame(wx.Frame):
    def __init__(self, *args, **kwds):        
        # begin wxGlade: MainFrame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.MainNotebook = wx.Notebook(self, -1, style=0)
        self.MainNotebook_console = wx.Panel(self.MainNotebook, -1)
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
        self.txtQuota = wx.TextCtrl(self.MainNotebook_pane_1, -1, "", style=wx.TE_PROCESS_ENTER)
        self.label_3 = wx.StaticText(self.MainNotebook_pane_1, -1, "Total Resources: ")
        self.txtResources = wx.TextCtrl(self.MainNotebook_pane_1, -1, "", style=wx.TE_PROCESS_ENTER)
        self.label_5 = wx.StaticText(self.MainNotebook_pane_1, -1, "Round to Nearest: ")
        self.txtRound = wx.TextCtrl(self.MainNotebook_pane_1, -1, "", style=wx.TE_PROCESS_ENTER)
        self.ballotsHead = wx.StaticText(self.MainNotebook_pane_1, -1, "Ballot ID of TOTAL - NAME")
        self.treeProjects = wx.TreeCtrl(self.window_1_pane_1, -1, style=wx.TR_HAS_BUTTONS|wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.SUNKEN_BORDER)
        self.listProjects = BallotListCtrl(self.window_1_pane_2, -1, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.gridBallot = wx.grid.Grid(self.notebookBallotAdvanced, -1, size=(1, 1))
        self.butFirstBallot = wx.Button(self.MainNotebook_pane_1, -1, "<< First")
        self.butPrevBallot = wx.Button(self.MainNotebook_pane_1, -1, "< Previous")
        self.txtSearch = wx.SearchCtrl(self.MainNotebook_pane_1, -1, style=wx.TE_PROCESS_ENTER)
        self.butNextBallot = wx.Button(self.MainNotebook_pane_1, -1, "Next >")
        self.butLastBallot = wx.Button(self.MainNotebook_pane_1, -1, "Last >>")
        self.console = wx.TextCtrl(self.MainNotebook_console, -1, "", style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)

        self.__set_properties()
        self.__do_layout()

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
        self.MainNotebook.AddPage(self.MainNotebook_pane_1, "Current Election")
        self.MainNotebook.AddPage(self.MainNotebook_console, "Console")
        sizer_1.Add(self.MainNotebook, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        sizer_1.SetSizeHints(self)
        self.SetMinSize((450, 450))
        self.Layout()
        # end wxGlade
    
    def AskToSave(self):
        if self.needToSave == True:
            dlg = wx.MessageDialog(self,
                             'Do you want to save the current election?',
                             'Warning', wx.YES_NO | wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES:
                self.OnSaveElection(None)
            dlg.Destroy()
        self.needToSave = False
    
    def DiscardWarning(self):
        if self.election != None:
            dlg = wx.MessageDialog(self,
                             'Current election will be discarded.  '
                             'Would you like to continue?',
                             'Warning', wx.YES_NO | wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_NO:
                dlg.Destroy()
                return False
            dlg.Destroy()
        return True

    def OnNewElection(self, event):
        if self.DiscardWarning() == False:
            return
        self.AskToSave()
        self.election = elections.Election()
        print "Started new election."

    def OnLoadElection(self, event):        
        if self.DiscardWarning() == False:
            return
        if self.election == None:
            self.election = elections.Election()
        self.AskToSave()
        # FIXME: needs error checking.
        wildcard = "Election Files (*.bltp)|*.bltp|All Files|*.*"
        dlg = wx.FileDialog(self, "Open Election File",
                        os.getcwd(), "", wildcard, style=wx.OPEN|wx.CHANGE_DIR)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        self.bltp = dlg.GetPath()
        dlg.Destroy()
        self.election.import_bltp(self.bltp)
        self.Populate()

    def OnSaveElection(self, event): # wxGlade: MainFrame.<event_handler>
        Debug("Event handler `OnSaveElection' not implemented!")

    def OnRunElection(self, event): # wxGlade: MainFrame.<event_handler>
        Debug("Event handler `OnRunElection' not implemented!")
        event.Skip()

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
        dlg = wx.TextEntryDialog(self, 
                "Category name: ", "Add New Category", style=wx.OK|wx.CANCEL)
        dlg.ShowModal()
        name = dlg.GetValue()
        dlg.Destroy()
        id = len(self.election.categories) + 1
        self.election.categories[id] = elections.Category(id, name)
        Debug("added cateogry: %d - %s" % (id, name))
        b = self.election.ballots[self.currentBallot]
        self.PopulateBallotSimple(b)

    def OnAddProject(self, event):
        dialog = ProjectDialog(self, -1, "")
        dialog.ShowModal()
        event.Skip()

    def OnAddBallot(self, event): # wxGlade: MainFrame.<event_handler>
        Debug("Event handler `OnAddBallot' not implemented!")
        event.Skip()

    def OnQuit(self, event): # wxGlade: MainFrame.<event_handler>
        Debug("Event handler `OnQuit' not implemented!")
        event.Skip()

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
        val = self.txtElectionName.GetValue()
        self.election.name = str(val)
        Debug("new election value: name == %s" % self.election.name)
    
    def onUpdateQuota(self, event):
        if self.election == None:
            self.election = elections.Election()
        val = self.txtQuota.GetValue()
        if val in [None, ""]:
            return
        try:
            self.election.quota = float(val)
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
        val = self.txtResources.GetValue()
        if val in [None, ""]:
            return
        try:
            self.election.totalResources = float(val)
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
        self.CheckForElection()
        val = self.txtRound.GetValue()
        if val in [None, ""]:
            return
        try:
            self.election.roundToNearest = float(val)
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
        root = self.treeProjects.AddRoot("Categories")
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
        # fill in ballot vote list control
        for id, item in ballot.ballotItems.iteritems():
            for v in item:
                index = self.listProjects.InsertStringItem(sys.maxint, str(id))
                self.listProjects.SetStringItem(index, 0, str(id))
                self.listProjects.SetStringItem(index, 1, str(self.election.projects[v.projectId].name))
                self.listProjects.SetStringItem(index, 2, "%.2f" % v.proposedFunding)
                self.listProjects.SetItemData(index, id)
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
            b = self.election.ballots[id]
            self.PopulateBallotAdvanced(b)
            self.PopulateBallotSimple(b)
            bid = b.id + 1
            name = b.name
            total = len(self.election.ballots)
            self.ballotsHead.SetLabel("Ballot %d of %d - %s" % (bid, total, name))
            self.currentBallot = id
        except KeyError:
            self.ballotsHead.SetLabel("Ballot 0 of 0")
        
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
