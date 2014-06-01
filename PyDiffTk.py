#!/usr/bin/python
#
# edward.s.macgillivray@intel.com
# sergeyx.Belikov@intel.com
# andrewx.r.radke@intel.com
#
# http://www.shayanderson.com/linux/using-git-with-remote-repository.htm
# http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/index.html
# http://www.afterhoursprogramming.com/tutorial/Python/Formatting/
import sys, os, time, platform

import tkinter.messagebox
import tkinter.filedialog
import tkinter.font
import hashlib  #sha1
import logging
import difflib
import filecmp
import binascii
import shutil
import re
import subprocess
from subprocess import Popen, PIPE

sys.path.append('auxfiles')

import __main__ as main
from inspect import currentframe, getframeinfo
from send2trash import send2trash
from ToolTip import ToolTip
from MultiListbox import *
from DougModules import SearchPath
from DougModules import MyTrace
from DougModules import MyMessageBox
from DougModules import Logger
from DougModules import ParseCommandLine
from DougModules import StartFile

import pprint
pp=pprint.pprint

Main = tkinter.Tk()
Main.option_add('*Dialog.msg.wrapLength', '20i')

from PyDiffTkVars import Vars

#------------------------------

#Setup the logger
def SetUpLogger():
    Vars.LogFileNameVar.set(os.path.join(Vars.StartUpDirectoryVar.get(),'PyDiffTk.log'))
    logger = logging.getLogger()
    RemoveAFile(Vars.LogFileNameVar.get(), Trash = False)
    logger = logging.basicConfig(level=logging.DEBUG,
                filename=Vars.LogFileNameVar.get(),
                format='%(asctime)s %(levelname)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')
#------------------------------
#Set up defaults in case there is no project file
#Intialize the variables
#Written over by StartUpStuff and by ProjectLoad
def SetDefaults():
    print('SetDefaults')
    Vars.LeftPathEntry.delete(0,END)
    Vars.RightPathEntry.delete(0,END)
    Vars.FilterEntry.delete(0,END)
    Vars.SystemEditorVar.set('')
    Vars.SystemDifferVar.set('')
    Vars.SystemRenamerVar.set('')
    Vars.SystemLocaterVar.set('')
    Vars.ShowRightCheckVar.set(True)
    Vars.ShowLeftCheckVar.set(True)
    Vars.ShowBothCheckVar.set(True)
    Vars.ShowDiffCheckVar.set(True)
    Vars.ShowDirectoriesCheckVar.set(True)
    Vars.AutoRefreshCheckVar.set(True)
    Vars.ConfirmCopyCheckVar.set(True)
    Vars.ConfirmRenameCheckVar.set(True)
    Vars.ConfirmDeleteCheckVar.set(True)
    Vars.RecycleCheckVar.set(True)
    Vars.CheckSumAutoVar.set(True)
    Vars.CheckSumTypeVar.set(True)
    Vars.FileTimeTriggerScaleVar.set('10')
    Vars.TriggerNumberOfFilesVar.set('10')
    Vars.LeftSearchVar.set(True)
    Vars.RightSearchVar.set(True)
    Vars.StatusSearchVar.set(False)
    Vars.MoreSearchVar.set(False)
    Vars.CaseSearchVar.set(False)
#------------------------------
#Initialize the program
def StartUpStuff():
    #-- Lots of startup stuff ------------------------------------
    #The following are defaults which may be over-written by a project file
    print('StartUpStuff')
    if sys.platform.startswith('linux'):
        Vars.SystemEditorVar.set('gedit')
        Vars.SystemDifferVar.set('meld')
        Vars.SystemRenamerVar.set('pyrename')
        Vars.SystemLocaterVar.set('konqueror')
        Vars.ProjectFileExtensionVar.set('prjl')
    elif sys.platform.startswith('win32'):
        Vars.SystemEditorVar.set('c:\\windows\\notepad.exe')
        Vars.SystemDifferVar.set('C:\\Program Files (x86)\\WinMerge\\WinMergeU.exe')
        Vars.SystemRenamerVar.set('C:\\Program Files (x86)\\Ant Renamer\\Renamer.exe')
        Vars.SystemLocaterVar.set('explorer.exe')
        Vars.ProjectFileExtensionVar.set('prjw')

    Vars.StartUpDirectoryVar.set(os.getcwd())
    Vars.AuxDirectoryVar.set(os.path.join(Vars.StartUpDirectoryVar.get(),'auxfiles','.'))
    Vars.HelpFileVar.set(os.path.join(Vars.AuxDirectoryVar.get(),'PyDiffTk.hlp'))
    SetUpLogger()

    Logger(str(os.environ.get('OS')), getframeinfo(currentframe()))
    Logger(str(platform.uname()), getframeinfo(currentframe()))
    Logger('Number of argument(s): ' + str(len(sys.argv)), getframeinfo(currentframe()))
    Logger('Argument List: ' + str(sys.argv), getframeinfo(currentframe()))
    ProjectLoad('default') # Now get the project settings

#------------------------------
#This updates the ShowLineNumberVar label
def Update():
    Logger('Update', getframeinfo(currentframe()))
    Vars.ShowLineNumberVar.set(str(Vars.DataBox.curselection()) + ' of ' + str(Vars.DataBox.size()-1))
    Vars.DataBoxTooltipVar = str(Vars.DataBox.curselection())
    Vars.BatchNumberItemsVar.set(str(Vars.DataBox.curselection()) + ' of ' + str(Vars.DataBox.size()-1))
#------------------------------
# Bound to F7
# x is a junk parameter
# Displays Vars.SelectedListVar by updating DataBox
def ShowSelectedList(x=''):
    Logger('ShowSelectedList', getframeinfo(currentframe()))
    #if Vars.BatchBlockMode.get(): return
    Vars.DataBox.selection_clear(0, 99999)
    for x in Vars.SelectedListVar:
        print(MyTrace(getframeinfo(currentframe())),x)
        Vars.DataBox.selection_set(x)
        Vars.DataBox.see(x)
    Update()
#------------------------------
# Bound to F8
# x is a junk parameter
# Adds any selected rows to Vars.SelectedListVar and updates DataBox
def AddSelectedToList(x=''):
    Logger('AddSelectedToList', getframeinfo(currentframe()))
    if Vars.BatchBlockMode.get(): return
    # Get the currently selected index
    Current = str(Vars.DataBox.curselection())
    # Clean it up and extend to the list
    Current = re.sub('[(),\']','',Current)

    if len(Current) < 1: return # Nothing is selected so abort

    tmp = Current.split(' ')
    Vars.SelectedListVar.extend(tmp)

    # Now remove the dups from the list
    TempList = []
    for x in Vars.SelectedListVar:
        if x not in TempList:
            TempList.append(x)
    Vars.SelectedListVar = TempList

    # Clear DataBox and then repopulate it
    Vars.DataBox.selection_clear(0, 99999)
    for row in Vars.SelectedListVar:
        Vars.DataBox.selection_set(row)
        Vars.DataBox.see(row)
    Update()
#------------------------------
#Will Remove a row from Vars.SelectedListVar and the Databox
def RemoveARow():
    Logger('RemoveARow', getframeinfo(currentframe()))
    tkinter.messagebox.showerror('RemoveARow' ,'Not ready yet\n' + str(MyTrace(getframeinfo(currentframe()))))
    Update()
#------------------------------
# Bound to F9
# x is a junk parameter
# Clears Vars.SelectedListVar and the Databox
def ClearSelectedList(x=''):
    Logger('ClearSelectedList', getframeinfo(currentframe()))
    Vars.SelectedListVar = []
    Vars.DataBox.selection_clear(0, END)
    Vars.StartRowEntry.delete(0, END)
    Vars.StopRowEntry.delete(0, END)
    Update()
#------------------------------
#This will either delete a file or move it to trash
def RemoveAFile(File, Trash):
    #if os.access(FileName,os.W_OK)
    Logger('Remove a file: ' + File + str(Trash), getframeinfo(currentframe()))
    if not os.path.exists(File):
        return
    if Trash:
        try:
            send2trash(File)
        except OSError:
            tkinter.messagebox.showerror('Send file to trash error. ' ,File + '\nPermissions?')
    else:
        try:
            os.remove(File)
        except OSError:
            tkinter.messagebox.showerror('Delete a file error. ' ,File + '\nPermissions?')

#------------------------------

if __name__ == '__main__':
#------------------------------
    #This clears everything, terminal, GUI etc.
    def ClearAll():
        Logger('Clear everything', getframeinfo(currentframe()))
        Vars.FileRenameTopLevelVar.withdraw()
        Vars.FileInfoTopLevelVar.withdraw()
        Vars.OptionsTopLevelVar.withdraw()
        Vars.BatchTopLevelVar.withdraw()
        Vars.DataBox.delete(0, END)
        os.system(['clear','cls'][os.name == 'nt'])
        Main.update_idletasks()
#------------------------------
    def UpdatePathEntry(trace,Path):
        Logger('UpdatePathEntry ' + trace + ' ' + Path, getframeinfo(currentframe()))
        if os.path.isdir(Path):
            if not os.path.isdir(Path) or not os.access(Path, os.W_OK):
                tkinter.messagebox.showinfo('UpdatePathEntry error',
                    'Path not a directory or not writable\n' + trace + '\n' + Path)

        if trace == 'Left':
            Vars.LeftPathEntry.delete(0,END)
            Vars.LeftPathEntry.insert(0,Path)
        elif trace == 'Right':
            Vars.RightPathEntry.delete(0,END)
            Vars.RightPathEntry.insert(0,Path)
        else:
            tkinter.messagebox.showinfo('UpdatePathEntry error', 'Bad trace\n' + trace + '\n' + Path)
#------------------------------
#This searches for matching strings in the data and selects the lines that match
#CaseSearchVar enables/disables case sensitive searchs
#The user can select what data columns to search
#Null search is not allowed
    def SearchData(Mode):
        Logger('SearchData ' + Mode, getframeinfo(currentframe()))
        Vars.DataBox.selection_clear(0, Vars.DataBox.size())
        if Mode == 'main':
            a = Vars.SearchEntryMain.get()
        if Mode == 'batch':
            a = Vars.SearchEntryBatch.get()
        if len(a) < 1: return #No null searchs
        if Vars.CaseSearchVar.get(): a = a.upper()

        for x in range(0,Vars.DataBox.size()):
            Found = False
            b = Vars.DataBox.get(x)
            if Vars.CaseSearchVar.get(): b = [x.upper() for x in b]
            if Vars.LeftSearchVar.get():
                if a in b[0]: Found = True
            if Vars.RightSearchVar.get():
                if a in b[1]: Found = True
            if Vars.StatusSearchVar.get():
                if a in b[2]: Found = True
            if Vars.MoreSearchVar.get():
                if a in b[3]: Found = True
            if Found:
                Vars.DataBox.selection_set(x)
                Vars.DataBox.see(x)
#------------------------------
#Quit the program
    def Quit():
        Logger('Quit', getframeinfo(currentframe()))
        if tkinter.messagebox.askyesno('Quit', 'Really quit?'):
            Main.destroy()
            sys.exit(0)

#------------------------------
    def GetType(FileName):
        tmp = ''
        if os.path.isfile(FileName): tmp = 'File, '
        if os.path.isdir(FileName): tmp += 'Dir, '
        if os.path.islink(FileName): tmp += 'Link, '
        if os.path.ismount(FileName): tmp += 'Mount, '
        if not os.access(FileName,os.W_OK): tmp += 'Read only, '
        return tmp
#------------------------------
    def FetchDirectories(Trace):
        dir_opt = options = {}
        Vars.DoNotAskNumberOfFilesVar.set(False)
        if Trace == 'Both':
            Logger('Fetch directories ' + Trace, getframeinfo(currentframe()))
            Vars.DataBox.delete(0, END)
            Vars.FileRenameTopLevelVar.withdraw()
            Vars.FileInfoTopLevelVar.withdraw()
            Vars.StatusVar.set('Fetch directories')

        if Trace == 'Left' or Trace == 'Both':
            options['title'] = 'Select left directory'
            options['initialdir'] = Vars.LeftPathEntry.get()
            New = tkinter.filedialog.askdirectory(**dir_opt)
            if len(New) > 0:
                UpdatePathEntry('Left', New)

        if Trace == 'Right' or Trace == 'Both':
            options['title'] = 'Select right directory'
            options['initialdir'] = Vars.RightPathEntry.get()
            New = tkinter.filedialog.askdirectory(**dir_opt)
            if len(New) > 0:
                UpdatePathEntry('Right', New)
#------------------------------
    # Return a checksum for the FileName
    # Force overrides CheckSumAuto
    def GetCheckSum(FileName, Force=False):
        if not os.path.isfile(FileName):
            return 'Checksum not tested. Not a file.'
        if not Vars.CheckSumAutoVar.get() and not Force:
            return 'Checksum not auto-enabled.'
        if Vars.CheckSumTypeVar.get() == 1: # crc32file
            return str(crc32file(FileName))
        elif Vars.CheckSumTypeVar.get() == 2: # md5file
            return str(md5file(FileName))
        elif Vars.CheckSumTypeVar.get() == 3: # sha1file
            return str(sha1file(FileName))
        else:
            tkinter.messagebox.showerror('GetCheckSum(FileName) error',
            'Invalid checksum type\n' +
            'Values from 1 to 3 are valid\n' +
            Vars.ProjectFileNameVar.get() + '\n' +
            str(Vars.CheckSumAutoVar.get()) + '\n' +
            str(Vars.CheckSumTypeVar.get()))
            raise SystemExit
            return 0
#------------------------------
#This displays a splash screen. It is always centered in the main window
#It also enables/disables menu buttons as appropriate
    def SplashScreen(Message, Show):
        if Show: #Display the splashscreen and disable the button
            FetchDataButton.config(state=DISABLED)
            Vars.SplashTopLevelVar = Toplevel(Main)
            Vars.SplashTopLevelVar.title(Message)

            Main.update()
            SplashTopLevelSizeX = 500
            SplashTopLevelSizeY = 200
            Mainsize = Main.geometry().split('+')
            x = int(Mainsize[1]) + SplashTopLevelSizeX / 2
            y = int(Mainsize[2]) + SplashTopLevelSizeY / 2
            Vars.SplashTopLevelVar.geometry("%dx%d+%d+%d" % (SplashTopLevelSizeX,SplashTopLevelSizeY,x,y))
            Vars.SplashTopLevelVar.resizable(1,1)

            w = Label(Vars.SplashTopLevelVar, text=Message,fg='yellow',bg='blue',font=("Helvetica", 30))
            w.pack(side=TOP, fill=BOTH, expand=YES)
            Vars.SplashTopLevelVar.wm_transient(Main)
            Main.update()
        else: #Destroy the splashscreen and enable the button
            Vars.SplashTopLevelVar.destroy()
            FetchDataButton.config(state=NORMAL)
#------------------------------
    def FetchData():
        SplashScreen('FetchData is running', True)
        Logger('Fetch data', getframeinfo(currentframe()))

        DataBoxCurrentLine = re.sub("[^0-9]", "", str(Vars.DataBox.curselection()))
        Vars.DataBox.delete(0, END)

        if not os.path.isdir(Vars.LeftPathEntry.get()):
            tkinter.messagebox.showerror('Left path does not exist', 'Left path error:\n' + Vars.LeftPathEntry.get())
            Vars.StatusVar.set('Left path error')
            SplashScreen('FetchData is closing', False)
            return

        if not os.path.isdir(Vars.RightPathEntry.get()):
            tkinter.messagebox.showerror('Right path does not exist', 'Right path error:\n' + Vars.RightPathEntry.get())
            Vars.StatusVar.set('Right path error')
            SplashScreen('FetchData is closing', False)
            return

        LeftNumberOfFiles = len([item for item in os.listdir(Vars.LeftPathEntry.get()) if os.path.isfile(os.path.join(Vars.LeftPathEntry.get(), item))])
        RightNumberOfFiles = len([item for item in os.listdir(Vars.RightPathEntry.get()) if os.path.isfile(os.path.join(Vars.RightPathEntry.get(), item))])
        ActualTotalFiles =  LeftNumberOfFiles + RightNumberOfFiles
        Logger('Disable stuff: ' + str(ActualTotalFiles)+ '   ' + str( Vars.TriggerNumberOfFilesVar.get()), getframeinfo(currentframe()))

        #Decide to disable autorefresh and/or checksum
        if (ActualTotalFiles > Vars.TriggerNumberOfFilesVar.get()) and not Vars.DoNotAskNumberOfFilesVar.get():
            Vars.DoNotAskNumberOfFilesVar.set(True)
            if Vars.AutoRefreshCheckVar.get(): #enabled
                if tkinter.messagebox.askyesno(str(ActualTotalFiles) + ' files to be processed','Disable autorefresh?'):
                    Vars.AutoRefreshCheckVar.set(False)
            if Vars.CheckSumAutoVar.get(): #enabled
                if tkinter.messagebox.askyesno(str(ActualTotalFiles) + ' files to be processed','Disable checksum?'):
                    Vars.CheckSumAutoVar.set(False)

        Vars.StatusVar.set('Starting the compare')
        comparison = filecmp.dircmp(Vars.LeftPathEntry.get(), Vars.RightPathEntry.get())

        if Vars.ShowBothCheckVar.get():
            new = sorted(comparison.common)
            for name in new:
                if Vars.FilterEntry.get().upper() in name.upper():
                    LeftName = os.path.join(Vars.LeftPathEntry.get(), name)
                    RightName = os.path.join(Vars.RightPathEntry.get(), name)
                    CompareString = ''
                    CompareString += GetType(LeftName)
                    CompareString += GetType(RightName)

                    if not Vars.ShowDirectoriesCheckVar.get(): #Don't show directories
                        if 'Dir' in CompareString: continue

                    if os.path.getsize(LeftName) != os.path.getsize(RightName):
                        CompareString += 'Size, '
                    #Check sum is tested only if CheckSumAutoVar is True and item is in both left and right
                    if Vars.CheckSumAutoVar.get() and GetCheckSum(LeftName) != GetCheckSum(RightName):
                        CompareString += 'CheckSum, '

                    TimeDiff = abs(os.path.getmtime(LeftName) - os.path.getmtime(RightName))
                    if TimeDiff < 1:
                        pass
                    elif TimeDiff > Vars.FileTimeTriggerScaleVar.get():
                        CompareString += 'TIME, ' #Big time difference
                    else:
                        CompareString += 'time, ' #Small time difference
                    Vars.DataBox.insert(END,(name,name,'Both',CompareString))

        Dict = {}
        new1 = sorted(comparison.left_only)
        for s in new1:
            if (Vars.ShowLeftCheckVar.get()) and Vars.FilterEntry.get().upper() in s.upper():
                if os.path.isdir(os.path.join(Vars.LeftPathEntry.get(), s)):
                    if Vars.ShowDirectoriesCheckVar.get():
                        Vars.DataBox.insert(END,(s,'','Left','Directory'))
                else:
                    Vars.DataBox.insert(END,(s,'','Left','File'))
            if not s.upper() in Dict:
                Dict[s.upper()] = 0
            else:
                Dict[s.upper()] += 1

        new2 = sorted(comparison.right_only)
        for s in new2:
            if (Vars.ShowRightCheckVar.get()) and Vars.FilterEntry.get().upper() in s.upper():
                if os.path.isdir(os.path.join(Vars.RightPathEntry.get(), s)):
                    if Vars.ShowDirectoriesCheckVar.get():
                        Vars.DataBox.insert(END,('',s,'Right','Directory'))
                else:
                    Vars.DataBox.insert(END,('',s,'Right','File'))
            if not s.upper() in Dict:
                Dict[s.upper()] = 0
            else:
                Dict[s.upper()] += 1

        if Vars.ShowDiffCheckVar.get():
            for key, value in Dict.items():
                for s in new1:
                    if s.upper() == key and value > 0 and Vars.FilterEntry.get().upper() in s.upper():
                        Vars.DataBox.insert(END,(s,'','Diff','Diff'))
                        Logger('Show diff new1: ' + s, getframeinfo(currentframe()))
                for s in new2:
                    if s.upper() == key and value > 0 and Vars.FilterEntry.get().upper() in s.upper():
                        Vars.DataBox.insert(END,('',s,'Diff','Diff'))
                        Logger('Show diff new2: ' + s, getframeinfo(currentframe()))


        Vars.StatusVar.set('Compare complete. Items: ' + str(Vars.DataBox.size()-1))
        Vars.ShowLineNumberVar.set('No line selected of ' + str(Vars.DataBox.size()-1))
        SplashScreen('FetchData is closing', False)

        try:
            Vars.DataBox.selection_set(DataBoxCurrentLine)
            Vars.DataBox.see(DataBoxCurrentLine)
        except:
            Vars.DataBox.selection_set(0)
            Vars.DataBox.see(0)

        Main.update()
#------------------------------
    def crc32file(filename):
        filedata = open(filename,'rt').read()
        return binascii.crc32(bytearray(filedata,'utf-8'))
#------------------------------
    def md5file(filename, block_size=256*128):
        md5 = hashlib.md5()
        with open(filename,'rt') as f:
            for chunk in iter(lambda: f.read(block_size), b''):
                 md5.update(chunk)
        return md5.hexdigest()
#------------------------------
    def sha1file(filename):
        sha1 = hashlib.sha1()
        f = open(filename, 'rb')
        try:
            sha1.update(f.read())
        except:
            Logger('whoops '  + str(exception), getframeinfo(currentframe()))
        finally:
            f.close()
        return sha1.hexdigest()
#------------------------------
    # All copying is done here (Both batch and individual).
    # Checks for status before and after copy
    # Check for user OK
    def CopyAFile(Trace, src, dst, IsBatch):
        if os.path.isdir(dst): dst = os.path.join(dst, "")

        Logger('Trace: %s SRC:%s DST:%s IsBatch:%d' % (Trace, src, dst, IsBatch),getframeinfo(currentframe()))
        errors = []
        if os.path.isdir(src):
            Logger(src + ' is directory', getframeinfo(currentframe()))
            if tkinter.messagebox.askyesno(Trace, 'Copy directory tree?\n' + src + ' \nto\n ' + dst):
                try:
                    Logger(dst + os.path.basename(src), getframeinfo(currentframe()))
                    shutil.copytree(src, dst + os.path.basename(src), symlinks=False, ignore=None)
                except shutil.Error as e:
                    Logger('Directory not copied. Error: %s' % e, getframeinfo(currentframe()))
                # Any error saying that the directory doesn't exist
                except OSError as e:
                    Logger('Directory not copied. Error: %s' % e, getframeinfo(currentframe()))
                if Vars.AutoRefreshCheckVar.get() and not IsBatch:
                    FetchData()
            return

        if Vars.ConfirmCopyCheckVar.get():
            if not tkinter.messagebox.askyesno(Trace, 'Copy\n' + src + '\nto\n' + dst + '?'):
                Logger('Copy aborted by user\n' + src + '\nto\n' + dst, getframeinfo(currentframe()))
                return
        try:
            getframeinfo(currentframe())[1], shutil.copy2(src, dst)
        except:
        #except IOError, e:
            tkinter.messagebox.showerror(Trace, 'Retry copy\n' + src + '\nto\n' + dst + ' ' + str(e))
            Logger('Copy failed\n' + src + '\nto\n' + dst + ' ' , e, getframeinfo(currentframe()))
            return

        if Vars.AutoRefreshCheckVar.get() and not IsBatch: FetchData()
        return

    def CopyLeft():
        src = os.path.join(Vars.LeftPathEntry.get(), Vars.FileLeftNameVar.get())
        dst = Vars.RightPathEntry.get()
        CopyAFile('CopyLeft', src, dst, False)

    def CopyRight():
        src = os.path.join(Vars.RightPathEntry.get(), Vars.FileRightNameVar.get())
        dst = Vars.LeftPathEntry.get()
        CopyAFile('CopyRight', src, dst , False)
        #------------------------------

    # All deleting is done here (Both batch and individual).
    # Checks for status before and after delete
    # Check for user OK
    def DeleteAFile(file1, file2):
        if Vars.RecycleCheckVar.get() == 0:
            Message = 'Delete'
        else:
            Message = 'Recycle'

        Logger('DeleteAFile  left:' + file1 + '<< right:' + file2 +'<< ' + Message, getframeinfo(currentframe()))
        Main.update_idletasks()
        if Vars.ConfirmDeleteCheckVar.get():
            if not tkinter.messagebox.askyesno(Message + ' file(s)?', file1 + '\n' + file2):
                Logger(Message + ' aborted', file1 + '  ' + file2, getframeinfo(currentframe()))
                return

        if Vars.RecycleCheckVar.get() == 0:
            Logger('os.remove', getframeinfo(currentframe()))
            RemoveAFile(file1, Trash = False)
            RemoveAFile(file2, Trash = False)
            #if os.path.exists(file1): os.remove(file1)
            #if os.path.exists(file2): os.remove(file2)
        else:
            if os.path.exists(file1):
                #send2trash(file1)
                RemoveAFile(file1, Trash = True)
                if os.path.exists(file1): #This tests to see if the operation worked
                    if tkinter.messagebox.showerror(Message + ' failed',file1):
                        Logger(Message + ' failed ' + file1, getframeinfo(currentframe()))
            if os.path.exists(file2):
                #send2trash(file2)
                RemoveAFile(file2, Trash = True)
                if os.path.exists(file2): #This tests to see if the operation worked
                    if tkinter.messagebox.showerror(Message + ' failed',file2):
                        Logger(Message + ' failed ' + file2, getframeinfo(currentframe()))

        if Vars.AutoRefreshCheckVar.get(): FetchData()
        else: Vars.StatusVar.set('Refresh needed')

    def DeleteBoth():
        file1 = os.path.join(Vars.LeftPathEntry.get(), Vars.FileLeftNameVar.get())
        file2 = os.path.join(Vars.RightPathEntry.get(), Vars.FileRightNameVar.get())
        DeleteAFile(file1, file2)

    def DeleteLeft():
        file = os.path.join(Vars.LeftPathEntry.get(), Vars.FileLeftNameVar.get())
        DeleteAFile(file,'')

    def DeleteRight():
        file = os.path.join(Vars.RightPathEntry.get(), Vars.FileRightNameVar.get())
        DeleteAFile('',file)
#------------------------------
#This class handles file rename for the file info menu
    class FileRename:
        RenameEntry = None
        Trace = 'Bullpoo'
        def FileRenameBoth():
            Logger('RenameBoth',getframeinfo(currentframe()))
            if len(Vars.FileLeftNameVar.get()) > 0 and len(Vars.FileRightNameVar.get()) > 0:
                self.Trace='Both'
                self.RenameAFile()

        def FileRenameRight(self):
            if len(Vars.FileRightNameVar.get()) > 0:
                self.Trace='Right'
                self.RenameAFile()

        def FileRenameLeft(self):
            if len(Vars.FileLeftNameVar.get()) > 0:
                self.Trace='Left'
                self.RenameAFile()

    #------------------------------
        def Swapcase(self):
            filename = self.RenameEntry.get()
            self.RenameEntry.delete(0,END)
            self.RenameEntry.insert(0,filename.swapcase())

        def Titlecase(self):
            filename = self.RenameEntry.get()
            def titlecase(s):
                return re.sub(r"[A-Za-z]+('[A-Za-z]+)?",
                lambda mo: mo.group(0)[0].upper() +
                mo.group(0)[1:].lower(),s)
            self.RenameEntry.delete(0,END)
            self.RenameEntry.insert(0,titlecase(filename))

        def Uppercase(self):
            filename = self.RenameEntry.get()
            self.RenameEntry.delete(0,END)
            self.RenameEntry.insert(0,filename.upper())
            self.RenameEntry.focus_set()

        def Lowercase(self):
            filename = self.RenameEntry.get()
            self.RenameEntry.delete(0,END)
            self.RenameEntry.insert(0,filename.lower())
            self.RenameEntry.focus_set()

        def Capitalize(self):
            filename = self.RenameEntry.get()
            self.RenameEntry.delete(0,END)
            self.RenameEntry.insert(0,filename.capitalize())
            self.RenameEntry.focus_set()

        def Done(self): #Filename will always be the same
            filenameL = Vars.FileLeftNameVar.get()
            filenameR = Vars.FileRightNameVar.get()
            filepathL = Vars.LeftPathEntry.get()
            filepathR = Vars.RightPathEntry.get()
            try:
                if self.Trace == 'Both':
                    os.rename(os.path.join(filepathL, filenameL), os.path.join(filepathL, self.RenameEntry.get()))
                    self.RenameTest(os.path.join(filepathL, filenameL), os.path.join(filepathL, self.RenameEntry.get()))
                    os.rename(os.path.join(filepathR, filenameR), os.path.join(filepathR, self.RenameEntry.get()))
                    RenameTest('Both Right' ,os.path.join(filepathL, filenameL), os.path.join(filepathL, self.RenameEntry.get()))
                    Logger('os.rename both', getframeinfo(currentframe()))
                elif self.Trace == 'Left':
                    os.rename(os.path.join(filepathL, filenameL), os.path.join(filepathL, self.RenameEntry.get()))
                    self.RenameTest(os.path.join(filepathL, filenameL), os.path.join(filepathL, self.RenameEntry.get()))
                    Logger('os.rename left', getframeinfo(currentframe()))
                elif self.Trace == 'Right':
                    os.rename(os.path.join(filepathR, filenameR), os.path.join(filepathR, self.RenameEntry.get()))
                    self.RenameTest(os.path.join(filepathL, filenameL), os.path.join(filepathL, self.RenameEntry.get()))
                    Logger('os.rename right', getframeinfo(currentframe()))
                else: Logger( 'OPPS. Bad trace value ' + self.Trace, getframeinfo(currentframe()))
            except:
                print('*********************************')
                tkinter.messagebox.showerror('Rename error',
                    'Source file does not exist\nRefresh needed')

            Vars.FileRenameTopLevelVar.withdraw()
            if Vars.AutoRefreshCheckVar.get(): FetchData()

        #If the two names are the same then the rename succeeded
        def RenameTest(self,left,right):
            if left == right:
                Logger('os.rename test: ' + self.Trace + ' FAIL ',getframeinfo(currentframe()))
            else:
                Logger('os.rename test: ' + self.Trace + ' PASS ',getframeinfo(currentframe()))

        def Cancel(self):
            Vars.FileRenameTopLevelVar.withdraw()

        Vars.StatusVar.set('Refresh needed (Fetch Data)')

        def RenameAFile(self):
            FileRenameTopLevelVar = Toplevel()
            FileRenameTopLevelVar.title(self.Trace + ' file rename')
            FileRenameTopLevelVar.resizable(0,0)

            Main.update()
            FileRenameTopLevelSizeX = 460
            FileRenameTopLevelSizeY = 110
            Mainsize = Main.geometry().split('+')
            x = int(Mainsize[1]) + FileRenameTopLevelSizeX / 2
            y = int(Mainsize[2]) + FileRenameTopLevelSizeY / 2
            FileRenameTopLevelVar.geometry("%dx%d+%d+%d" % (FileRenameTopLevelSizeX, FileRenameTopLevelSizeY, x, y))
            FileRenameTopLevelVar.resizable(1,1)

            FileRenameFrame1 = Frame(FileRenameTopLevelVar, relief=SUNKEN, bd=1)
            FileRenameFrame1.pack(side=TOP)
            FileRenameFrame2 = Frame(FileRenameTopLevelVar, relief=SUNKEN, bd=1)
            FileRenameFrame2.pack(side=TOP)
            FileRenameFrame3 = Frame(FileRenameTopLevelVar, relief=SUNKEN, bd=1)

            if self.Trace == 'Both':
                filename = Vars.FileRightNameVar.get()
            elif self.Trace == 'Left':
                filename = Vars.FileLeftNameVar.get()
            elif self.Trace == 'Right':
                filename = Vars.FileRightNameVar.get()
            else: Logger('OPPS. Bad trace value', getframeinfo(currentframe()))

            Label(FileRenameFrame1, text=filename).pack()
            self.RenameEntry = Entry(FileRenameFrame1, width=50)
            self.RenameEntry.pack()
            self.RenameEntry.delete(0,END)
            self.RenameEntry.insert(0,filename)
            self.RenameEntry.focus_set()

            FileRenameFrame3.pack(side=TOP)
            Button(FileRenameFrame2, text='Done', width=12, command=self.Done).pack(side=LEFT)
            Button(FileRenameFrame2, text='Cancel', width=12, command=self.Cancel).pack(side=LEFT)
            Button(FileRenameFrame2, text='Title', width=12, command=self.Titlecase).pack(side=LEFT)

            Button(FileRenameFrame3, text='Upper', width=12, command=self.Uppercase).pack(side=LEFT)
            Button(FileRenameFrame3, text='Lower', width=12, command=self.Lowercase).pack(side=LEFT)
            Button(FileRenameFrame3, text='Swap', width=12, command=self.Swapcase).pack(side=LEFT)
            Button(FileRenameFrame3, text='Capitalize', width=12, command=self.Capitalize).pack(side=LEFT)

#------------------------------
#TODO 'This does not work for linux'
    def LocateFile(path):
        Logger(path, getframeinfo(currentframe()))
        subprocess.call([Vars.SystemLocaterVar.get(),path])

    def LocateRight():
        path = str(Vars.RightPathEntry.get())
        LocateFile(path)

    def LocateLeft():
        path = str(Vars.LeftPathEntry.get())
        LocateFile(path)

    def LocateBoth():
        LocateLeft()
        LocateRight()

#This works when both exist
    def DiffBoth():
        Logger('DiffBoth', getframeinfo(currentframe()))
        Left = os.path.join(Vars.LeftPathEntry.get(), Vars.FileLeftNameVar.get())
        Right = os.path.join(Vars.RightPathEntry.get(), Vars.FileRightNameVar.get())
        StartFile(Vars.SystemDifferVar.get(), Left, Right)

#------------------------------
    class FileInfo:
        LeftButtons = True
        RightButtons = True

        BothDeleteButton = None
        BothDiffButton = None
        BothCheckSUMButton = None
        LeftCopyButton = None
        LeftDeleteButton = None
        RightCopyButton = None
        RightDeleteButton = None
        LeftCheckSumButton = None
        RightCheckSumButton = None

        LeftPathAndNameVar = StringVar()
        RightPathAndNameVar = StringVar()
        RowInfoVar = StringVar()
        FileStatusVar = StringVar()
        TypeStatusVar = StringVar()
        SizeStatusVar = StringVar()
        TimeStatusVar = StringVar()
        CheckSumStatusVar = StringVar()
        StatType = None
        StatSize = None
        StatTime = None
        StatCheckSum = None
        FileLeftTypeVar = StringVar()
        FileRightTypeVar = StringVar()
        FileLeftSizeVar = StringVar()
        FileRightSizeVar = StringVar()
        FileRightTimeVar = StringVar()
        FileLeftTimeVar = StringVar()
        FileLeftCheckSumVar = StringVar()
        FileRightCheckSumVar = StringVar()
        FileInfoBGColor = StringVar()

        def ClearInfoForm(self):
            Vars.FileLeftNameVar.set('')
            Vars.FileRightNameVar.set('')
            self.FileLeftTypeVar.set('')
            self.FileRightTypeVar.set('')
            self.FileLeftTimeVar.set('')
            self.FileRightTimeVar.set('')
            self.FileLeftSizeVar.set('')
            self.FileRightSizeVar.set('')
            self.FileLeftCheckSumVar.set('')
            self.FileRightCheckSumVar.set('')
            self.TypeStatusVar.set('')
            self.TimeStatusVar.set('')
            self.SizeStatusVar.set('')
            self.CheckSumStatusVar.set('')

            self.StatType.config(bg=self.FileInfoBGColor.get())
            self.StatTime.config(bg=self.FileInfoBGColor.get())
            self.StatSize.config(bg=self.FileInfoBGColor.get())
            self.StatCheckSum.config(bg=self.FileInfoBGColor.get())
            self.RowInfoVar.set('')
            self.FileStatusVar.set('')


        def UpdateCheckSumStatus(self):
            #The following updates the checksum status bar
            if self.FileLeftCheckSumVar.get().find('Checksum') > -1 and \
               self.FileRightCheckSumVar.get().find('Checksum') > -1:
                self.StatCheckSum.config(bg='yellow')
                self.CheckSumStatusVar.set('Checksum not tested')
            else:
                if self.FileLeftCheckSumVar.get() == 'Checksum not tested' or \
                    self.FileLeftCheckSumVar.get() == 'Checksum not tested':
                    self.CheckSumStatusVar.set('Checksums not tested')
                    self.StatCheckSum.config(bg='grey')
                elif self.FileLeftCheckSumVar.get() != self.FileRightCheckSumVar.get():
                    self.CheckSumStatusVar.set('Checksums are different')
                    self.StatCheckSum.config(bg='red')
                else:
                    self.CheckSumStatusVar.set('Checksums are the same')
                    self.StatCheckSum.config(bg='green')

        #This builds the file information form
        def BuildFileInfoForm(self):
            def FileInfoXButton():
                Logger('FileInfo X button detected', getframeinfo(currentframe()))
                Vars.FileInfoTopLevelVar.withdraw()

            Vars.FileInfoTopLevelVar = Toplevel()
            #Vars.FileInfoTopLevelVar.overrideredirect(1)
            Vars.FileInfoTopLevelVar.title('File information')
            Vars.FileInfoTopLevelVar.resizable(1,1)
            Vars.FileInfoTopLevelVar.wm_transient(Main)
            Vars.FileInfoTopLevelVar.protocol('WM_DELETE_WINDOW', FileInfoXButton)

            FileInfoFrame1 = Frame(Vars.FileInfoTopLevelVar,relief=SUNKEN,bd=1)
            FileInfoFrame1.pack(side=TOP,fill=X)
            FileInfoFrame2 = Frame(Vars.FileInfoTopLevelVar,relief=SUNKEN,bd=1)
            FileInfoFrame2.pack(side=TOP,fill=X)
            FileInfoFrame3 = Frame(Vars.FileInfoTopLevelVar,relief=SUNKEN,bd=1)
            FileInfoFrame3.pack(side=TOP,fill=X)
            FileInfoFrame4 = Frame(Vars.FileInfoTopLevelVar,relief=SUNKEN,bd=1)
            FileInfoFrame4.pack(side=TOP,fill=X)
            FileInfoFrame5 = Frame(Vars.FileInfoTopLevelVar,relief=SUNKEN,bd=1)
            FileInfoFrame5.pack(side=TOP,fill=X)

            #These are the definitions for the top frame (status)
            Label(FileInfoFrame1, textvariable = self.FileStatusVar).pack(fill=X)
            self.RowInfoLabel = Label(FileInfoFrame1, textvariable = self.RowInfoVar)
            self.RowInfoLabel.pack(fill=X)
            ToolTip(self.RowInfoLabel,'Selected row(s) and total rows in data')

            self.StatType = Label(FileInfoFrame1, textvariable = self.TypeStatusVar)
            self.StatType.pack(fill=X)
            ToolTip(self.StatType, text='Dir or file and read only status (both)')

            #The next line saves the defaut BG color so it can be restored to various items later
            self.FileInfoBGColor.set(self.StatType.cget('bg'))

            #Status labels for type, size, time/date, amd checksum
            self.StatSize = Label(FileInfoFrame1, textvariable = self.SizeStatusVar)
            self.StatSize.pack(fill=X)
            ToolTip(self.StatSize, text='File size status (both)')
            self.StatTime = Label(FileInfoFrame1, textvariable = self.TimeStatusVar)
            self.StatTime.pack(fill=X)
            ToolTip(self.StatTime, text='File date and time status (both)')
            self.StatCheckSum = Label(FileInfoFrame1, textvariable = self.CheckSumStatusVar)
            self.StatCheckSum.pack(fill=X)
            ToolTip(self.StatCheckSum, text='File checksum status (both)')

            #Now define the buttons for frame 1 in the ButtonFrame
            ButtonFrame = Frame(FileInfoFrame1, relief=SUNKEN, bd=1)
            ButtonFrame.pack(fill=X)
            self.BothDeleteButton = Button(ButtonFrame, text='Delete', width=8, command=DeleteBoth)
            self.BothDeleteButton.pack(side=LEFT, fill=X)
            ToolTip(self.BothDeleteButton, text='Delete both left and right selected items')
            self.BothDiffButton = Button(ButtonFrame, text='Diff', width=10, command=DiffBoth)
            self.BothDiffButton.pack(side=LEFT, fill=X)
            ToolTip(self.BothDiffButton, text='Call an external difference program to compare the selected files/directories')

            def BothCheckSUM():
                self.FileLeftCheckSumVar.set(GetCheckSum(self.LeftPathAndNameVar.get(), True))
                self.FileRightCheckSumVar.set(GetCheckSum(self.RightPathAndNameVar.get(), True))
                self.UpdateCheckSumStatus()
            self.BothCheckSUMButton = Button(ButtonFrame, text='CheckSUM', width=8, command=BothCheckSUM)
            self.BothCheckSUMButton.pack(side=LEFT,fill=X)
            ToolTip(self.BothCheckSUMButton, text='Compute checksums for both files')

            def ChangeDir():
                Vars.LeftPathEntry.delete(0,END)
                Vars.RightPathEntry.delete(0,END)
                UpdatePathEntry('Left',self.LeftPathAndNameVar.get())
                UpdatePathEntry('Right',self.RightPathAndNameVar.get())
                if Vars.AutoRefreshCheckVar.get(): FetchData()
                else: Vars.StatusVar.set('Refresh needed')

            self.BothChangeDirButton = Button(ButtonFrame, text='Change Dir', width=16, command=ChangeDir)
            self.BothChangeDirButton.pack(side=LEFT,fill=X)
            ToolTip(self.BothChangeDirButton, text='Change to the selected directories')

            #The definitions for Left begin here
            Label(FileInfoFrame2, text='Left information',fg='blue').pack(fill=X)
            Label(FileInfoFrame2, textvariable = Vars.FileLeftNameVar).pack(fill=X)
            Label(FileInfoFrame2, textvariable = self.FileLeftTypeVar).pack(fill=X)
            Label(FileInfoFrame2, textvariable = self.FileLeftSizeVar).pack(fill=X)
            Label(FileInfoFrame2, textvariable = self.FileLeftTimeVar).pack(fill=X)
            def LeftCheckSum():
                self.FileLeftCheckSumVar.set(GetCheckSum(self.LeftPathAndNameVar.get(), True))
                self.UpdateCheckSumStatus()
            self.LeftCheckSumButton = Button(FileInfoFrame2, textvariable = self.FileLeftCheckSumVar, command=LeftCheckSum)
            self.LeftCheckSumButton.pack(fill=X)
            ToolTip(self.LeftCheckSumButton,'Compute left checksum')
            self.LeftCopyButton = Button(FileInfoFrame3, text='Copy', command=CopyLeft, width=10, state=DISABLED)
            self.LeftCopyButton.pack(side=LEFT,fill=X)
            ToolTip(self.LeftCopyButton,'Copy left side item to the right side')
            self.LeftDeleteButton = Button(FileInfoFrame3, text='Delete', command=DeleteLeft, width=10, state=DISABLED)
            self.LeftDeleteButton.pack(side=LEFT,fill=X)
            ToolTip(self.LeftDeleteButton,'Delete the left side item')

            #The following section creates the rename toplevel instance
            FileRenameInstance = FileRename()

            self.LeftRenameButton = Button(FileInfoFrame3, text='Rename', command=FileRenameInstance.FileRenameLeft, width=10, state=DISABLED)
            self.LeftRenameButton.pack(side=LEFT,fill=X)
            ToolTip(self.LeftRenameButton,'Rename the left side item')
            self.LeftLocateButton = Button(FileInfoFrame3, text='Locate',command=LocateLeft, width=10, state=DISABLED)
            self.LeftLocateButton.pack(side=LEFT,fill=X)
            ToolTip(self.LeftLocateButton,'Open the directoty containing the left side item')

            self.RightCopyButton = Button(FileInfoFrame5, text='Copy', command=CopyRight, width=10, state=DISABLED)
            self.RightCopyButton.pack(side=LEFT,fill=X)
            ToolTip(self.RightCopyButton,'Copy right side item to the left side')
            self.RightDeleteButton = Button(FileInfoFrame5, text='Delete', command=DeleteRight, width=10, state=DISABLED)
            self.RightDeleteButton.pack(side=LEFT,fill=X)
            ToolTip(self.RightDeleteButton,'Delete the right side item')
            self.RightRenameButton = Button(FileInfoFrame5, text='Rename', command=FileRenameInstance.FileRenameRight, width=10, state=DISABLED)
            ToolTip(self.RightRenameButton,'Rename the right side item')
            self.RightRenameButton.pack(side=LEFT,fill=X)
            self.RightLocateButton = Button(FileInfoFrame5, text='Locate',command=LocateRight, width=10, state=DISABLED)
            self.RightLocateButton.pack(side=LEFT,fill=X)
            ToolTip(self.RightLocateButton,'Open the directoty containing the right side item')

            #The definitions for Right begin here
            Label(FileInfoFrame4, text='Right information',fg='blue').pack(fill=X)
            Label(FileInfoFrame4, textvariable = Vars.FileRightNameVar).pack(fill=X)
            Label(FileInfoFrame4, textvariable = self.FileRightTypeVar).pack(fill=X)
            Label(FileInfoFrame4, textvariable = self.FileRightSizeVar).pack(fill=X)
            Label(FileInfoFrame4, textvariable = self.FileRightTimeVar).pack(fill=X)
            def RightCheckSum():
                self.FileRightCheckSumVar.set(GetCheckSum(self.RightPathAndNameVar.get(), True))
                self.UpdateCheckSumStatus()
            self.RightCheckSumButton = Button(FileInfoFrame4, textvariable = self.FileRightCheckSumVar, command=RightCheckSum)
            ToolTip(self.RightCheckSumButton,'Compute right checksum')
            self.RightCheckSumButton.pack(fill=X)
            Vars.FileInfoTopLevelVar.withdraw()

        def ShowFileInfo(self):
            self.ClearInfoForm()
            Vars.FileInfoTopLevelVar.deiconify()
            Vars.FileInfoTopLevelVar.wm_transient(Main)
            FileInfoTopLevelX = 400
            FileInfoTopLevelY = 510
            Mainsize = Main.geometry().split('+')
            x = int(Mainsize[1]) + (FileInfoTopLevelX / 2)
            y = int(Mainsize[2]) + (FileInfoTopLevelX / 2)

            Vars.FileInfoTopLevelVar.geometry("%dx%d+%d+%d" % (FileInfoTopLevelX, FileInfoTopLevelY, x, y))
            Vars.FileInfoTopLevelVar.resizable(1,1)

            Logger('ShowFileInfoForm', getframeinfo(currentframe()))
            Logger('FileInfo', getframeinfo(currentframe()))
            if Vars.DataBox.size() < 0:
                tkinter.messagebox.showerror('Data box error', 'Databox is empty')
                return

            if not Vars.DataBox.curselection():
                tkinter.messagebox.showerror('Data box error', 'Nothing is selected')
                return

            self.RowInfoVar.set('Row ' + str(Vars.DataBox.curselection()[0]) + ' of ' + str(Vars.DataBox.size()-1))
            t = Vars.DataBox.curselection()

            Vars.FileLeftNameVar.set(Vars.DataBox.get(t)[0])
            Vars.FileRightNameVar.set(Vars.DataBox.get(t)[1])

            if len(Vars.FileLeftNameVar.get()) > 0:
                self.LeftPathAndNameVar.set(os.path.join(Vars.LeftPathEntry.get(), Vars.FileLeftNameVar.get()))
            else:
                self.LeftPathAndNameVar.set('')
            if len(Vars.FileRightNameVar.get()) > 0:
                self.RightPathAndNameVar.set(os.path.join(Vars.RightPathEntry.get(), Vars.FileRightNameVar.get()))
            else:
                self.RightPathAndNameVar.set('')

            Vars.FileInfoTopLevelVar.deiconify()
            Vars.FileInfoTopLevelVar.lift()

            #Enable or disable button depending on file/directory status and location
            #Disable all 'both' buttons by default
            self.BothDeleteButton.config(state=DISABLED)
            self.BothDiffButton.config(state=DISABLED)
            self.BothCheckSUMButton.config(state=DISABLED)
            self.BothChangeDirButton.config(state=DISABLED)

            if len(Vars.FileLeftNameVar.get()) == 0: #left file/directory does not exist
                self.FileLeftSizeVar.set('No left file')
                self.LeftCopyButton.config(state=DISABLED)
                self.LeftDeleteButton.config(state=DISABLED)
                self.LeftRenameButton.config(state=DISABLED)
                self.LeftLocateButton.config(state=DISABLED)
                self.LeftCheckSumButton.config(state=DISABLED)
            else: #left file/directory does exist
                self.statinfoLeft = os.stat(self.LeftPathAndNameVar.get())
                self.FileLeftTypeVar.set(GetType(self.LeftPathAndNameVar.get()))
                self.FileLeftSizeVar.set('File size: {:,}'.format(self.statinfoLeft.st_size))
                self.FileLeftTimeVar.set('Modified:  %s' % time.ctime(self.statinfoLeft.st_mtime))
                self.FileLeftCheckSumVar.set(str(GetCheckSum(self.LeftPathAndNameVar.get())))
                self.LeftCopyButton.config(state=NORMAL)
                self.LeftDeleteButton.config(state=NORMAL)
                self.LeftRenameButton.config(state=NORMAL)
                self.LeftLocateButton.config(state=NORMAL)
                self.LeftCheckSumButton.config(state=NORMAL)

            if len(Vars.FileRightNameVar.get()) == 0: #right file/directory does not exist
                self.FileRightSizeVar.set('No right file')
                self.RightCopyButton.config(state=DISABLED)
                self.RightDeleteButton.config(state=DISABLED)
                self.RightRenameButton.config(state=DISABLED)
                self.RightLocateButton.config(state=DISABLED)
                self.RightCheckSumButton.config(state=DISABLED)
            else: #right file/directory does exist
                self.statinfoRight = os.stat(self.RightPathAndNameVar.get())
                self.FileRightTypeVar.set(GetType(self.RightPathAndNameVar.get()))
                self.FileRightSizeVar.set('File Size: {:,}'.format(self.statinfoRight.st_size))
                self.FileRightTimeVar.set('Modified:  %s' % time.ctime(self.statinfoRight.st_mtime))
                self.FileRightCheckSumVar.set(str(GetCheckSum(self.RightPathAndNameVar.get())))
                self.RightCopyButton.config(state=NORMAL)
                self.RightDeleteButton.config(state=NORMAL)
                self.RightRenameButton.config(state=NORMAL)
                self.RightLocateButton.config(state=NORMAL)
                self.RightCheckSumButton.config(state=NORMAL)

            #If both sides exist and they are the same type enable 'BothDeleteButton' and 'BothDiffButton' buttons
            if os.path.exists(self.LeftPathAndNameVar.get()) and \
               os.path.exists(self.RightPathAndNameVar.get()) and \
               self.FileLeftTypeVar.get() == self.FileRightTypeVar.get():
                self.BothDeleteButton.config(state=NORMAL)
                self.BothDiffButton.config(state=NORMAL)

            #If both sides exist and are not directories enable 'BothCheckSUMButton' buttons
            if os.path.isfile(self.LeftPathAndNameVar.get()) and \
               os.path.isfile(self.RightPathAndNameVar.get()):
                self.BothCheckSUMButton.config(state=NORMAL)

            #If both sides exist and both are directories enable 'Change Dir' button
            if os.path.isdir(self.LeftPathAndNameVar.get()) and \
               os.path.isdir(self.RightPathAndNameVar.get()):
                self.BothChangeDirButton.config(state=NORMAL)

            #Display the size, time and checksum status
            if len(Vars.FileRightNameVar.get()) > 0 and len(Vars.FileLeftNameVar.get()) > 0:
                if os.path.getsize(self.LeftPathAndNameVar.get()) != os.path.getsize(self.RightPathAndNameVar.get()):
                    self.SizeStatusVar.set('Sizes are different')
                    self.StatSize.config(bg='red')
                else:
                    self.SizeStatusVar.set('Sizes are the same')
                    self.StatSize.config(bg='green')

                self.UpdateCheckSumStatus()

                if self.FileLeftTypeVar.get() != self.FileRightTypeVar.get():
                    self.TypeStatusVar.set('Types are different')
                    self.StatType.config(bg='red')
                else:
                    self.TypeStatusVar.set('Types are the same')
                    self.StatType.config(bg='green')

                TimeDiff = abs(os.path.getmtime(self.LeftPathAndNameVar.get()) - os.path.getmtime(self.RightPathAndNameVar.get()))
                if TimeDiff < 1:
                    self.TimeStatusVar.set('Times are the same')
                    self.StatTime.config(bg='green')
                elif TimeDiff > Vars.FileTimeTriggerScaleVar.get():
                    self.TimeStatusVar.set('Times are different')
                    self.StatTime.config(bg='red')
                else:
                    self.TimeStatusVar.set('Times are close')
                    self.StatTime.config(bg='yellow')

            self.FileStatusVar.set('Status: ' + Vars.DataBox.get(t)[2])

            return 0
#------------------------------
    #Loads a project file
    #Lines without a ~ in the line are ignored and may be used as comments
    #Lines with # in position 0 may be used as comments
    def ProjectLoad(LoadType='none'):
        print('ProjectLoad ' + LoadType)
        if LoadType == 'default':
            Vars.ProjectFileNameVar.set(os.path.join(Vars.AuxDirectoryVar.get(), 'PyDiffTk.'+ Vars.ProjectFileExtensionVar.get()))
        else:
            Vars.ProjectFileNameVar.set(tkinter.filedialog.askopenfilename(
            defaultextension = Vars.ProjectFileExtensionVar.get(),
            filetypes = [('Project file','PyDiff*.' + Vars.ProjectFileExtensionVar.get()),('All files','*.*')],
            initialdir = os.path.dirname(Vars.AuxDirectoryVar.get()),
            initialfile = 'PyDiffTk.' + Vars.ProjectFileExtensionVar.get(),
            title = 'Load a PyDiffTk project file',
                parent = Main))
        Logger('Project Load ' + Vars.ProjectFileNameVar.get(), getframeinfo(currentframe()))

        ProjectEntry.delete(0,END)
        ProjectEntry.insert(0, Vars.ProjectFileNameVar.get())

        try:
            f = open(Vars.ProjectFileNameVar.get(), 'r')
        except IOError:
            tkinter.messagebox.showerror('Project file error', 'Requested file does not exit.\n>>' + Vars.ProjectFileNameVar.get() + '<<')
            return

        lines = f.readlines()
        f.close()
        print('PyDiffTk.py project file ' + sys.platform)
        try:
            if not 'PyDiffTk.py project file ' + sys.platform in lines[0]:
                tkinter.messagebox.showerror('Project file error', 'Not a valid project file.\nproject file' + '\n' + lines[0] )
                Logger('PyDiffTk.py project file  ' + lines[0].strip(), getframeinfo(currentframe()))
                return
        except:
                tkinter.messagebox.showerror('Project file error', 'Unable to read project file' +  Vars.ProjectFileNameVar.get())
                Logger('PyDiffTk.py project file. Unable to read file', getframeinfo(currentframe()))
                return

        del lines[0] # remove the first line so it won't be added to the comments list
        #Clear any widgets that need to be
        Vars.CommentsListVar = []
        for line in lines:
            if '~' in line and line[0] != '#':
                t = line.split('~')
                if 'False' in t[1]:
                    t[1] = 0
                elif 'True' in t[1]:
                    t[1] = 1
                if 'LeftPathEntry' in line:
                    x = os.path.normpath(t[1].strip())
                    UpdatePathEntry('Left',x)
                if 'RightPathEntry' in line:
                    x = os.path.normpath(t[1].strip())
                    UpdatePathEntry('Right',x)
                if 'FilterEntry' in line:
                    Vars.FilterEntry.delete(0,END)
                    Vars.FilterEntry.insert(0,t[1].strip())
                if 'SearchEntryBatch' in line:
                    Vars.SearchEntryBatch.delete(0,END)
                    Vars.SearchEntryBatch.insert(0,t[1].strip())
                if 'SearchEntryMain' in line:
                    Vars.SearchEntryMain.delete(0,END)
                    Vars.SearchEntryMain.insert(0,t[1].strip())
# TODO
                if 'LeftSearchVar' in line:
                    Vars.LeftSearchVar.set(int(t[1]))
                if 'RightSearchVar' in line:
                    Vars.RightSearchVar.set(int(t[1]))
                if 'StatusSearchVar' in line:
                    Vars.StatusSearchVar.set(int(t[1]))
                if 'MoreSearchVar' in line:
                    Vars.MoreSearchVar.set(int(t[1]))
                if  'Vars.CaseSearchVar' in line:
                    Vars.CaseSearchVar.set(int(t[1]))
                if 'SystemEditorVar' in line and len(t[1]) > 1:
                    Vars.SystemEditorVar.set(t[1].strip())
                if 'SystemDifferVar' in line and len(t[1]) > 1:
                    Vars.SystemDifferVar.set(t[1].strip())
                if 'SystemRenamerVar' in line and len(t[1]) > 1:
                    Vars.SystemRenamerVar.set(t[1].strip())
                if 'SystemLocaterVar' in line and len(t[1]) > 1:
                    Vars.SystemLocaterVar.set(t[1].strip())
                if 'ShowLeftCheckVar' in line:
                    Vars.ShowLeftCheckVar.set(int(t[1]))
                if 'ShowRightCheckVar' in line:
                    Vars.ShowRightCheckVar.set(int(t[1]))
                if 'ShowBothCheckVar' in line:
                    Vars.ShowBothCheckVar.set(int(t[1]))
                if 'ShowDiffCheckVar' in line:
                    Vars.ShowDiffCheckVar.set(int(t[1]))
                if 'ShowDirectoriesCheckVar' in line:
                    Vars.ShowDirectoriesCheckVar.set(int(t[1]))
                if 'AutoRefreshCheckVar' in line:
                    Vars.AutoRefreshCheckVar.set(int(t[1]))
                if 'ConfirmCopyCheckVar' in line:
                    Vars.ConfirmCopyCheckVar.set(int(t[1]))
                if 'ConfirmDeleteCheckVar' in line:
                    Vars.ConfirmDeleteCheckVar.set(int(t[1]))
                if 'ConfirmRenameCheckVar' in line:
                    Vars.ConfirmRenameCheckVar.set(int(t[1]))
                if 'RecycleCheckVar' in line:
                    Vars.RecycleCheckVar.set(int(t[1]))
                if 'CheckSumAutoVar' in line:
                    Vars.CheckSumAutoVar.set(int(t[1]))
                if 'CheckSumTypeVar' in line:
                    Vars.CheckSumTypeVar.set(int(t[1]))
                if 'FileTimeTriggerScaleVar~' in line:
                    Vars.FileTimeTriggerScaleVar.set(int(t[1]))
                if 'TriggerNumberOfFilesVar~' in line:
                    Vars.TriggerNumberOfFilesVar.set(int(t[1]))
            else:
                #All lines with # in the first column are comments
                #All line that do not contain ~ are comments
                Vars.CommentsListVar.append(line)

        if not SearchPath(Vars.SystemEditorVar.get()):
            Logger('File does not exist' + Vars.SystemEditorVar.get(),MessageBox = True)
        if not SearchPath(Vars.SystemDifferVar.get()):
            Logger('File does not exist' + Vars.SystemDifferVar.get(),MessageBox = True)
        if not SearchPath(Vars.SystemRenamerVar.get()):
            Logger('File does not exist' + Vars.SystemRenamerVar.get(),MessageBox = True)
        if not SearchPath(Vars.SystemLocaterVar.get()):
            tkinter.messagebox.showerror('File does not exist', Vars.SystemLocaterVar.get())

        Logger('Project opened: ' + Vars.ProjectFileNameVar.get(), getframeinfo(currentframe()))
        if Vars.AutoRefreshCheckVar.get(): FetchData()
#------------------------------
#Saves a project file
    def ProjectSave():
        Logger('ProjectSave ' + Vars.ProjectFileNameVar.get(), getframeinfo(currentframe()))

        Vars.ProjectFileNameVar.set(tkinter.filedialog.asksaveasfilename(
            defaultextension = Vars.ProjectFileExtensionVar.get(),
            filetypes = [('Project file','PyDiff*.' + Vars.ProjectFileExtensionVar.get()),
            ('All files','*.*')],
            initialdir = os.path.dirname(Vars.AuxDirectoryVar.get()),
            initialfile = 'PyDiffTk.' + Vars.ProjectFileExtensionVar.get(),
            title = 'Save a PyDiffTk project file',
            parent = Main))

        ProjectEntry.delete(0,END)
        ProjectEntry.insert(0, Vars.ProjectFileNameVar.get())

        try:
            f = open(Vars.ProjectFileNameVar.get(), 'w')
        except IOError:
            tkinter.messagebox.showerror('Project file error',
            'Requested file does not exist.\n>>' + Vars.ProjectFileNameVar.get() + '<<')
            return

        if not Vars.ProjectFileNameVar.get():
            return

        f.write('PyDiffTk.py project file ' + sys.platform + '\n')
        for item in Vars.CommentsListVar:
            f.write(item)
        f.write('LeftPathEntry~' + Vars.LeftPathEntry.get().strip() + '\n')
        f.write('RightPathEntry~' + Vars.RightPathEntry.get().strip() + '\n')
        f.write('FilterEntry~' + Vars.FilterEntry.get().strip() + '\n')
        f.write('SearchEntryMain~' + Vars.SearchEntryMain.get().strip() + '\n')
        f.write('SearchEntryBatch~' + Vars.SearchEntryBatch.get().strip() + '\n')
        f.write('LeftSearchVar~' + str(Vars.LeftSearchVar.get()) + '\n')
        f.write('RightSearchVar~' + str(Vars.RightSearchVar.get()) + '\n')
        f.write('StatusSearchVar~' + str(Vars.StatusSearchVar.get()) + '\n')
        f.write('MoreSearchVar~' + str(Vars.MoreSearchVar.get()) + '\n')
        f.write('CaseSearchVar~' + str(Vars.CaseSearchVar.get()) + '\n')
        f.write('SystemEditorVar~' + Vars.SystemEditorVar.get().strip() + '\n')
        f.write('SystemLocaterVar~' + Vars.SystemLocaterVar.get().strip() + '\n')
        f.write('SystemDifferVar~' + Vars.SystemDifferVar.get().strip() + '\n')
        f.write('SystemRenamerVar~' + Vars.SystemRenamerVar.get().strip() + '\n')
        f.write('ShowRightCheckVar~' + str(Vars.ShowRightCheckVar.get()) + '\n')
        f.write('ShowLeftCheckVar~' + str(Vars.ShowLeftCheckVar.get()) + '\n')
        f.write('ShowBothCheckVar~' + str(Vars.ShowBothCheckVar.get()) + '\n')
        f.write('ShowDiffCheckVar~' + str(Vars.ShowDiffCheckVar.get()) + '\n')
        f.write('ShowDirectoriesCheckVar~' + str(Vars.ShowDirectoriesCheckVar.get()) + '\n')
        f.write('AutoRefreshCheckVar~' + str(Vars.AutoRefreshCheckVar.get()) + '\n')
        f.write('ConfirmCopyCheckVar~' + str(Vars.ConfirmCopyCheckVar.get()) + '\n')
        f.write('ConfirmRenameCheckVar~' + str(Vars.ConfirmRenameCheckVar.get()) + '\n')
        f.write('ConfirmDeleteCheckVar~' + str(Vars.ConfirmDeleteCheckVar.get()) + '\n')
        f.write('RecycleCheckVar~' + str(Vars.RecycleCheckVar.get()) + '\n')
        f.write('CheckSumAutoVar~'+ str(Vars.CheckSumAutoVar.get()) + '\n')
        f.write('CheckSumTypeVar~' + str(Vars.CheckSumTypeVar.get()) + '\n')
        f.write('FileTimeTriggerScaleVar~' + str(Vars.FileTimeTriggerScaleVar.get()) + '\n')
        f.write('TriggerNumberOfFilesVar~' + str(Vars.TriggerNumberOfFilesVar.get()) + '\n')

        f.close()
        Logger('Project saved: ' + Vars.ProjectFileNameVar.get(), getframeinfo(currentframe()))
#------------------------------
#Edit a project file
    def ProjectEdit():
        Logger('Project edit: ' + ProjectEntry.get(), getframeinfo(currentframe()))
        ShowEditFile(ProjectEntry.get())
#------------------------------
#Show selected row in a message box
    def ShowRow():
        Current= str(Vars.DataBox.curselection())
        Current = re.sub('[(),\']','',Current)

        try:
            ShowRowTopLevel = Toplevel()
            ShowRowTopLevel.title('Show row')
            ShowRowTopLevel.wm_transient(Main)
            ShowRowTopLevelX = 250
            ShowRowTopLevelY = 120
            Mainsize = Main.geometry().split('+')
            x = int(Mainsize[1]) + (ShowRowTopLevelX / 2)
            y = int(Mainsize[2]) + (ShowRowTopLevelY / 2)
            ShowRowTopLevel.geometry("%dx%d+%d+%d" % (ShowRowTopLevelX, ShowRowTopLevelY, x, y))
            ShowRowTopLevel.resizable(1,0)

            Label(ShowRowTopLevel, text='Left:  ' + Vars.DataBox.get(Current)[0],
                relief=GROOVE).pack(expand=FALSE, fill=X)
            Label(ShowRowTopLevel, text='Right:  ' + Vars.DataBox.get(Current)[1],
                relief=GROOVE).pack(expand=FALSE, fill=X)
            Label(ShowRowTopLevel, text='Status:  ' + Vars.DataBox.get(Current)[2],
                relief=GROOVE).pack(expand=FALSE, fill=X)
            Label(ShowRowTopLevel, text='More:  ' + Vars.DataBox.get(Current)[3],
                relief=GROOVE).pack(expand=FALSE, fill=X)
            Button(ShowRowTopLevel, text='Close', command=lambda : ShowRowTopLevel.destroy()).pack()
        except:
            pass

#------------------------------
    class Batch:
        AbortVar = BooleanVar()
        AbortVar.set(False)

        def ShowBatchForm(self):
            Vars.BatchTopLevelVar.deiconify()
            Vars.BatchTopLevelVar.wm_transient(Main)
            BatchTopLevelX = 530
            BatchTopLevelY = 250
            Mainsize = Main.geometry().split('+')
            x = int(Mainsize[1]) + (BatchTopLevelX / 2)
            y = int(Mainsize[2]) + (BatchTopLevelY / 2)

            Vars.BatchTopLevelVar.geometry("%dx%d+%d+%d" % (BatchTopLevelX, BatchTopLevelY, x, y))
            Vars.BatchTopLevelVar.resizable(1,0)
            Logger('ShowBatchForm', getframeinfo(currentframe()))

        def BuildBatchForm(self):
            Vars.BatchTopLevelVar = Toplevel()
            Vars.BatchTopLevelVar.title('Batch')
            Vars.BatchTopLevelVar.withdraw()
            Vars.BatchTopLevelVar.wm_transient(Main)

            #Get currently selected line
            def GetCurrentSelection():
                Current= str(Vars.DataBox.curselection())
                Vars.ShowLineNumberVar.set(Current)
                Vars.ShowLineNumberVar.set(str(Vars.DataBox.curselection()) +
                 ' of ' + str(Vars.DataBox.size()-1))
                Current = re.sub('[(),\']','',Current)
                if ' ' in Current: Current = '-1'
                return Current

            #Get currently selected line information and total line count
            def SelectBlockRows():
                StartRow = re.sub('[(),\']','',Vars.StartRowEntry.get())
                StopRow = re.sub('[(),\']','',Vars.StopRowEntry.get())
                print('start>'+StartRow+'<', 'stop>'+StopRow+'<')
                Vars.DataBox.selection_clear(0,199999)
                if StartRow.isdigit() and StopRow.isdigit():
                    for Row in range(int(StartRow), int(StopRow)+1):
                        Vars.DataBox.selection_set(Row)
                        Vars.DataBox.see(Row)
                Update()
                Vars.BatchNumberItemsVar.set(Vars.ShowLineNumberVar.get())

            #Lists displaylist to command line
            def TestTheData():
                Logger(str(Vars.SelectedListVar), getframeinfo(currentframe()))
                print(Vars.SelectedListVar)
                Vars.DataBox.selection_clear(0,199999)
                for x in Vars.SelectedListVar:
                    print(x, Vars.DataBox.get(x))
                    Vars.DataBox.selection_set(x)
                    Vars.DataBox.see(x)


            #Fetch the first line to perform the batch action on
            def GetLineNumberStart():
                ClearSelectedList
                tmp = GetCurrentSelection()
                print(MyTrace(getframeinfo(currentframe())), tmp)
                if len(tmp) > 0:
                    Vars.StartRowEntry.insert(0, tmp)
                else:
                    Vars.StartRowEntry.insert(0, 0)
                SelectBlockRows()

            #Fetch the last line to perform the batch action on
            def GetLineNumberStop():
                Vars.StopRowEntry.delete(0, END)
                tmp = GetCurrentSelection()
                print(MyTrace(getframeinfo(currentframe())), tmp)
                if len(tmp) > 0:
                    Vars.StopRowEntry.insert(0, tmp)
                else:
                    Vars.StopRowEntry.insert(0, str(Vars.DataBox.size()-1))
                SelectBlockRows()

            StartRow = '-1'
            StopRow = '-1'
            BatchStatusVar = StringVar()
            BatchWorkingCount = 0
            BatchStatusVar.set('This is batch mode')

            #TODO VerifyInput(trace)
            def VerifyInput(trace):
                StartRow = str(Vars.StartRowEntry.get())
                StopRow = str(Vars.StopRowEntry.get())
                BatchStatusVar.set(trace + '\nSuccess')
                TestMessage = ''
                if not StartRow.isdigit() or not StopRow.isdigit():
                    TestMessage = 'Start and stop row must be positive interger values'
                    BatchStatusVar.set(trace + '\n' + TestMessage)
                    tkinter.messagebox.showerror('Bad entry value',trace + '\n' + TestMessage)
                    SplashScreen('Batch copy is closing', False)
                    return 1
                Logger('Start row:' + str(StartRow) + '  Number of items:' + str(Vars.DataBox.size()-1), getframeinfo(currentframe()))
                if int(StartRow) < 0:
                    TestMessage += '\nStart must be 0 or more\n'
                if int(StartRow) > int(Vars.DataBox.size()-1):
                    TestMessage += '\nStart must be less than or equal to ' + str(Vars.DataBox.size()-1)
                if int(StartRow) > int(StopRow):
                    TestMessage += '\nStart must be less than or equal to stop'
                if int(StopRow) > int(Vars.DataBox.size()-1):
                    TestMessage += '\nStop must be less than or equal to ' + str(Vars.DataBox.size()-1)
                if len(TestMessage) > 0:
                    TestMessage += '\nStart: ' + str(StartRow) + ' Stop: ' + str(StopRow)
                    BatchStatusVar.set(trace + '\n' + TestMessage)
                    tkinter.messagebox.showerror('Bad entry value',trace + '\n' + TestMessage)
                    return 1
                return 0

            def BatchRefresh():
                GetLineNumberStart()
                GetLineNumberStop()
                Vars.BatchNumberItemsVar.set(str(Vars.DataBox.size()-1))

            def GetFilePathList(trace): #This gets the selected items and puts them in FilePathList
                FilePathList = [] #Vars.SelectedListVar
                if VerifyInput(trace) != 0: return
                Vars.DataBox.selection_clear(0,199999)
                try:
                    Vars.DataBox.selection_set(int(Vars.StartRowEntry.get()), int(Vars.StopRowEntry.get()))
                except: return

                Vars.ShowLineNumberVar.set(str(Vars.DataBox.curselection()) + ' of ' + str(Vars.DataBox.size()-1))
                for i in range(int(Vars.StartRowEntry.get()), int(Vars.StopRowEntry.get())+1):
                    Vars.FileLeftNameVar.set(Vars.DataBox.get(i)[0])
                    Vars.FileRightNameVar.set(Vars.DataBox.get(i)[1])

                    Vars.FileLeftNameVar.set(Vars.DataBox.get(i)[0])
                    Vars.FileRightNameVar.set(Vars.DataBox.get(i)[1])
                    if len(Vars.FileLeftNameVar.get()) < 1:
                        left = Vars.LeftPathEntry.get() + os.sep
                    else:
                        left = os.path.join(Vars.LeftPathEntry.get(), Vars.FileLeftNameVar.get())
                    if len(Vars.FileRightNameVar.get()) < 1:
                        right = Vars.RightPathEntry.get() + os.sep
                    else:
                        right = os.path.join(Vars.RightPathEntry.get(), Vars.FileRightNameVar.get())
                    FilePathList.append(left + '~' + right)
                print('kkkkkkkkk',FilePathList,MyTrace(getframeinfo(currentframe())))
                return FilePathList

            #The batch rename functions call external renamer programs
            #Linux: /usr/bin/pyrenamer
            #Windows (x64): C:\Program Files (x86)\Ant Renamer\Renamer.exe
            #Windows (x32): C:\Program Files\Ant Renamer\Renamer.exe
            def BatchRename(Trace):
                Logger('Batch rename ' + Trace, getframeinfo(currentframe()))
                if Trace == 'left': #Rename left
                    StartFile(Vars.SystemRenamerVar.get(), Vars.LeftPathEntry.get())
                elif Trace == 'right': #Rename right
                    StartFile(Vars.SystemRenamerVar.get(), Vars.RightPathEntry.get())
                else:
                    Logger('ERROR with batch rename trace ' + Trace + ' ' + Vars.SystemRenamerVar.get(), getframeinfo(currentframe()))
                return

            def BatchRenameRight():
                BatchRename('right')
            def BatchRenameLeft():
                BatchRename('left')

            #This either sends item to trash or deletes them depending on options setting
            def BatchDeleteOrTrash(Trace):
                SplashScreen('Batch Delete is running:' + Trace, True)
                self.AbortVar.set(False)
                BatchDeleteList = GetFilePathList('Batch delete')
                if BatchDeleteList == None: return
                Logger('Batch delete ' + Trace, getframeinfo(currentframe()))
                BatchDeleteCount = 0

                for RowStr in BatchDeleteList:
                    Main.update_idletasks()
                    if self.AbortVar.get(): break
                    BatchDeleteCount += 1
                    BatchStatusVar.set('Batch delete:' + str(BatchDeleteCount))
                    Main.update_idletasks()
                    RowStrSplit = RowStr.split('~')
                    if Trace == 'left':
                        Logger('Delete left. ' + RowStrSplit[0], getframeinfo(currentframe()))
                        if os.path.exists(RowStrSplit[0]) and os.path.isfile(RowStrSplit[0]):
                            if Vars.RecycleCheckVar.get() == 0:
                                RemoveAFile(RowStrSplit[0], Trash = False)
                            else:
                                RemoveAFile(RowStrSplit[0], Trash = True)
                    elif Trace == 'right': #Delete right
                        Logger('Delete right. ' + RowStrSplit[0], getframeinfo(currentframe()))
                        if os.path.exists(RowStrSplit[1]) and os.path.isfile(RowStrSplit[1]):
                            if Vars.RecycleCheckVar.get() == 0:
                                RemoveAFile(RowStrSplit[1], Trash = False)
                            else:
                                RemoveAFile(RowStrSplit[1], Trash = True)
                    elif Trace == 'auto': #Delete auto deletes whatever exists
                        Logger('Delete auto. ' + RowStrSplit[0], getframeinfo(currentframe()))
                        if os.path.exists(RowStrSplit[0]) and os.path.isfile(RowStrSplit[0]):
                            if Vars.RecycleCheckVar.get() == 0:
                                RemoveAFile(RowStrSplit[0], Trash = False)
                                #os.remove(RowStrSplit[0])
                            else:
                                RemoveAFile(RowStrSplit[0], Trash = True)
                                #send2trash(RowStrSplit[0])

                        if os.path.exists(RowStrSplit[1]) and os.path.isfile(RowStrSplit[1]):
                            if Vars.RecycleCheckVar.get() == 0:
                                RemoveAFile(RowStrSplit[1], Trash = False)
                                #os.remove(RowStrSplit[1])
                            else:
                                #send2trash(RowStrSplit[1])
                                RemoveAFile(RowStrSplit[1], Trash = True)
                    else: Logger('ERROR with batch delete ' + Trace, getframeinfo(currentframe()))
                Vars.StartRowEntry.delete(0, END)
                Vars.StopRowEntry.delete(0, END)
                SplashScreen('Batch Delete is closing: ' + Trace, False)
                if Vars.AutoRefreshCheckVar.get():
                    FetchData()
                    update()
                    Vars.BatchNumberItemsVar.set(str(Vars.DataBox.size()-1))
            #---------------------------------
            def BatchCopy(Trace):
                self.AbortVar.set(False)
                BatchCopyList = GetFilePathList('Batch copy')
                if BatchCopyList == None: return
                SplashScreen('Batch copy is running ' + Trace, True)

                Logger('Batch copy ' + Trace, getframeinfo(currentframe()))
                BatchCopyCount = 0
                for RowStr in BatchCopyList:
                    Main.update_idletasks()
                    if self.AbortVar.get(): break
                    BatchCopyCount += 1
                    BatchStatusVar.set('Batch copy ' + str(BatchCopyCount))
                    Main.update_idletasks()
                    RowStrSplit = RowStr.split('~')
                    Logger(str(RowStrSplit), getframeinfo(currentframe()))
                    if Trace == 'right': #Copy right
                        src = RowStrSplit[1] #right
                        dst = RowStrSplit[0] #left
                        print(getframeinfo(currentframe())[1], src, dst)
                        CopyAFile('Batch copy right to left ' + Trace , src, dst, True)
                    elif Trace == 'left': #Copy left
                        src = RowStrSplit[0] #left
                        dst = RowStrSplit[1] #right
                        print(getframeinfo(currentframe())[1], src, dst)
                        CopyAFile('Batch copy left to right ' + Trace , src, dst, True)
                    elif Trace == 'auto': #Copy auto
                        src = RowStrSplit[1] #right
                        dst = RowStrSplit[0] #left
                        print(getframeinfo(currentframe())[1], Trace, src, dst)
                        CopyAFile('Batch copy right to left ' + Trace, src, dst, True)
                        src = RowStrSplit[0] #right
                        dst = RowStrSplit[1] #left
                        print(getframeinfo(currentframe())[1], Trace, src, dst)
                        CopyAFile('Batch copy right to left ' + Trace, src, dst, True)
                Vars.StartRowEntry.delete(0, END)
                Vars.StopRowEntry.delete(0, END)
                if Vars.AutoRefreshCheckVar.get(): FetchData()
                Vars.StatusVar.set('Batch copy complete. Files copied: ' +str(BatchCopyCount))
                SplashScreen('Batch copy is closing ' + Trace, False)

            #---------------------------------
            Logger('Batch', getframeinfo(currentframe()))
            Vars.BatchTopLevelVar = Toplevel()
            Vars.BatchTopLevelVar.title('Batch')

            #Status frame and abort
            BatchFrame1 = Frame(Vars.BatchTopLevelVar, relief=SUNKEN, bd=1)
            BatchFrame1.pack(side=TOP, expand=FALSE, fill=X)

            #Block mode
            BatchFrame2 = Frame(Vars.BatchTopLevelVar, relief=SUNKEN, bd=1)
            BatchFrame2.pack(side=TOP, expand=FALSE, fill=X)


            #This frame is for search
            BatchFrame3 = Frame(Vars.BatchTopLevelVar, relief=SUNKEN, bd=1)
            BatchFrame3.pack(side=TOP, expand=FALSE, fill=X)

            #This frame is for add/remove/clear buttons
            BatchFrame4 = Frame(Vars.BatchTopLevelVar, relief=SUNKEN, bd=1)
            BatchFrame4.pack(side=TOP, expand=FALSE, fill=X)

            #The following frames are used for the action buttons
            BatchFrame5 = Frame(Vars.BatchTopLevelVar, relief=SUNKEN, bd=1)
            BatchFrame5.pack(side=TOP, fill=X)

            BatchFrame5a = Frame(BatchFrame5, relief=SUNKEN, bd=1)
            BatchFrame5a.pack(side=LEFT, expand=TRUE, fill=Y)

            BatchFrame5b = Frame(BatchFrame5, relief=SUNKEN, bd=1)
            BatchFrame5b.pack(side=LEFT, expand=TRUE, fill=Y)

            BatchFrame5c = Frame(BatchFrame5, relief=SUNKEN, bd=1)
            BatchFrame5c.pack(side=LEFT, expand=TRUE, fill=Y)

            #Display number of lines
            BatchFrame6 = Frame(Vars.BatchTopLevelVar, relief=SUNKEN, bd=1)
            BatchFrame6.pack(side=TOP, expand=TRUE, fill=X)

            #---------------------------------
            BatchStatus = Label(BatchFrame1,  textvariable=BatchStatusVar, relief=GROOVE)
            BatchStatus.pack(fill=BOTH, expand=True,side=LEFT)
            ToolTip(BatchStatus,'Displays batch status')

            AbortCheck = Checkbutton(BatchFrame1, text='Abort', variable=self.AbortVar)
            AbortCheck.pack(side=LEFT)
            ToolTip(AbortCheck,'Abort batch operations')

            #---------------------------------
            #Block select controls
            StartRowButton = Button(BatchFrame2, text='Start row:', command=GetLineNumberStart)
            StartRowButton.pack(side=LEFT)
            ToolTip(StartRowButton,'Fetch the first line to perform the batch action on')
            Vars.StartRowEntry = Entry(BatchFrame2, width=6)
            Vars.StartRowEntry.pack(side=LEFT)
            Vars.StartRowEntry.bind('<Return>', lambda x: SelectBlockRows())
            #Vars.StartRowEntry.bind('<Leave>', lambda x: SelectBlockRows())
            ToolTip(Vars.StartRowEntry,'Enter the first line to perform the batch action on')

            StopRowButton = Button(BatchFrame2, text='Stop row:',  command=GetLineNumberStop)
            StopRowButton.pack(side=LEFT)
            ToolTip(StopRowButton,'Fetch the last line to perform the batch action on')
            Vars.StopRowEntry = Entry(BatchFrame2, width=6)
            Vars.StopRowEntry.pack(side=LEFT)
            Vars.StopRowEntry.bind('<Return>', lambda x: SelectBlockRows())
            #Vars.StopRowEntry.bind('<Leave>', lambda x: SelectBlockRows())
            ToolTip(Vars.StopRowEntry,'Enter the last line to perform the batch action on')

            #BatchRefreshButton = Button(BatchFrame2, text='Select', command=SelectBlockRows, width=7)
            #BatchRefreshButton.pack(side=LEFT)
            #ToolTip(BatchRefreshButton,'Get currently selected line information and total line count')

            # The follow will test that the selected data is valid
            BatchTestButton = Button(BatchFrame2, text='Test', command=TestTheData, width=7)
            BatchTestButton.pack(side=RIGHT)
            ToolTip(BatchTestButton,'Lists displaylist to command line')

            #---------------------------------
            #Search BatchFrame3
            Checkbutton(BatchFrame3, text='Left', variable=Vars.LeftSearchVar ).pack(side=LEFT)
            Checkbutton(BatchFrame3, text='Right', variable=Vars.RightSearchVar).pack(side=LEFT)
            Checkbutton(BatchFrame3, text='Status', variable=Vars.StatusSearchVar).pack(side=LEFT)
            Checkbutton(BatchFrame3, text='More', variable=Vars.MoreSearchVar).pack(side=LEFT)
            Checkbutton(BatchFrame3, text='Case', variable=Vars.CaseSearchVar).pack(side=LEFT)

            SearchButtonBatch = Button(BatchFrame3, text='Search', width=8, command=lambda:SearchData('batch'))
            SearchButtonBatch.pack(side=LEFT)
            ToolTip(SearchButtonBatch,'Enter a Search string to find certain entries')
            Vars.SearchEntryBatch = Entry(BatchFrame3)
            Vars.SearchEntryBatch.bind('<Return>',lambda x: SearchData('batch'))
            Vars.SearchEntryBatch.pack(side=LEFT, expand=TRUE, fill=X)
            ToolTip(Vars.SearchEntryBatch,'Enter a Search string to find certain entries')
            Vars.SearchEntryBatch.delete(0,END)

            #This frame is for add/remove/clear/show buttons
            AddRowsButton = Button(BatchFrame4, text='Add row(s)', command=AddSelectedToList)
            AddRowsButton.pack(side=LEFT)
            ToolTip(AddRowsButton,'Add all selected rows to display list')

            RemoveRowButton = Button(BatchFrame4, text='Remove row', command=RemoveARow)
            RemoveRowButton.pack(side=LEFT)
            ToolTip(RemoveRowButton,'Remove the selected row from display list')

            ClearAllRowsButton = Button(BatchFrame4, text='Clear all rows', command=ClearSelectedList)
            ClearAllRowsButton.pack(side=LEFT)
            ToolTip(ClearAllRowsButton,'Remove all rows from display list')

            ShowRowsButton = Button(BatchFrame4, text='Show rows', command=ShowSelectedList)
            ShowRowsButton.pack(side=LEFT)
            ToolTip(ShowRowsButton,'Show all selected rows')

            #---------------------------------
            #Action buttons BatchFrame5
            DeleteLeftButton = Button(BatchFrame5a, text='Delete left',state=NORMAL, width=20, command=lambda: BatchDeleteOrTrash('left'))
            DeleteLeftButton.pack(anchor='w')
            ToolTip(DeleteLeftButton,'Batch delete left')

            DeleteRightButton = Button(BatchFrame5a, text='Delete right',state=NORMAL, width=20, command=lambda: BatchDeleteOrTrash('right'))
            DeleteRightButton.pack(anchor='w')
            ToolTip(DeleteRightButton,'Batch delete right')

            DeleteAutoButton = Button(BatchFrame5a, text='Delete auto',state=NORMAL, width=20,command=lambda: BatchDeleteOrTrash('auto'))
            DeleteAutoButton.pack(anchor='w')
            ToolTip(DeleteAutoButton,'Batch delete auto')
            #---------------------------------
            CopyLeftButton = Button(BatchFrame5b, text='Copy left to right', state=NORMAL, width=20, command=lambda: BatchCopy('left'))
            CopyLeftButton.pack(anchor='w')
            ToolTip(CopyLeftButton,'Batch copy left')

            CopyRightButton = Button(BatchFrame5b, text='Copy right to left', state=NORMAL, width=20,command=lambda: BatchCopy('right'))
            CopyRightButton.pack(anchor='w')
            ToolTip(CopyRightButton,'Batch copy Right')

            CopyAutoButton = Button(BatchFrame5b, text='Copy auto', state=NORMAL, width=20,command=lambda: BatchCopy('auto'))
            CopyAutoButton.pack(anchor='w')
            ToolTip(CopyAutoButton,'Batch copy auto')
            #---------------------------------
            RenameLeftButton = Button(BatchFrame5c, text='Rename left',state=NORMAL, width=20, command=BatchRenameLeft)
            RenameLeftButton.pack(anchor='w')
            ToolTip(RenameLeftButton,'Batch rename left')

            RenameRightButton = Button(BatchFrame5c, text='Rename right',state=NORMAL, width=20,
            command=BatchRenameRight)
            RenameRightButton.pack(anchor='w')
            ToolTip(RenameRightButton,'Batch rename right')
            #-------------------
            BatchSelectedLine = Button(BatchFrame6, textvariable=Vars.BatchNumberItemsVar,
               command=SelectBlockRows, relief=GROOVE)
            BatchSelectedLine.pack(side=LEFT, expand=TRUE, fill=BOTH)
            ToolTip(BatchSelectedLine,'Number of lines in data display')

            Vars.BatchTopLevelVar.withdraw()

            def BatchXButton():
                Logger('Batch X button detected', getframeinfo(currentframe()))
                Vars.BatchTopLevelVar.withdraw()
            Vars.BatchTopLevelVar.protocol('WM_DELETE_WINDOW', BatchXButton)

#------------------------------
#Any entry, scale or other widgets go here
    class Options:
        def ShowOptionsForm(self):
            #Deiconify the TopLevelVar and put it in the center of the main window
            Vars.OptionsTopLevelVar.deiconify()
            Main.update()
            OptionsTopLevelSizeX = 350
            OptionsTopLevelSizeY = 175
            MainGeo = Main.geometry().split('+')
            MainPosition = MainGeo[0].split('x')
            x = int(MainGeo[1]) + (OptionsTopLevelSizeX / 2)
            y = int(MainGeo[2]) + (OptionsTopLevelSizeY / 2)

            Vars.OptionsTopLevelVar.geometry("%dx%d+%d+%d" % (OptionsTopLevelSizeX, OptionsTopLevelSizeY, x, y))
            Vars.OptionsTopLevelVar.resizable(1,0)
            Vars.OptionsTopLevelVar.wm_transient(Main)

            Logger('ShowOptionsForm', getframeinfo(currentframe()))

        def BuildOptionsForm(self):
            Logger('BuildOptionsForm', getframeinfo(currentframe()))
            Vars.OptionsTopLevelVar = Toplevel()
            Vars.OptionsTopLevelVar.title('Options')
            Vars.OptionsTopLevelVar.withdraw()

            def OptionsXButton():
                Logger('Options X button detected', getframeinfo(currentframe()))
                Vars.OptionsTopLevelVar.withdraw()
            Vars.OptionsTopLevelVar.protocol('WM_DELETE_WINDOW', OptionsXButton)

            FileTimeTriggerScale = Scale(Vars.OptionsTopLevelVar, from_=0, to=5000, \
            variable=Vars.FileTimeTriggerScaleVar, orient=HORIZONTAL, \
            tickinterval=1000, label='File time difference trigger (seconds)',length=200)
            FileTimeTriggerScale.pack(fill='x')

            TriggerNumberOfFilesScale = Scale(Vars.OptionsTopLevelVar, from_=0, to=500, \
            variable=Vars.TriggerNumberOfFilesVar, orient=HORIZONTAL, \
            tickinterval=100, label='Trigger number of files', length=200)
            TriggerNumberOfFilesScale.pack(fill='x')
#------------------------------
    def ShowEditFile(FileName=None):
        if FileName == None:
            FileName = tkinter.filedialog.askopenfilename(
                defaultextension='.*',
                initialdir=os.path.dirname(os.path.realpath(Vars.AuxDirectoryVar.get())),
                filetypes=[('All files','*.*')],
                title='Show/Edit a file',
                parent=Vars.OptionsTopLevelVar)

        Logger('Show/Edit file: >>' + FileName + '<<', getframeinfo(currentframe()))
        FileName = os.path.normpath(FileName)
        try:
            StartFile(Vars.SystemEditorVar.get(), FileName)
        except IOError:
            tkinter.messagebox.showerror('Show/Edit file error', 'Requested file does not exit.\n ' + FileName)
            return
#------------------------------
    def ClearLogs():
        os.system(['clear','cls'][os.name == 'nt'])
#------------------------------
#Some debug stuff
    def About():
        Logger('About ' + main.Vars.StartUpDirectoryVar.get(), getframeinfo(currentframe()))
        tkinter.messagebox.showinfo('About',  main.Vars.StartUpDirectoryVar.get() +
          '\n' + Main.geometry() +
          '\n' + str(Main.winfo_screenwidth()) + 'x' +  str(Main.winfo_screenheight()) +
          '\n' + 'Python version: ' + platform.python_version() +
          '\n' + platform.platform())
#------------------------------
#The help file (someday)
    def Help():
        Logger('Help ' + main.Vars.StartUpDirectoryVar.get(), getframeinfo(currentframe()))

        try:
            f = open(Vars.HelpFileVar.get(), 'r')
        except IOError:
            tkinter.messagebox.showerror('Help file error', 'Requested file does not exist.\n>>' + Vars.HelpFileVar.get() + '<<')
            return
        lines = f.readlines()
        f.close()
        help = ''
        for l in lines:
            help = help + l
        tkinter.messagebox.showinfo('Help', help)
#------------------------------
#Swap the left and right entry boxes (other menu)
    def SwapLeftAndRight():
        Logger('SwapLeftAndRight', getframeinfo(currentframe()))
        temp1 = Vars.LeftPathEntry.get()
        temp2 = Vars.RightPathEntry.get()
        Vars.LeftPathEntry.delete(0,END)
        Vars.LeftPathEntry.insert(0,temp2)
        Vars.RightPathEntry.delete(0,END)
        Vars.RightPathEntry.insert(0,temp1)
#------------------------------
#Show Disk Space
    def DiskSpace():
        DiskSpace = shutil.disk_usage('/')
        tkinter.messagebox.showinfo('Disk space',
            'Free: %f Gbytes' %(DiskSpace.free/1e9) +'\n'+
            'Used: %f Gbytes' %(DiskSpace.used/1e9) +'\n'+
            'Total: %f Gbytes' %(DiskSpace.total/1e9))
        Logger('DiskSpace', getframeinfo(currentframe()))
#------------------------------
#This where the program starts up
    #default_font = tkFont.nametofont("TkFixedFont")
    #default_font.configure(size=9)
    Main.option_add('*Font', 'courier 10')

    Vars.FileRenameTopLevelVar = Toplevel()
    Vars.FileRenameTopLevelVar.title('File rename')
    Vars.FileRenameTopLevelVar.withdraw()

    ControlFrame1 = Frame(Main, relief=SUNKEN, bd=1)
    ControlFrame1.pack(side=TOP, expand=FALSE, fill=X)

    ControlFrame2 = Frame(Main, relief=SUNKEN, bd=1)
    ControlFrame2.pack(side=TOP, expand=FALSE, fill=X)

    ControlFrame3 = Frame(Main, relief=SUNKEN, bd=1)
    ControlFrame3.pack(side=TOP, expand=FALSE, fill=X)

    ControlFrame4 = Frame(Main, relief=SUNKEN, bd=1)
    ControlFrame4.pack(side=TOP, expand=FALSE, fill=X)

    DataFrame = Frame(Main, relief=GROOVE, bd=5)
    DataFrame.pack(side=TOP, expand=TRUE, fill=BOTH)
    Vars.DataBox = MultiListbox(DataFrame,
            (('Left', 45),
             ('Right', 45),
             ('Status', 3),
             ('More',40)))

    ToolTip(Vars.DataBox, text='This is where the data is displayed')
    Vars.DataBox.pack(expand=TRUE, fill=BOTH)

    menubar = Menu(Main)
    Main['menu'] = menubar
    DirectoriesSelectMenu = Menu(menubar)
    ProjectsMenu = Menu(menubar)
    OptionsMenu = Menu(menubar)
    OtherMenu = Menu(menubar)
    HelpMenu = Menu(menubar)

    menubar.add_cascade(menu=DirectoriesSelectMenu, label='Directories')
    DirectoriesSelectMenu.add_command(label='Select both directories', command=lambda: FetchDirectories('Both'))
    DirectoriesSelectMenu.add_command(label='Select left directory', command=lambda: FetchDirectories('Left'))
    DirectoriesSelectMenu.add_command(label='Select right directory', command=lambda: FetchDirectories('Right'))

    #DirectoriesSelectMenu.add_command(label='History', command=HistoryInstance.HistoryGoto)

    menubar.add_cascade(menu=ProjectsMenu, label='Projects')
    ProjectsMenu.add_command(label='Load', command=ProjectLoad)
    ProjectsMenu.add_command(label='Save', command=ProjectSave)
    ProjectsMenu.add_command(label='Edit', command=ProjectEdit)

    menubar.add_cascade(menu=OptionsMenu, label='Options')
    OptionsMenu.add_checkbutton(label='Auto refresh', variable=Vars.AutoRefreshCheckVar)
    OptionsMenu.add_checkbutton(label='Confirm copy', variable=Vars.ConfirmCopyCheckVar)
    OptionsMenu.add_checkbutton(label='Confirm delete', variable=Vars.ConfirmDeleteCheckVar)
    OptionsMenu.add_checkbutton(label='Confirm rename', variable=Vars.ConfirmRenameCheckVar)
    OptionsMenu.add_checkbutton(label='Recycle', variable=Vars.RecycleCheckVar)
    OptionsMenu.add_separator()
    OptionsMenu.add_checkbutton(label='Auto checksum', variable=Vars.CheckSumAutoVar)

    OptionsMenu.add_radiobutton(label='CRC32', variable=Vars.CheckSumTypeVar, value=1)
    OptionsMenu.add_radiobutton(label='MD5', variable=Vars.CheckSumTypeVar, value=2)
    OptionsMenu.add_radiobutton(label='SHA1', variable=Vars.CheckSumTypeVar, value=3)

    OptionsMenu.add_separator()
    OptionsMenu.add_checkbutton(label='Show both', variable=Vars.ShowBothCheckVar)
    OptionsMenu.add_checkbutton(label='Show diff', variable=Vars.ShowDiffCheckVar)
    OptionsMenu.add_checkbutton(label='Show left', variable=Vars.ShowLeftCheckVar)
    OptionsMenu.add_checkbutton(label='Show right', variable=Vars.ShowRightCheckVar)
    OptionsMenu.add_checkbutton(label='Show directories', variable=Vars.ShowDirectoriesCheckVar)

    OptionsMenu.add_separator()
    OptionsInstance = Options()
    OptionsMenu.add_command(label='Other settings',command=OptionsInstance.ShowOptionsForm)

    menubar.add_cascade(menu=OtherMenu, label='Other')
    OtherMenu.add_command(label='Swap left and right',command=SwapLeftAndRight)
    OtherMenu.add_command(label='Show disk space',command=DiskSpace)
    OtherMenu.add_command(label='Show/Edit file', command=ShowEditFile)
    OtherMenu.add_command(label='Clear logs', command=ClearLogs)
    OtherMenu.add_command(label='Clear all', command=ClearAll)

    menubar.add_cascade(menu=HelpMenu, label='Help')
    HelpMenu.add_command(label='About', command=About)
    HelpMenu.add_command(label='Help', command=Help)
    HelpMenu.add_command(label='Quit', command=Quit)

    FileInfoInstance = FileInfo()
    FileInfoButton = Button(ControlFrame2, text='File info',command=FileInfoInstance.ShowFileInfo)
    FileInfoButton.pack(side=LEFT)
    ToolTip(FileInfoButton, text='Show file info form')

    BatchInstance = Batch()
    BatchButton = Button(ControlFrame2, text='Batch',command=BatchInstance.ShowBatchForm)
    BatchButton.pack(side=LEFT)
    ToolTip(BatchButton, text='Show batch form')

    Statuslabel = Label(ControlFrame2, textvariable=Vars.StatusVar, relief=GROOVE)
    Statuslabel.pack(side=LEFT, expand=TRUE, fill=X)
    Vars.StatusVar.set('Status: Program started')
    ToolTip(Statuslabel, text='Show the status')

    ShowLineNumber = Label(ControlFrame2, textvariable=Vars.ShowLineNumberVar, relief=GROOVE)
    ShowLineNumber.pack(side=LEFT, expand=TRUE, fill=X)
    ToolTip(ShowLineNumber, text='Show line numbers\nAll values are zero based')

    def BothX():
        if Vars.AutoRefreshCheckVar.get(): FetchData()
        Logger('BothVar: ' + str(Vars.ShowBothCheckVar.get()), getframeinfo(currentframe()))
        ShowBoth = Checkbutton(ControlFrame1, text='Both', variable=Vars.ShowBothCheckVar, command=BothX)
        ShowBoth.pack(side=LEFT)
        ToolTip(ShowBoth,'Show items that exist in both left and right directories and are the same')
        Vars.ShowBothCheckVar.set(TRUE)

    def DiffX():
        if Vars.AutoRefreshCheckVar.get(): FetchData()
        Logger('DiffVar: ' + str(Vars.ShowDiffCheckVar.get()), getframeinfo(currentframe()))
        ShowDiff = Checkbutton(ControlFrame1, text='Diff', variable=Vars.ShowDiffCheckVar, command=DiffX)
        ShowDiff.pack(side=LEFT)
        ToolTip(ShowDiff,'Show items that exist in both left and right directories but are different')
        Vars.ShowDiffCheckVar.set(TRUE)

    def LeftX():
        if Vars.AutoRefreshCheckVar.get(): FetchData()
        Logger('LeftVar: ' + str(Vars.ShowLeftCheckVar.get()), getframeinfo(currentframe()))
        ShowLeft = Checkbutton(ControlFrame1, text='Left', variable=Vars.ShowLeftCheckVar, command=LeftX)
        ShowLeft.pack(side=LEFT)
        ToolTip(ShowLeft,'Show items that exist in the left directory only')
        Vars.ShowLeftCheckVar.set(FALSE)

    def RightX():
        if Vars.AutoRefreshCheckVar.get(): FetchData()
        Logger('RightVar: ' + str(Vars.ShowRightCheckVar.get()), getframeinfo(currentframe()))
        ShowRight = Checkbutton(ControlFrame1, text='Right', variable=Vars.ShowRightCheckVar, command=RightX)
        ShowRight.pack(side=LEFT)
        ToolTip(ShowRight,'Show items that exist in the right directory only')
        Vars.ShowRightCheckVar.set(FALSE)

    ProjectFrame = Frame(ControlFrame1, relief=SUNKEN, bd=2)
    ProjectFrame.pack(side=TOP, expand=FALSE, fill=X)
    ProjectLabel = Label(ProjectFrame, text='Project', width=8)
    ProjectLabel.pack(side=LEFT)
    ToolTip(ProjectLabel,'Enter or show the current project file name')
    ProjectEntry = Entry(ProjectFrame)
    ProjectEntry.pack(side=LEFT, expand=TRUE, fill=X)
    ToolTip(ProjectEntry,'Enter or show the current project file name')
    ProjectEntry.delete(0,END)
    ProjectEntry.insert(0,'****************')

#---------
    FilterFrame = Frame(ControlFrame1, relief=SUNKEN, bd=2)
    FilterFrame.pack(side=LEFT, fill=X)
    FetchDataButton = Button(FilterFrame, text='Fetch data', width=12, command=FetchData)
    FetchDataButton.pack(side=LEFT)
    ToolTip(FetchDataButton,'Fetch data')
    Vars.FilterEntry = Entry(FilterFrame)
    Vars.FilterEntry.pack(side=LEFT)
    ToolTip(Vars.FilterEntry,'Enter a filter string to display only certain entries')
    Vars.FilterEntry.delete(0,END)

    Checkbutton(FilterFrame, text='Both', variable=Vars.ShowBothCheckVar).pack(side=LEFT)
    Checkbutton(FilterFrame, text='Diff', variable=Vars.ShowDiffCheckVar).pack(side=LEFT)
    Checkbutton(FilterFrame, text='Left', variable=Vars.ShowLeftCheckVar).pack(side=LEFT)
    Checkbutton(FilterFrame, text='Right', variable=Vars.ShowRightCheckVar).pack(side=LEFT)
    Checkbutton(FilterFrame, text='Dir', variable=Vars.ShowDirectoriesCheckVar).pack(side=LEFT)
#---------
    SearchFrame = Frame(ControlFrame1, relief=SUNKEN, bd=2)
    SearchFrame.pack(side=LEFT, fill=X)
    SearchButtonMain = Button(SearchFrame, text='Search', width=8, command=lambda:SearchData('main'))
    SearchButtonMain.pack(side=LEFT)
    ToolTip(SearchButtonMain,'Enter a Search string to find certain entries')
    Vars.SearchEntryMain = Entry(SearchFrame)
    Vars.SearchEntryMain.pack(side=LEFT)
    Vars.SearchEntryMain.bind('<Return>', lambda x: SearchData('main'))
    ToolTip(Vars.SearchEntryMain,'Enter a Search string to find certain entries')
    Vars.SearchEntryMain.delete(0,END)

    Checkbutton(SearchFrame, text='Left', variable=Vars.LeftSearchVar ).pack(side=LEFT)
    Checkbutton(SearchFrame, text='Right', variable=Vars.RightSearchVar).pack(side=LEFT)
    Checkbutton(SearchFrame, text='Status', variable=Vars.StatusSearchVar).pack(side=LEFT)
    Checkbutton(SearchFrame, text='More', variable=Vars.MoreSearchVar).pack(side=LEFT)
    Checkbutton(SearchFrame, text='Case', variable=Vars.CaseSearchVar).pack(side=LEFT)
#---------

    Leftdirectorybutton = Button(ControlFrame3, width=20, text='Left directory path',command=lambda: FetchDirectories('Left'))
    Leftdirectorybutton.pack(side=LEFT)
    ToolTip(Leftdirectorybutton, 'Enter or display left directory path')
    Vars.LeftPathEntry = Entry(ControlFrame3)
    Vars.LeftPathEntry.pack(side=LEFT, expand=TRUE, fill=X)
    ToolTip(Vars.LeftPathEntry, 'Enter or display left directory path')
    Vars.LeftPathEntry.delete(0,END)

    Rightdirectorybutton = Button(ControlFrame4, width=20, text='Right directory path',command=lambda: FetchDirectories('Right'))
    Rightdirectorybutton.pack(side=LEFT)
    Vars.RightPathEntry = Entry(ControlFrame4)
    Vars.RightPathEntry.pack(side=LEFT, expand=TRUE, fill=X)
    ToolTip(Vars.RightPathEntry, 'Enter or display the right directory path')
    Vars.RightPathEntry.delete(0,END)
    ToolTip(Rightdirectorybutton, 'Enter or display the right directory path')

    Main.title('PyDiffTk')
    Main.minsize(920,300)
    Main.wm_iconname('PyDiffTk')

    Vars.AutoRefreshCheckVar.set(1)
    Vars.CheckSumTypeVar.set(1)

    Vars.RecycleCheckVar.set(1)
    Vars.ConfirmCopyCheckVar.set(1)
    Vars.ConfirmDeleteCheckVar.set(1)
    Vars.ConfirmRenameCheckVar.set(1)

    OptionsInstance.BuildOptionsForm()
    BatchInstance.BuildBatchForm()
    FileInfoInstance.BuildFileInfoForm()

    Vars.LeftPathEntry.delete(0,END)
    Vars.RightPathEntry.delete(0,END)

    ParseCommandLine()
    SetDefaults() #Initialize the variables
    StartUpStuff()

    Logger('System editor: ' + Vars.SystemEditorVar.get(), getframeinfo(currentframe()))
    Logger('System differ: ' + Vars.SystemDifferVar.get(), getframeinfo(currentframe()))
    Logger('System renamer: ' + Vars.SystemRenamerVar.get(), getframeinfo(currentframe()))

    Main.bind('<F1>', lambda e:Help())
    Main.bind('<F2>', lambda e: About())
    Main.bind('<F3>', lambda e: ClearAll())
    Main.bind('<F4>', lambda e: ShowRow())
    Main.bind('<F5>', lambda e: FetchData())
    Main.bind('<F7>', ShowSelectedList)
    Main.bind('<F8>', AddSelectedToList)
    Main.bind('<F9>', ClearSelectedList)
    Main.bind('<F12>', lambda e: FileInfoInstance.ShowFileInfo())
    Main.bind('<Control-q>', lambda e: Quit())
    Main.bind('<Control-Q>', lambda e: Quit())
    Main.bind('<ButtonRelease-1>', lambda e: Update())
    Main.bind('<ButtonRelease-2>', lambda e: BatchInstance.ShowBatchForm()) #Middle button
    Main.bind('<ButtonRelease-3>', lambda e: FileInfoInstance.ShowFileInfo()) #Right button

    Main.mainloop()
