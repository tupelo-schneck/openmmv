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

import version
from BFE import *
from  NonSTV import *
from STV import *
from ballots import *
from LER import *

# Path to OpenSTV application.  Used for accessing files.
HOME = ""

##################################################################

# This is used to capture stdout/stderr from STV.py and send
# it to a wxPython window.

class Output:
  def __init__(self, nb):
    self.nb = nb
  def write(self, txt):
    self.nb.GetCurrentPage().AppendText(txt)

##################################################################

class Tally():
  
  def __init__(self, e):
    self.dispWidth = 120
    self.e = e

  def runElection(self):
    self.e.runElection()
    
  def generateTextOutput(self):
    txt = self.e.generateTextResults(self.dispWidth)
    return txt

  def generateERSCSVOutput(self):
    csv = self.e.generateERSCSVResults()
    return csv

  def generateHTMLOutput(self):
    html = self.e.generateHTMLResults()
    return html
    
##################################################################

class Frame(wx.Frame):

  def __init__(self, parent):
    wx.Frame.__init__(self, parent, -1, "OpenSTV", size=(900,600))

    warnings.showwarning = self.catchWarnings

    fn = os.path.join(HOME, "Icons", "pie.ico")
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
    self.output = Output(self.notebook)
    sys.stdout = self.output
    sys.stderr = self.output

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

    os.chdir(wx.StandardPaths.Get().GetDocumentsDir())

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
    self.AddMenuItem(FileMenu, 'Create New Ballot File...',
                     'Create New Ballot File...', self.OnNewBF)
    self.AddMenuItem(FileMenu, 'Edit Ballot File...',
                     'Edit Ballot File...', self.OnEditBF)
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
    dlg = ElectionMethodFileDialog(self)
    dlg.Center()
    if dlg.ShowModal() != wx.ID_OK:
      dlg.Destroy()
      return
    filename = dlg.filename
    method = dlg.method
    dlg.Destroy()

    # Load the ballot file and create an election instance
    try:
      b = Ballots.loadUnknown(filename)
      cmd = "%s(b)" % method
      e = eval(cmd)
      T = Tally(e)
    except RuntimeError, msg:
      wx.MessageBox(str(msg), "Error", wx.OK|wx.ICON_ERROR)
      return

    # Get info and options
    dlg = ElectionOptionsDialog(self, T)
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
    BFE = BFEFrame(self, HOME, "new")
    BFE.Show(True)
  
  ###
    
  def OnEditBF(self, event):
    BFE = BFEFrame(self, HOME, "old")
    BFE.Show(True)
  
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
    dlg = AboutDialog(self)
    dlg.Center()
    dlg.ShowModal()
    dlg.Destroy()

  ###

  def OnDetails(self, event):
    frame = HTMLFrame(self, "Method Details", "Details.html")
    frame.Show(True)

  ###

  def OnHelp(self, event):
    frame = HTMLFrame(self, "OpenSTV Help", "Help.html")
    frame.Show(True)

  ###

  def OnLicense(self, event):
    frame = HTMLFrame(self, "GNU General Public License", "License.html")
    frame.Show(True)

##################################################################

class ElectionMethodFileDialog(wx.Dialog):

  def __init__(self, parent):
    wx.Dialog.__init__(self, parent, -1, "Select Input File and Method")

    # Explanation
    txt = wx.StaticText(self, -1, """\
To run an election, choose the input filename and the election method.
See the Help menu for more information about the available methods.""")

    # The English description of methods and corresponding class name
    self.methods = {
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
      "WarrenX STV" : "WarrenXSTV",
      "LERa" : "LERa",
      "LERb" : "LERb",
      "LERab" : "LERab"
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

##################################################################

class WithdrawCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
  
  def __init__(self, parent, ID):
    style = wx.LC_REPORT|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES
    wx.ListCtrl.__init__(self, parent, ID, style=style, size=(-1,100))
    listmix.ListCtrlAutoWidthMixin.__init__(self)

##################################################################

class ElectionOptionsDialog(wx.Dialog):

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

    seatsL = wx.StaticText(self, -1, "Seats:")
    self.seatsC = wx.SpinCtrl(self, -1)
    self.seatsC.SetRange(1, len(self.T.e.b.names)-1)
    self.seatsC.SetValue(self.T.e.nSeats)
    if self.T.e.method in ["Bucklin", "Condorcet", "Supplemental Vote"]:
      self.seatsC.SetValue(1)
      self.seatsC.Enable(False)


    widthL = wx.StaticText(self, -1, "Display Width:")
    self.widthC = wx.SpinCtrl(self, -1)
    self.widthC.SetRange(0, 200)
    self.widthC.SetValue(self.T.dispWidth)

    # Withdraw candidates
    withdrawTxt = wx.StaticText(self, -1, """\
Candidates with "W" in the first column are withdrawn.  Double
click on a candidate's name to change the status of the candidate.\
""")
    self.withdrawC = WithdrawCtrl(self, -1)
    self.withdrawC.InsertColumn(0, "W")
    self.withdrawC.InsertColumn(1, "Candidate")
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
    if self.T.e.method in ["Fractional Transfer STV",
                           "MeekX STV", "WarrenX STV",
                           "Meek STV", "Warren STV"]:
      precL = wx.StaticText(self, -1, "Precision:")
      self.precC = wx.SpinCtrl(self, -1)
      self.precC.SetRange(0, 20)
      self.precC.SetValue(self.T.e.prec)
      labelList.append(precL)
      ctrlList.append(self.precC)

    # ballot completion
    if self.T.e.method == "Borda":
      ballotCompletionL = wx.StaticText(self, -1, "Ballot completion:")
      choices = ["Off", "On"]
      self.ballotCompletionC = wx.Choice(self, -1, choices = choices)
      if self.T.e.ballotCompletion == True:
        self.ballotCompletionC.SetStringSelection("On")
      else:
        self.ballotCompletionC.SetStringSelection("Off")        
      labelList.append(ballotCompletionL)
      ctrlList.append(self.ballotCompletionC)

    # Condorcet completion method
    if self.T.e.method == "Condorcet":
      completionMethodL = wx.StaticText(self, -1, "Completion method:")
      choices = ["Borda on Smith Set",
                 "IRV on Smith Set",
                 "Schwartz Sequential Dropping"]
      self.completionMethodC = wx.Choice(self, -1, choices = choices)
      self.completionMethodC.SetStringSelection(self.T.e.completion)
      labelList.append(completionMethodL)
      ctrlList.append(self.completionMethodC)

    # threshold
    if self.T.e.method in ["Random Transfer STV", "Fractional Transfer STV",
                           "Meek STV", "Warren STV"]:
      thresh0L = wx.StaticText(self, -1, "Threshold:")
      choices = ["Droop", "Hare"]
      self.thresh0C = wx.Choice(self, -1, choices = choices)
      self.thresh0C.SetStringSelection(self.T.e.threshName[0])
      labelList.append(thresh0L)
      ctrlList.append(self.thresh0C)
      thresh1L = wx.StaticText(self, -1, "")
      choices = ["Dynamic", "Static"]
      self.thresh1C = wx.Choice(self, -1, choices = choices)
      self.thresh1C.SetStringSelection(self.T.e.threshName[1])
      labelList.append(thresh1L)
      ctrlList.append(self.thresh1C)
      if self.T.e.method != "Random Transfer STV":
        thresh2L = wx.StaticText(self, -1, "")
        choices = ["Whole", "Fractional"]
        self.thresh2C = wx.Choice(self, -1, choices = choices)
        self.thresh2C.SetStringSelection(self.T.e.threshName[2])
        labelList.append(thresh2L)
        ctrlList.append(self.thresh2C)

    # delayed transfer of surplus and batch elimination
    if self.T.e.method in ["Random Transfer STV", "Fractional Transfer STV"]:
      delayedTransferL = wx.StaticText(self, -1, "Delay Surplus Tansfer:")
      choices = ["Off", "On"]
      self.delayedTransferC = wx.Choice(self, -1, choices = choices)
      if self.T.e.delayedTransfer:
        self.delayedTransferC.SetStringSelection("On")
      else:
        self.delayedTransferC.SetStringSelection("Off")
      labelList.append(delayedTransferL)
      ctrlList.append(self.delayedTransferC)
      batchEliminationL = wx.StaticText(self, -1, "Batch elimination:")
      choices = ["None", "Zero", "Losers", "Cutoff"]
      self.batchEliminationC = wx.Choice(self, -1, choices = choices)
      self.batchEliminationC.SetStringSelection(self.T.e.batchElimination)
      self.Bind(wx.EVT_CHOICE, self.OnBatchElimination, self.batchEliminationC)
      labelList.append(batchEliminationL)
      ctrlList.append(self.batchEliminationC)
      batchCutoffL = wx.StaticText(self, -1, "Batch cutoff:")
      self.batchCutoffC = wx.SpinCtrl(self, -1)
      self.batchCutoffC.SetRange(0, 10000)
      self.batchCutoffC.SetValue(self.T.e.batchCutoff)
      if self.T.e.batchElimination == "Cutoff":
        self.batchCutoffC.Enable(True)
      else:
        self.batchCutoffC.Enable(False)
      labelList.append(batchCutoffL)
      ctrlList.append(self.batchCutoffC)

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
    fgs.Add(seatsL, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
    fgs.Add(self.seatsC, 0, wx.EXPAND)
    fgs.Add(widthL, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
    fgs.Add(self.widthC, 0, wx.EXPAND)
    fgs.AddGrowableCol(1)
    informationSizer.Add(fgs, 0, wx.EXPAND|wx.ALL, 5)

    # Withdraw candidates
    withdrawBox = wx.StaticBox(self, -1, "Withdraw Candidates")
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
    self.T.e.nSeats = self.seatsC.GetValue()
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
    
##################################################################

class AboutDialog(wx.Dialog):
  "Dialog for about OpenSTV box."

  def __init__(self, parent):
    wx.Dialog.__init__(self, parent, -1, "About OpenSTV")

    sizer = wx.BoxSizer(wx.VERTICAL)

    fn = os.path.join(HOME, "Icons", "splash.png")
    bmp = wx.Image(fn, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
    bm = wx.StaticBitmap(self, -1, bmp)
    sizer.Add(bm)

    button = wx.Button(self, wx.ID_OK, "Close")
    button.SetDefault()
    sizer.Add(button, 0, wx.ALIGN_CENTER|wx.ALL, 5)

    sizer.Fit(self)
    self.SetAutoLayout(True)
    self.SetSizer(sizer)

##################################################################

class HTMLFrame(wx.Frame):
  def __init__(self, parent, title, htmlFile):
    wx.Frame.__init__(self, parent, -1, title, size=(600, 400))
    self.win = wx.html.HtmlWindow(self, -1)
    fn = os.path.join(HOME, htmlFile)
    self.win.LoadFile(fn)

##################################################################

class App(wx.App):

  def OnInit(self):
    wx.InitAllImageHandlers()

    # Need this to be able to access local files
    global HOME
    exePath = os.path.split(sys.argv[0])[0]
    cwdPath = os.getcwd()
    if exePath == ".":
      HOME = cwdPath
    else:
      HOME = exePath

    # Show a splash screen
    png = os.path.join(HOME, "Icons", "splash.png")
    bmp = wx.Image(png).ConvertToBitmap()
    wx.SplashScreen(bmp,
                    wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT,
                    5000, None, -1)

    self.frame = Frame(None)
    self.frame.Show(True)
    self.frame.Center()
    self.frame.Raise()
    self.SetTopWindow(self.frame)
    return True

##################################################################

if __name__ == '__main__':
  app = App(0)
  app.MainLoop()
