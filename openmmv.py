#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
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
        print "Event handler `onProjCancel' not implemented!"
        event.Skip()

    def onProjOk(self, event): # wxGlade: ProjectDialog.<event_handler>
        print "Event handler `onProjOk' not implemented!"
        event.Skip()

# end of class ProjectDialog


class CategoryDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        # begin wxGlade: CategoryDialog.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.THICK_FRAME
        wx.Dialog.__init__(self, *args, **kwds)
        self.label_6 = wx.StaticText(self, -1, "Category Name: ")
        self.textCatName = wx.TextCtrl(self, -1, "")
        self.butCatCancel = wx.Button(self, wx.ID_CANCEL, "")
        self.butCatOk = wx.Button(self, wx.ID_OK, "")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onCatCancel, self.butCatCancel)
        self.Bind(wx.EVT_BUTTON, self.onCatOk, self.butCatOk)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: CategoryDialog.__set_properties
        self.SetTitle("Add a Project Category")
        self.SetSize((279, 71))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: CategoryDialog.__do_layout
        sizer_14 = wx.BoxSizer(wx.VERTICAL)
        sizer_15 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_16 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_16.Add(self.label_6, 0, 0, 0)
        sizer_16.Add(self.textCatName, 2, 0, 0)
        sizer_14.Add(sizer_16, 1, wx.EXPAND, 0)
        sizer_15.Add(self.butCatCancel, 1, wx.EXPAND, 0)
        sizer_15.Add(self.butCatOk, 1, wx.EXPAND, 0)
        sizer_14.Add(sizer_15, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_14)
        self.Layout()
        # end wxGlade

    def onCatCancel(self, event): # wxGlade: CategoryDialog.<event_handler>
        print "Event handler `onCatCancel' not implemented"
        event.Skip()

    def onCatOk(self, event): # wxGlade: CategoryDialog.<event_handler>
        print "Event handler `onCatOk' not implemented"
        event.Skip()

# end of class CategoryDialog

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

    def Populate(self, ballotItems):

        for id, item in ballotItems.iteritems():
            index = self.InsertStringItem(sys.maxint, str(id))
            self.SetStringItem(index, 0, str(id))
            self.SetStringItem(index, 1, str(item.projectId))
            self.SetStringItem(index, 2, str(item.proposedFunding))
            self.SetItemData(index, id)

        self.currentItem = 0
        
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
        self.txtElectionName = wx.TextCtrl(self.MainNotebook_pane_1, -1, "")
        self.label_4 = wx.StaticText(self.MainNotebook_pane_1, -1, "Quota: ")
        self.txtQuota = wx.TextCtrl(self.MainNotebook_pane_1, -1, "")
        self.label_3 = wx.StaticText(self.MainNotebook_pane_1, -1, "Total Resources: ")
        self.txtResources = wx.TextCtrl(self.MainNotebook_pane_1, -1, "")
        self.label_5 = wx.StaticText(self.MainNotebook_pane_1, -1, "Round to Nearest: ")
        self.txtRound = wx.TextCtrl(self.MainNotebook_pane_1, -1, "")
        self.label_1 = wx.StaticText(self.MainNotebook_pane_1, -1, "Ballot ID of TOTAL - NAME")
        self.treeProjects = wx.TreeCtrl(self.window_1_pane_1, -1, style=wx.TR_HAS_BUTTONS|wx.TR_DEFAULT_STYLE|wx.SUNKEN_BORDER)
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
        # end wxGlade

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
        sizer_4.Add(self.label_1, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
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
        self.Layout()
        # end wxGlade
        
        # hook up console
        self.output = Output(self.console)
        sys.stdout = self.output
        sys.stderr = self.output
        
        # initialize variables
        self.election = elections.Election()
        self.bltp = None
        self.needToSave = False
    
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

    def OnSaveElection(self, event): # wxGlade: MainFrame.<event_handler>
        print "Event handler `OnSaveElection' not implemented!"

    def OnRunElection(self, event): # wxGlade: MainFrame.<event_handler>
        print "Event handler `OnRunElection' not implemented!"
        event.Skip()

    def OnSaveHtml(self, event): # wxGlade: MainFrame.<event_handler>
        print "Event handler `OnSaveHtml' not implemented!"
        event.Skip()

    def OnSaveTxt(self, event): # wxGlade: MainFrame.<event_handler>
        print "Event handler `OnSaveTxt' not implemented!"
        event.Skip()

    def OnSaveCsv(self, event): # wxGlade: MainFrame.<event_handler>
        print "Event handler `OnSaveCsv' not implemented!"
        event.Skip()

    def OnAddCategory(self, event): # wxGlade: MainFrame.<event_handler>
        dialog = CategoryDialog(self, -1, "")
        dialog.Show()
        event.Skip()

    def OnAddProject(self, event): # wxGlade: MainFrame.<event_handler>
        dialog = ProjectDialog(self, -1, "")
        dialog.Show()
        event.Skip()

    def OnAddBallot(self, event): # wxGlade: MainFrame.<event_handler>
        print "Event handler `OnAddBallot' not implemented!"
        event.Skip()

    def OnQuit(self, event): # wxGlade: MainFrame.<event_handler>
        print "Event handler `OnQuit' not implemented!"
        event.Skip()

    def onClick(self, event): # wxGlade: MainFrame.<event_handler>
        print "Event handler `onClick' not implemented!"
        event.Skip()

    def onEnter(self, event): # wxGlade: MainFrame.<event_handler>
        print "Event handler `onEnter' not implemented"
        event.Skip()

    def onSearch(self, event): # wxGlade: MainFrame.<event_handler>
        print "Event handler `onSearch' not implemented"
        event.Skip()

    def onClickFirst(self, event): # wxGlade: MainFrame.<event_handler>
        print "Event handler `onClickFirst' not implemented"
        event.Skip()

    def onClickPrev(self, event): # wxGlade: MainFrame.<event_handler>
        print "Event handler `onClickPrev' not implemented"
        event.Skip()

    def onClickNext(self, event): # wxGlade: MainFrame.<event_handler>
        print "Event handler `onClickNext' not implemented"
        event.Skip()

    def onClickLast(self, event): # wxGlade: MainFrame.<event_handler>
        print "Event handler `onClickLast' not implemented"
        event.Skip()

# end of class MainFrame


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    MainFrame = MainFrame(None, -1, "")
    app.SetTopWindow(MainFrame)
    MainFrame.Show()
    app.MainLoop()
