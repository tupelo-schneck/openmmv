#!/usr/bin/env python

## OpenSTV Copyright (C) 2003-2009 Jeffrey O'Neill
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

__revision__ = "$Id: OpenSTV.py 471 2009-01-31 19:29:20Z jco8 $"

import wx
import wx.html
import os
import sys
import warnings
import pdb

import version
import OpenSTV
import BFE
from  NonSTV import *
from STV import *
from ballots import *
from projectBallots import *
from projectElection import *

##################################################################
### BFE.py monkey patching ###

class MyBFEFrame(wx.Frame):

  def __init__(self, parent, home, mode):
    wx.Frame.__init__(self, parent, -1, "Ballot File Editor")

    self.MakeMenu()
    self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
    self.logfName = ""

    fn = os.path.join(home, "Icons", "blt.ico")
    icon = wx.Icon(fn, wx.BITMAP_TYPE_ICO)
    self.SetIcon(icon)

    self.LoadBallotFile(mode, parent)

  ###
  
  def LoadBallotFile(self, mode, parent):
    if mode == "new":

      # Create an empty ballots class instance
      self.b = BltBallots()

      # Get the candidate names from the user
      dlg = BFE.CandidatesDialog(parent, self.b)
      dlg.Center()
      if dlg.ShowModal() != wx.ID_OK:
        dlg.Destroy()
        self.Destroy()
        return
      dlg.Destroy()
        
    # Edit an existing ballot file
    elif mode == "old":
      dlg = wx.FileDialog(self, "Select Ballot File", os.getcwd(), "",
                          style=wx.OPEN|wx.CHANGE_DIR)
      if dlg.ShowModal() != wx.ID_OK:
        dlg.Destroy()
        self.Destroy()
        return
      fName = dlg.GetPath()
      dlg.Destroy()

      # Open the file
      try:
        self.b = Ballots.loadUnknown(fName)
      except RuntimeError, msg:
        wx.MessageBox(str(msg), "Error", wx.OK|wx.ICON_ERROR)
        self.Destroy()
        return

    else:
      assert(0)

    # Set the window title to include the filename
    title = "%s - %s" % (os.path.basename(self.b.fName),
                         "Ballot File Editor")
    self.SetTitle(title)

    # Create a notebook with an editing page and a log page
    nb = wx.Notebook(self, -1)

    self.panel = BFE.BallotsPanel(nb, self.b)
    nb.AddPage(self.panel, "Ballots")

    self.logN = 1 # counter for display purposes
    self.log = wx.TextCtrl(nb, -1,
                           style=wx.TE_MULTILINE|wx.TE_READONLY|\
                           wx.TE_WORDWRAP|wx.FIXED)
    self.log.SetMaxLength(0)
    nb.AddPage(self.log, "Log")

    # Initialize
    if mode == "new":
      self.panel.NeedToSaveBallots = True
      self.Log("Created a new ballot file.")
    elif mode == "old":
      self.panel.NeedToSaveBallots = False
      self.Log("Loaded %d ballots from file %s." %\
               (self.b.nBallots, os.path.basename(self.b.fName)))
    else:
      assert(0)

    # Set up the sizer
    sizer = wx.BoxSizer()
    sizer.Add(nb, 1, wx.EXPAND, 0)
    self.SetSizer(sizer)
    sizer.Fit(self)
    sizer.SetSizeHints(self)

  def Log(self, txt):

    # create a prompt for each new line
    prompt = "%3d: " % self.logN
    self.log.AppendText(prompt + txt + "\n")
    self.logN += 1

  ###
    
  def MakeMenu(self):

    fileMenu = wx.Menu()

    append = fileMenu.Append(-1, "A&ppend ballots from file...")
    saveBallots = fileMenu.Append(-1, "&Save ballots")
    saveBallotsAs = fileMenu.Append(-1, "Save ballots &as...")
    saveLog = fileMenu.Append(-1, "Save &log")
    saveLogAs = fileMenu.Append(-1, "Save log as...")
    exitBFE = fileMenu.Append(wx.ID_EXIT, "E&xit")

    self.Bind(wx.EVT_MENU, self.OnAppendBF, append)
    self.Bind(wx.EVT_MENU, self.OnSaveBallots, saveBallots)
    self.Bind(wx.EVT_MENU, self.OnSaveBallotsAs, saveBallotsAs)
    self.Bind(wx.EVT_MENU, self.OnSaveLog, saveLog)
    self.Bind(wx.EVT_MENU, self.OnSaveLogAs, saveLogAs)
    self.Bind(wx.EVT_MENU, self.OnExit, exitBFE)

    if wx.Platform == "__WXMAC__":
      wx.App.SetMacExitMenuItemId(wx.ID_EXIT)

    menuBar = wx.MenuBar()
    menuBar.Append(fileMenu, "&File")
    self.SetMenuBar(menuBar)

  ### File Menu

  def OnAppendBF(self, event):

    # Get the filename of the ballots to be appended
    dlg = wx.FileDialog(self, "Select Ballot File", os.getcwd(), "",
                        style=wx.OPEN|wx.CHANGE_DIR)
    if dlg.ShowModal() != wx.ID_OK:
      dlg.Destroy()
      return
    fName = dlg.GetPath()
    dlg.Destroy()

    # Attempt to load the ballots
    try:
      bb = Ballots.loadUnknown(fName)
    except RuntimeError, msg:
      wx.MessageBox(str(msg), "Error", wx.OK|wx.ICON_ERROR)
      return

    # Attempt to append the ballots
    try:
      self.b.append(bb)
    except RuntimeError, msg:
      wx.MessageBox(str(msg), "Error", wx.OK|wx.ICON_ERROR)
    else:
      self.Log("Appended %d ballots from file %s." %\
               (bb.nBallots, os.path.basename(bb.fName)))

    self.panel.NeedToSaveBallots = True
    self.panel.UpdatePanel()
    
  ###
      
  def OnSaveBallots(self, event):

    if self.b.fName == "":
      self.OnSaveBallotsAs(event)
      return

    try:
      self.b.save()
    except RuntimeError, msg:
      wx.MessageBox(str(msg), "Error", wx.OK|wx.ICON_ERROR)
      return
    self.panel.NeedToSaveBallots = False

  ###

  def OnSaveBallotsAs(self, event):

    # Ask the user to choose the filename.
    dlg = wx.FileDialog(self, "Save Ballot File", os.getcwd(), "",
                        style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR)
    if dlg.ShowModal() != wx.ID_OK:
      dlg.Destroy()
      return
    self.b.fName = dlg.GetPath()
    dlg.Destroy()

    # Save
    try:
      self.b.save()
    except RuntimeError, msg:
      wx.MessageBox(str(msg), "Error", wx.OK|wx.ICON_ERROR)
      return
    self.panel.NeedToSaveBallots = False

    # Set the window title to include the filename
    title = "%s - %s" % (os.path.basename(self.b.fName),
                         "Ballot File Editor")
    self.SetTitle(title)
    self.panel.UpdatePanel()

  ###

  def OnSaveLog(self, event):

    if self.logfName == "":
      self.OnSaveLogAs(event)
      return

    try:
      self.log.SaveFile(self.logfName)
    except RuntimeError, msg:
      wx.MessageBox(str(msg), "Error", wx.OK|wx.ICON_ERROR)
      return

    self.panel.NeedToSaveLog = False

  ###
    
  def OnSaveLogAs(self, event):
    dlg = wx.FileDialog(self, "Save Log to a File",
                        os.getcwd(), "", "All Files|*.*",
                        style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR)
    if dlg.ShowModal() != wx.ID_OK:
      dlg.Destroy()
      return
    self.logfName = dlg.GetPath()
    dlg.Destroy()

    try:
      self.log.SaveFile(self.logfName)
    except RuntimeError, msg:
      wx.MessageBox(str(msg), "Error", wx.OK|wx.ICON_ERROR)
      return

    self.panel.NeedToSaveLog = False

  ###
    
  def OnExit(self, event):
    self.Close()

  ### Other Event Handlers

  def OnCloseWindow(self, event):

    # Check to see if the current ballot is empty and warn user
    if len(self.b.raw[self.panel.i]) == 0:
      txt = "The current ballot is empty.  Ok to close editor?"
      code = wx.MessageBox(txt, "Warning", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
      if code == wx.CANCEL:
        # Don't exit
        event.Veto()
        return

    # Ask user if we should save ballots.
    if self.panel.NeedToSaveBallots == True:
      if self.b.fName == "":
        msg = "Do you want to save the ballots?"
      else:
        msg = "Do you want to save the ballots to %s?" % self.b.fName
      saveBallots = wx.MessageBox(msg, "Warning",
                                  wx.YES_NO|wx.CANCEL|wx.ICON_INFORMATION)
      if saveBallots == wx.CANCEL:
        event.Veto() # Don't exit
        return
      elif saveBallots == wx.YES:
        self.OnSaveBallots(None) # Save ballots

    # Ask user if we should save the log.
    if self.panel.NeedToSaveLog == True:
      msg = "Do you want to save the log for ballot file %s?" %\
            os.path.basename(self.b.fName)
      saveLog = wx.MessageBox(msg, "Warning",
                                  wx.YES_NO|wx.CANCEL|wx.ICON_INFORMATION)
      if saveLog == wx.CANCEL:
        event.Veto() # Don't exit
        return
      elif saveLog == wx.YES:
        self.OnSaveLog(None) # Save log

    self.Destroy()

####################

class PBFEFrame(BFE.BFEFrame):

  def __init__(self, parent, home, mode):
    wx.Frame.__init__(self, parent, -1, "Ballot File Editor")

    self.MakeMenu()
    self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
    self.logfName = ""

    fn = os.path.join(home, "Icons", "blt.ico")
    icon = wx.Icon(fn, wx.BITMAP_TYPE_ICO)
    self.SetIcon(icon)

    self.LoadBallotFile(mode, parent)
    
  def LoadBallotFile(self, mode, parent):
    # Create an empty ballots class instance
    self.b = ProjectBallots()
    
    if mode == "new":

      # Get the projects info from the user
      dlg = BFE.ProjectDialog(parent, self.b)
      dlg.Center()
      if dlg.ShowModal() != wx.ID_OK:
        dlg.Destroy()
        self.Destroy()
        return
      dlg.Destroy()
        
    # Edit an existing ballot file
    elif mode == "old":
      dlg = wx.FileDialog(self, "Select Project Ballot File", os.getcwd(), "",
                          style=wx.OPEN|wx.CHANGE_DIR)
      if dlg.ShowModal() != wx.ID_OK:
        dlg.Destroy()
        self.Destroy()
        return
      fName = dlg.GetPath()
      dlg.Destroy()

      # Open the file
      try:
        self.b.load(fName)
      except RuntimeError, msg:
        wx.MessageBox(str(msg), "Error", wx.OK|wx.ICON_ERROR)
        self.Destroy()
        return

    else:
      assert(0)

    # Set the window title to include the filename
    title = "%s - %s" % (os.path.basename(self.b.fName),
                         "Project Ballot File Editor")
    self.SetTitle(title)

    # Create a notebook with an editing page and a log page
    nb = wx.Notebook(self, -1)

    self.panel = BFE.BallotsPanel(nb, self.b)
    nb.AddPage(self.panel, "Ballots")

    self.logN = 1 # counter for display purposes
    self.log = wx.TextCtrl(nb, -1,
                           style=wx.TE_MULTILINE|wx.TE_READONLY|\
                           wx.TE_WORDWRAP|wx.FIXED)
    self.log.SetMaxLength(0)
    nb.AddPage(self.log, "Log")

    # Initialize
    if mode == "new":
      self.panel.NeedToSaveBallots = True
      self.Log("Created a new ballot file.")
    elif mode == "old":
      self.panel.NeedToSaveBallots = False
      self.Log("Loaded %d ballots from file %s." %\
               (self.b.nBallots, os.path.basename(self.b.fName)))
    else:
      assert(0)

    # Set up the sizer
    sizer = wx.BoxSizer()
    sizer.Add(nb, 1, wx.EXPAND, 0)
    self.SetSizer(sizer)
    sizer.Fit(self)
    sizer.SetSizeHints(self)

  ###

  def OnAppendBF(self, event):

    # Get the filename of the ballots to be appended
    dlg = wx.FileDialog(self, "Select Project Ballot File", os.getcwd(), "",
                        style=wx.OPEN|wx.CHANGE_DIR)
    if dlg.ShowModal() != wx.ID_OK:
      dlg.Destroy()
      return
    fName = dlg.GetPath()
    dlg.Destroy()

    # Attempt to load the ballots
    try:
      bb = ProjectBallots()
      bb.load(fName)
    except RuntimeError, msg:
      wx.MessageBox(str(msg), "Error", wx.OK|wx.ICON_ERROR)
      return

    # Attempt to append the ballots
    try:
      self.b.append(bb)
    except RuntimeError, msg:
      wx.MessageBox(str(msg), "Error", wx.OK|wx.ICON_ERROR)
    else:
      self.Log("Appended %d ballots from file %s." %\
               (bb.nBallots, os.path.basename(bb.fName)))

    self.panel.NeedToSaveBallots = True
    self.panel.UpdatePanel()

####################

class ProjectsDialog(wx.Dialog):

  def __init__(self, parent, b):
    wx.Dialog.__init__(self, parent, -1, "Projects")

    self.b = b

    # Explanation
    txt = wx.StaticText(self, -1, """\
Enter the candidates' names one by one.  To remove a candidate
whose name has already been entered, double click on the candidate's
name below.""")

    # Candidate entry
    candidateL = wx.StaticText(self, -1, "Candidate to add:")
    self.candidateC = wx.TextCtrl(self, -1, "", style=wx.TE_PROCESS_ENTER)
    self.Bind(wx.EVT_TEXT_ENTER, self.OnEnter, self.candidateC)
    candidateB = wx.Button(self, -1, "Add")
    self.Bind(wx.EVT_BUTTON, self.OnAdd, candidateB)

    # Candidate list
    listL = wx.StaticText(self, -1, "Candidates:")
    self.listC = wx.ListBox(self, -1, choices=self.b.names, size=(-1,100))
    self.Bind(wx.EVT_LISTBOX_DCLICK, self.OnListDClick, self.listC)
    blank = wx.StaticText(self, -1, "")

    # Buttons
    ok = wx.Button(self, wx.ID_OK)
    self.Bind(wx.EVT_BUTTON, self.OnOK, ok)
    cancel = wx.Button(self, wx.ID_CANCEL)

    # Sizers
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(txt, 0, wx.ALL, 5)
    sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)

    fgs = wx.FlexGridSizer(2, 3, 5, 5)
    fgs.Add(candidateL, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
    fgs.Add(self.candidateC, 0, wx.EXPAND)
    fgs.Add(candidateB, 0)
    fgs.Add(listL, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
    fgs.Add(self.listC, 0, wx.EXPAND)
    fgs.Add(blank, 0)
    fgs.AddGrowableCol(1)

    sizer.Add(fgs, 0, wx.EXPAND|wx.ALL, 5)
    bs = wx.StdDialogButtonSizer()
    bs.AddButton(ok)
    bs.AddButton(cancel)
    bs.Realize()
    sizer.Add(bs, 0, wx.EXPAND|wx.ALL, 5)

    self.SetSizer(sizer)
    sizer.Fit(self)

  ###

  def OnOK(self, event):
    # Check to see if name is entered and not added
    name = self.candidateC.GetValue().strip()
    if name == "":
      event.Skip()
    else:
      wx.MessageBox("Name entered but not added.  Please hit the 'Add' "
                    "button or clear the name in the text box to continue.",
                    "Message", wx.OK|wx.ICON_INFORMATION)

  ###

  def OnEnter(self, event):
    self.OnAdd(event)
    
  ###

  def OnAdd(self, event):
    # Get the name in the text box
    name = self.candidateC.GetValue().strip()
    # Add the name to the ballots instance and update the list control
    if name not in self.b.names:
      self.b.names.append(name)
      self.b.nCand = len(self.b.names)
      self.listC.Set(self.b.names)
    else:
      wx.MessageBox("Can't have two candidates with the same name.",
                    "Error", wx.OK|wx.ICON_ERROR)
    # Clear the text box to allow user to enter another name
    self.candidateC.Clear()
    self.candidateC.SetFocus()
    
  ###

  def OnListDClick(self, event):
    # Remove the candidate from the ballots instance and update the control
    c = self.listC.GetSelection()
    self.b.names.pop(c)
    self.b.nCand = len(self.b.names)
    self.listC.Set(self.b.names)

####################

# replacing the various edited stuff in BFE.py
BFE.BFEFrame = MyBFEFrame
BFE.PBFEFrame = PBFEFrame
BFE.ProjectsDialog = ProjectsDialog

##################################################################
### OpenSTV.py monkey patching ###

class MyFrame(wx.Frame):

  def __init__(self, parent):
    wx.Frame.__init__(self, parent, -1, "OpenSTV (with MMV support)", size=(900,600))

    warnings.showwarning = self.catchWarnings

    fn = os.path.join(OpenSTV.HOME, "Icons", "pie.ico")
    icon = wx.Icon(fn, wx.BITMAP_TYPE_ICO)
    self.SetIcon(icon)

    self.TallyList = []
    self.MakeMenu()
    self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    # create a notebook
    self.notebook = wx.Notebook(self, -1)

    # create a console window
    self.console = wx.TextCtrl(self.notebook, -1,
                               style=wx.TE_MULTILINE|wx.TE_READONLY|\
                               wx.TE_WORDWRAP|wx.FIXED|wx.TE_RICH2)
    self.console.SetMaxLength(0)
    ps = self.console.GetFont().GetPointSize()
    font = wx.Font(ps, wx.MODERN, wx.NORMAL, wx.NORMAL)
    self.console.SetFont(font)

    # add the console as the first page
    self.notebook.AddPage(self.console, "Console")
    self.output = OpenSTV.Output(self.notebook)
    #sys.stdout = self.output
    #sys.stderr = self.output

    self.introText = """\
OpenSTV Copyright (C) 2003-2009 Jeffrey O'Neill
GNU General Public License
See Help->License for more details.

To run an election with an exsting ballot file, select "New Election" from
the File menu.

To create a new ballot file, select"Create New Ballot File" from the File
menu.  To edit an existing ballot file, select "Edit Ballot File" from the
File menu.

For more information about the operation of OpenSTV, see the Help menu, go
to www.OpenSTV.org, or send an email to OpenSTV@googlegroups.com.    
"""
    self.console.AppendText(self.introText)

    #os.chdir(wx.StandardPaths.Get().GetDocumentsDir())

  ###
    
  def catchWarnings(self, message, category, filename, lineno):
    "Catch any warnings and display them in a dialog box."
    
    wx.MessageBox(str(message), "Warning", wx.OK|wx.ICON_INFORMATION)

  ###

  def MakeMenu(self):

    self.menuBar = wx.MenuBar()

    # File menu
    FileMenu = wx.Menu()
    self.AddMenuItem(FileMenu, 'New Election...',
                     'New Election...', self.OnNewElection)
    FileMenu.AppendSeparator()
    self.AddMenuItem(FileMenu, 'Create New Ballot File...',
                     'Create New Ballot File...', self.OnNewBF)
    self.AddMenuItem(FileMenu, 'Edit Ballot File...',
                     'Edit Ballot File...', self.OnEditBF)
    FileMenu.AppendSeparator()
    self.AddMenuItem(FileMenu, 'Create New Project Ballot File...',
                     'Create New Project Ballot File...', self.OnNewProjectBF)
    self.AddMenuItem(FileMenu, 'Edit Project Ballot File...',
                     'Edit Project Ballot File...', self.OnEditProjectBF)
    FileMenu.AppendSeparator()
    id = self.AddMenuItem(FileMenu, 'Exit',
                     'Exit the application', self.OnExit, "Exit")
    if wx.Platform == "__WXMAC__":
       wx.App.SetMacExitMenuItemId(id)
    self.menuBar.Append(FileMenu, '&File')

    # Edit menu
    EditMenu = wx.Menu()
    self.AddMenuItem(EditMenu, 'Copy', 'Copy', self.OnCopy)
    self.AddMenuItem(EditMenu, 'Select All', 'Select All', self.OnSelectAll)
    self.menuBar.Append(EditMenu, '&Edit')

    # Results menu
    ResultsMenu = wx.Menu()

    self.AddMenuItem(ResultsMenu, 'Delete Tab', 'Delete Tab',
                     self.OnDeleteTab)

    subMenu = wx.Menu()
    self.AddMenuItem(subMenu, '6', '6', self.OnFontSize)
    self.AddMenuItem(subMenu, '7', '7', self.OnFontSize)
    self.AddMenuItem(subMenu, '8', '8', self.OnFontSize)
    self.AddMenuItem(subMenu, '9', '9', self.OnFontSize)
    self.AddMenuItem(subMenu, '10', '10', self.OnFontSize)
    self.AddMenuItem(subMenu, '11', '11', self.OnFontSize)
    self.AddMenuItem(subMenu, '12', '12', self.OnFontSize)
    self.AddMenuItem(subMenu, '13', '13', self.OnFontSize)
    self.AddMenuItem(subMenu, '14', '14', self.OnFontSize)
    ResultsMenu.AppendMenu(wx.NewId(), "Font Size", subMenu)

    ResultsMenu.AppendSeparator()
    self.AddMenuItem(ResultsMenu, 'Save Results as CSV...',
                     'Save results as CSV', self.OnSaveResultsCSV)
    self.AddMenuItem(ResultsMenu, 'Save Results as text...',
                     'Save results as text', self.OnSaveResultsText)
    self.AddMenuItem(ResultsMenu, 'Save Results as HTML...',
                     'Save results as HTML', self.OnSaveResultsHTML)

    self.menuBar.Append(ResultsMenu, '&Results')
    
    # Help menu
    HelpMenu = wx.Menu()
    self.AddMenuItem(HelpMenu, 'OpenSTV Help',
                     'OpenSTV Help', self.OnHelp, "Help")
    self.AddMenuItem(HelpMenu, 'Method Details',
                     'Method Details', self.OnDetails)
    self.AddMenuItem(HelpMenu, 'License',
                     'GNU General Public License', self.OnLicense)
    if wx.Platform != "__WXMAC__":
      HelpMenu.AppendSeparator()
    id = self.AddMenuItem(HelpMenu, '&About', 'About OpenSTV', self.OnAbout, "About")
    if wx.Platform == "__WXMAC__":
      wx.App.SetMacAboutMenuItemId(id)
    self.menuBar.Append(HelpMenu, '&Help')
    if wx.Platform == "__WXMAC__":
      wx.GetApp().SetMacHelpMenuTitleName('&Help')

    self.SetMenuBar(self.menuBar)

  ###
  
  def AddMenuItem(self, menu, itemText, itemDescription, itemHandler, opt=''):
    if (opt == "Exit"):
      menuId = wx.ID_EXIT
    elif (opt == "Help"):
      menuId = wx.ID_HELP
    elif (opt == "About"):
      menuId = wx.ID_ABOUT
    else:
      menuId = wx.ID_ANY

    if opt == "Radio":
      item = menu.Append(menuId, itemText, itemDescription, wx.ITEM_RADIO)
    elif opt == "Check":
      item = menu.Append(menuId, itemText, itemDescription, wx.ITEM_CHECK)
    else:
      item = menu.Append(menuId, itemText, itemDescription)
    self.Bind(wx.EVT_MENU, itemHandler, item)
    return item.GetId()

  ### File Menu
    
  def OnNewElection(self, event):

    # Get the ballot filename and election method
    dlg = OpenSTV.ElectionMethodFileDialog(self)
    dlg.Center()
    if dlg.ShowModal() != wx.ID_OK:
      dlg.Destroy()
      return
    filename = dlg.filename
    method = dlg.method
    dlg.Destroy()

    # Load the ballot file and create an election instance
    try:
      if method == "ProjectElection":        
        b = ProjectBallots()
        b.load(filename)
      else:
        b = Ballots.loadUnknown(filename)
      cmd = "%s(b)" % method
      e = eval(cmd)
      T = OpenSTV.Tally(e)
    except RuntimeError, msg:
      wx.MessageBox(str(msg), "Error", wx.OK|wx.ICON_ERROR)
      return

    # Get info and options
    if method == "ProjectElection":
      dlg = OpenSTV.ProjectElectionOptionsDialog(self, T)
    else:
      dlg = OpenSTV.ElectionOptionsDialog(self, T)
    dlg.Center()
    if dlg.ShowModal() != wx.ID_OK:
      dlg.Destroy()
      return
    dlg.Destroy()

    # Run the election
    try:
      T.runElection()
      txt = T.generateTextOutput()
    except RuntimeError, msg:
      wx.MessageBox(str(msg), "Error", wx.OK|wx.ICON_ERROR)
      return
      
    self.TallyList.append(T)

    # create a new notebook page
    tc = wx.TextCtrl(self.notebook, -1,
                     style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL|wx.FIXED)
    tc.SetMaxLength(0)
    ps = tc.GetFont().GetPointSize()
    font = wx.Font(ps, wx.MODERN, wx.NORMAL, wx.NORMAL)
    tc.SetFont(font)
    self.notebook.AddPage(tc, T.e.title)
    page = self.notebook.GetPageCount() - 1
    self.notebook.SetSelection(page)
    self.notebook.GetPage(page).ChangeValue(txt)

  ###
    
  def OnNewBF(self, event):
    window = BFE.BFEFrame(self, OpenSTV.HOME, "new")
    window.Show(True)

  ###
    
  def OnNewProjectBF(self, event):
    window = BFE.PBFEFrame(self, OpenSTV.HOME, "new")
    window.Show(True)
  
  ###
    
  def OnEditBF(self, event):
    window = BFE.BFEFrame(self, OpenSTV.HOME, "old")
    window.Show(True)

  ###
    
  def OnEditProjectBF(self, event):
    window = BFE.PBFEFrame(self, OpenSTV.HOME, "old")
    window.Show(True)
  
  ###
    
  def OnExit(self, event):
    self.Close()

  ###

  def OnCloseWindow(self, event):
    childrenList = self.GetChildren()
    for child in childrenList:
      # If the child is a frame, then it is a BFE
      if child.GetClassName() == "wxFrame":
        # Try to close the child, this will return true if the user selects
        # "yes" or "no" and false if the user selects "cancel"
        if not child.Close():
          break
    else:
      # This only happens if the user did not select cancel for any BFE
      self.Destroy()

  ### Edit Menu

  def OnCopy(self, event):
    n = self.notebook.GetSelection()
    text = self.notebook.GetPage(n).GetStringSelection()
    do = wx.TextDataObject()
    do.SetText(text)
    wx.TheClipboard.Open()
    wx.TheClipboard.SetData(do)
    wx.TheClipboard.Close()

  ###

  def OnSelectAll(self, event):
    n = self.notebook.GetSelection()
    self.notebook.GetPage(n).SetSelection(-1, -1)
    
  ### Results Menu Methods

  def OnDeleteTab(self, event):
    
    n = self.notebook.GetSelection()
    if n == 0:
      wx.MessageBox("Can't delete the Console.", "Error", wx.OK|wx.ICON_ERROR)
      return

    dlg = wx.MessageDialog(self, 'Delete current tab?', 'Warning',
                           wx.YES_NO | wx.ICON_INFORMATION)
    response = dlg.ShowModal()
    dlg.Destroy()
    if response != wx.ID_YES:
      return

    # The index into TallyList is off by one because of the console tab
    self.notebook.DeletePage(n)
    self.TallyList.pop(n-1)

  ###

  def OnFontSize(self, event):
    id = event.GetId()
    fontSize = int(self.menuBar.FindItemById(id).GetLabel())
    n = self.notebook.GetSelection()
    font = self.notebook.GetPage(n).GetFont()
    font.SetPointSize(fontSize)
    self.notebook.GetPage(n).SetFont(font)

  ###

  def OnSaveResultsCSV(self, event):

    n = self.notebook.GetSelection()
    if n == 0:
      wx.MessageBox("Please select a tab containing election results.",
                    "Message", wx.OK|wx.ICON_INFORMATION)
      return
    T = self.TallyList[n-1]

    if T.e.method == "Condorcet":
      wx.MessageBox("Not available for this method.",
                    "Message", wx.OK|wx.ICON_INFORMATION)
      return

    dlg = wx.FileDialog(self, "Save Results in CSV Format",
                        os.getcwd(), "", "All Files|*.*",
                        style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR)
    if dlg.ShowModal() != wx.ID_OK:
      dlg.Destroy()
      return
    fName = dlg.GetPath()
    dlg.Destroy()

    csv = T.generateERSCSVOutput()
    f = open(fName, 'w')
    f.write(csv)
    f.close()
    
  ###

  def OnSaveResultsText(self, event):

    n = self.notebook.GetSelection()
    if n == 0:
      wx.MessageBox("Please select a tab containing election results.",
                    "Message", wx.OK|wx.ICON_INFORMATION)
      return
    T = self.TallyList[n-1]

    dlg = wx.FileDialog(self, "Save Results in Text Format",
                        os.getcwd(), "", "All Files|*.*",
                        style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR)
    if dlg.ShowModal() != wx.ID_OK:
      dlg.Destroy()
      return
    fName = dlg.GetPath()
    dlg.Destroy()

    n = self.notebook.GetSelection()
    text = self.notebook.GetPage(n).SaveFile(fName)

  ###

  def OnSaveResultsHTML(self, event):

    n = self.notebook.GetSelection()
    if n == 0:
      wx.MessageBox("Please select a tab containing election results.",
                    "Message", wx.OK|wx.ICON_INFORMATION)
      return
    T = self.TallyList[n-1]

    dlg = wx.FileDialog(self, "Save Results in HTML Format",
                        os.getcwd(), "", "All Files|*.*",
                        style=wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR)
    if dlg.ShowModal() != wx.ID_OK:
      dlg.Destroy()
      return
    fName = dlg.GetPath()
    dlg.Destroy()

    html = T.generateHTMLOutput()
    f = open(fName, 'w')
    f.write(html)
    f.close()

  ### Help Menu

  def OnAbout(self, event):
    dlg = OpenSTV.AboutDialog(self)
    dlg.Center()
    dlg.ShowModal()
    dlg.Destroy()

  ###

  def OnDetails(self, event):
    frame = OpenSTV.HTMLFrame(self, "Method Details", "Details.html")
    frame.Show(True)

  ###

  def OnHelp(self, event):
    frame = OpenSTV.HTMLFrame(self, "OpenSTV Help", "Help.html")
    frame.Show(True)

  ###

  def OnLicense(self, event):
    frame = OpenSTV.HTMLFrame(self, "GNU General Public License", "License.html")
    frame.Show(True)

######

class MyElectionMethodFileDialog(wx.Dialog):

  def __init__(self, parent):
    wx.Dialog.__init__(self, parent, -1, "Select Input File and Method")

    # Explanation
    txt = wx.StaticText(self, -1, """\
To run an election, choose the input filename and the election method.
See the Help menu for more information about the available methods.""")

    # The English description of methods and corresponding class name
    self.methods = {
      "Movable Money Voting" : "ProjectElection",
      "Single Non-Transferable Vote" : "SNTV",
      "Approval Method" : "Approval",
      "Borda Count" : "Borda",
      "Bucklin System" : "Bucklin",
      "Condorcet's Method" : "Condorcet",
      "Instant Runoff Voting" : "IRV",
      "Supplemental Vote" : "SuppVote",
      "Coombs Method" : "Coombs",
      "Cambridge STV" : "CambridgeSTV",
      "ERS97 STV" : "ERS97STV",
      "N. Ireland STV" : "NIrelandSTV",
      "Scottish STV" : "ScottishSTV",
      "Green Party California STV": "GPCA2000STV",
      "Random Transfer STV" : "RTSTV",
      "Fractional Transfer STV" : "FTSTV",
      "Meek STV" : "MeekSTV",
      "Warren STV" : "WarrenSTV",
      "MeekX STV" : "MeekXSTV",
      "WarrenX STV" : "WarrenXSTV"
      }

    # Controls
    filenameL = wx.StaticText(self, -1, "Filename:")
    self.filenameC = wx.TextCtrl(self, -1, "")
    filenameB = wx.Button(self, -1, "Select...", (50,50))
    self.Bind(wx.EVT_BUTTON, self.OnFilenameSelect, filenameB)

    methodL = wx.StaticText(self, -1, "Method:")
    choices = self.methods.keys()
    choices.sort()
    self.methodC = wx.Choice(self, -1, choices = choices)
    self.methodC.SetStringSelection("Scottish STV")
    blank = wx.StaticText(self, -1, "")

    # Buttons
    ok = wx.Button(self, wx.ID_OK)
    self.Bind(wx.EVT_BUTTON, self.OnOK, ok)
    cancel = wx.Button(self, wx.ID_CANCEL)

    # Sizers
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(txt, 0, wx.ALL, 5)
    sizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5)

    fgs = wx.FlexGridSizer(2, 3, 5, 5)
    fgs.Add(filenameL, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
    fgs.Add(self.filenameC, 0, wx.EXPAND)
    fgs.Add(filenameB, 0)
    fgs.Add(methodL, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
    fgs.Add(self.methodC, 0, wx.EXPAND)
    fgs.Add(blank, 0)
    fgs.AddGrowableCol(1)

    sizer.Add(fgs, 0, wx.EXPAND|wx.ALL, 5)
    bs = wx.StdDialogButtonSizer()
    bs.AddButton(ok)
    bs.AddButton(cancel)
    bs.Realize()
    sizer.Add(bs, 0, wx.EXPAND|wx.ALL, 5)

    self.SetSizer(sizer)
    sizer.Fit(self)

  def OnFilenameSelect(self, event):
    dlg = wx.FileDialog(self, "Select Input File", os.getcwd(), "",
                        style=wx.OPEN|wx.CHANGE_DIR)
    if dlg.ShowModal() != wx.ID_OK:
      dlg.Destroy()
      return
    filename = dlg.GetPath()
    dlg.Destroy()
    self.filenameC.ChangeValue(filename)

  def OnOK(self, event):

    # Get filename
    self.filename = self.filenameC.GetValue().strip()
    if self.filename == "":
      wx.MessageBox("Please select a filename.", "Message",
                    wx.OK|wx.ICON_INFORMATION)
      return

    # Get method name and convert to class
    key = self.methodC.GetStringSelection()
    self.method = self.methods[key]

    event.Skip() # do normal OK button processing

##########

class ProjectElectionOptionsDialog(wx.Dialog):

  def __init__(self, parent, T):
    wx.Dialog.__init__(self, parent, -1, "Election Options")

    self.T = T

    # Controls for all elections
    method1L = wx.StaticText(self, -1, "Method:")
    method2L = wx.StaticText(self, -1, self.T.e.method)

    file1L = wx.StaticText(self, -1, "File:")
    file2L = wx.StaticText(self, -1, os.path.basename(self.T.e.b.fName))

    nBallots1L = wx.StaticText(self, -1, "Number of ballots:")
    nBallots2L = wx.StaticText(self, -1, str(self.T.e.b.nBallots))

    titleL = wx.StaticText(self, -1, "Title:")
    self.titleC = wx.TextCtrl(self, -1, "")
    self.titleC.SetValue(self.T.e.title)

    dateL = wx.StaticText(self, -1, "Date:")
    self.dateC = wx.TextCtrl(self, -1, "")
    self.dateC.SetValue(self.T.e.date)

    resourcesL = wx.StaticText(self, -1, "Resources:")
    self.resourcesC = wx.SpinCtrl(self, -1)
    self.resourcesC.SetRange(1, 9999999)
    self.resourcesC.SetValue(self.T.e.b.nResources)

    widthL = wx.StaticText(self, -1, "Display Width:")
    self.widthC = wx.SpinCtrl(self, -1)
    self.widthC.SetRange(0, 200)
    self.widthC.SetValue(self.T.dispWidth)

    # Withdraw projects
    withdrawTxt = wx.StaticText(self, -1, """\
Projects with "W" in the first column are withdrawn.  Double
click on a project's name to change the status of the project.\
""")
    self.withdrawC = OpenSTV.WithdrawCtrl(self, -1)
    self.withdrawC.InsertColumn(0, "W")
    self.withdrawC.InsertColumn(1, "Project")
    for c, name in enumerate(self.T.e.b.names):
      if c in self.T.e.withdrawn:
        self.withdrawC.InsertStringItem(c, "W")
      else:
        self.withdrawC.InsertStringItem(c, "")
      self.withdrawC.SetStringItem(c, 1, name)
    self.withdrawC.SetColumnWidth(0, wx.LIST_AUTOSIZE_USEHEADER)
    self.withdrawC.SetColumnWidth(1, wx.LIST_AUTOSIZE_USEHEADER)

    self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnListDClick,
              self.withdrawC)

    # Method options
    labelList = []
    ctrlList = []

    # precision
#    if self.T.e.method in ["MMV"]:
#      precL = wx.StaticText(self, -1, "Precision:")
#      self.precC = wx.SpinCtrl(self, -1)
#      self.precC.SetRange(0, 20)
#      self.precC.SetValue(self.T.e.prec)
#      labelList.append(precL)
#      ctrlList.append(self.precC)

    # threshold
#    if self.T.e.method in ["MMV"]:
#      thresh1L = wx.StaticText(self, -1, "")
#      choices = ["Dynamic", "Static"]
#      self.thresh1C = wx.Choice(self, -1, choices = choices)
#      self.thresh1C.SetStringSelection(self.T.e.threshName[1])
#      labelList.append(thresh1L)
#      ctrlList.append(self.thresh1C)
#      thresh2L = wx.StaticText(self, -1, "")
#      choices = ["Whole", "Fractional"]
#      self.thresh2C = wx.Choice(self, -1, choices = choices)
#      self.thresh2C.SetStringSelection(self.T.e.threshName[2])
#      labelList.append(thresh2L)
#      ctrlList.append(self.thresh2C)

    # Buttons
    ok = wx.Button(self, wx.ID_OK)
    self.Bind(wx.EVT_BUTTON, self.OnOK, ok)
    cancel = wx.Button(self, wx.ID_CANCEL)

    # Sizers
    sizer = wx.BoxSizer(wx.VERTICAL)

    # Election information
    informationBox = wx.StaticBox(self, -1, "Election Information")
    informationSizer = wx.StaticBoxSizer(informationBox, wx.VERTICAL)
    sizer.Add(informationSizer, 0, wx.EXPAND|wx.ALL, 5)

    fgs = wx.FlexGridSizer(7, 2, 5, 5)
    fgs.Add(method1L, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
    fgs.Add(method2L, 0, wx.EXPAND)
    fgs.Add(file1L, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
    fgs.Add(file2L, 0, wx.EXPAND)
    fgs.Add(nBallots1L, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
    fgs.Add(nBallots2L, 0, wx.EXPAND)
    fgs.Add(titleL, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
    fgs.Add(self.titleC, 0, wx.EXPAND)
    fgs.Add(dateL, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
    fgs.Add(self.dateC, 0, wx.EXPAND)
    fgs.Add(resourcesL, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
    fgs.Add(self.resourcesC, 0, wx.EXPAND)
    fgs.Add(widthL, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
    fgs.Add(self.widthC, 0, wx.EXPAND)
    fgs.AddGrowableCol(1)
    informationSizer.Add(fgs, 0, wx.EXPAND|wx.ALL, 5)

    # Withdraw projects
    withdrawBox = wx.StaticBox(self, -1, "Withdraw Projects")
    withdrawSizer = wx.StaticBoxSizer(withdrawBox, wx.VERTICAL)
    sizer.Add(withdrawSizer, 0, wx.EXPAND|wx.ALL, 5)

    withdrawSizer.Add(withdrawTxt, 0, wx.ALL, 5)
    withdrawSizer.Add(self.withdrawC, 0, wx.EXPAND|wx.ALL, 5)    
    
    # Method specific options
    n = len(labelList)
    if n > 0:
      optionsBox = wx.StaticBox(self, -1, "Method Options")
      optionsSizer = wx.StaticBoxSizer(optionsBox, wx.VERTICAL)
      sizer.Add(optionsSizer, 0, wx.EXPAND|wx.ALL, 5)

      fgs = wx.FlexGridSizer(n, 2, 5, 5)
      for i in range(n):
        fgs.Add(labelList[i], 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        fgs.Add(ctrlList[i], 0, wx.EXPAND)
      fgs.AddGrowableCol(1)
      optionsSizer.Add(fgs, 0, wx.EXPAND|wx.ALL, 5)

    # Buttons
    bs = wx.StdDialogButtonSizer()
    bs.AddButton(ok)
    bs.AddButton(cancel)
    bs.Realize()
    sizer.Add(bs, 0, wx.EXPAND|wx.ALL, 5)

    self.SetSizer(sizer)
    sizer.Fit(self)

  def OnBatchElimination(self, event):
    if self.batchEliminationC.GetStringSelection() == "Cutoff":
      self.batchCutoffC.Enable(True)
    else:
      self.batchCutoffC.Enable(False)

  def OnListDClick(self, event):
    withdrawC = event.GetEventObject()
    c = event.m_itemIndex
    if c in self.T.e.withdrawn:
      self.T.e.withdrawn.remove(c)
      withdrawC.SetStringItem(c, 0, "")
    else:
      self.T.e.withdrawn.append(c)
      withdrawC.SetStringItem(c, 0, "W")
      
  def OnOK(self, event):
    self.T.e.title = self.titleC.GetValue()
    self.T.e.date = self.dateC.GetValue()
    self.T.e.b.nResources = self.resourcesC.GetValue()
    self.T.dispWidth = self.widthC.GetValue()
    if vars(self).has_key("precC"):
      self.T.e.setOptions(prec=self.precC.GetValue())
    if vars(self).has_key("ballotCompletionC"):
      value = self.ballotCompletionC.GetStringSelection() == "On"
      self.T.e.setOptions(ballotCompletion=value)
    if vars(self).has_key("completionMethodC"):
      self.T.e.setOptions(completion=self.completionMethodC.GetStringSelection())
    if vars(self).has_key("thresh0C"):
      value0 = self.thresh0C.GetStringSelection()
      value1 = self.thresh1C.GetStringSelection()
      if vars(self).has_key("thresh2C"):
        value2 = self.thresh2C.GetStringSelection()
      else:
        value2 = "Whole"
      self.T.e.setOptions(threshName=(value0, value1, value2))
    if vars(self).has_key("delayedTransferC"):
      self.T.e.setOptions(delayedTransfer=self.delayedTransferC.GetStringSelection())
    if vars(self).has_key("batchEliminationC"):
      self.T.e.setOptions(batchElimination=self.batchEliminationC.GetStringSelection())
    if vars(self).has_key("batchCutoffC"):
      self.T.e.setOptions(batchCutoff=self.batchCutoffC.GetValue())
    event.Skip() # do normal OK button processing
    
#########
# replacing the various edited stuff in OpenSTV.py
OpenSTV.Frame = MyFrame
OpenSTV.ProjectElectionOptionsDialog = ProjectElectionOptionsDialog
OpenSTV.ElectionMethodFileDialog = MyElectionMethodFileDialog

##################################################################
### the actual run code from OpenSTV.py

if __name__ == '__main__':
 app = OpenSTV.App(0)
 app.MainLoop()
