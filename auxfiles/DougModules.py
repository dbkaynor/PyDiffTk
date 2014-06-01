import os
import sys
import time
import platform
import stat
import logging
import argparse
from inspect import currentframe, getframeinfo
import subprocess
from subprocess import Popen, PIPE

# TODO

#------------------------------
# Checks if file name exists
# File may be either on the system path
# or file may be a full path
def SearchPath(name):
  path = os.environ['PATH']
  for dir in path.split(os.pathsep):
    binpath = os.path.join(dir, name)
    if os.path.exists(binpath):
      return True
  return False
#------------------------------
#Parses the frame inspect information
def MyTrace(FrameInfoDict):
    filename = 0
    lineno = 1
    function = 2
    return FrameInfoDict[function], FrameInfoDict[lineno], FrameInfoDict[filename]
#------------------------------

def MyMessageBox(Title='MyMessageBox', XSize=250, YSize=120 ):
    MyMessageBoxToplevel = Toplevel()
    MyMessageBoxToplevel.title(Title)
    MyMessageBoxToplevel.wm_transient(Main)
    MyMessageBoxToplevelX = XSize
    MyMessageBoxToplevelY = YSize
    Mainsize = Main.geometry().split('+')
    x = int(Mainsize[1]) + (MyMessageBoxToplevelX / 2)
    y = int(Mainsize[2]) + (MyMessageBoxToplevelY / 2)
    MyMessageBoxToplevel.geometry("%dx%d+%d+%d" % (MyMessageBoxToplevelX, MyMessageBoxToplevelY, x, y))
    MyMessageBoxToplevel.resizable(1,0)

    Label(MyMessageBoxToplevel, text='Left:  ' + Vars.DataBox.get(Current)[0],
        relief=GROOVE).pack(expand=FALSE, fill=X)
    Label(MyMessageBoxToplevel, text='Right:  ' + Vars.DataBox.get(Current)[1],
        relief=GROOVE).pack(expand=FALSE, fill=X)
    Label(MyMessageBoxToplevel, text='Status:  ' + Vars.DataBox.get(Current)[2],
        relief=GROOVE).pack(expand=FALSE, fill=X)
    Label(MyMessageBoxToplevel, text='More:  ' + Vars.DataBox.get(Current)[3],
        relief=GROOVE).pack(expand=FALSE, fill=X)
    Button(MyMessageBoxToplevel, text='Close', command=lambda : MyMessageBoxToplevel.destroy()).pack()
#------------------------------

def Logger(LogMessage = '', FrameInfoDict=None, PrintToCommandLine=False):
    MyLogger = logging.getLogger()
    mystr = LogMessage + '  Trace: ' + str(MyTrace(FrameInfoDict))
    MyLogger.debug(mystr)
    if PrintToCommandLine: print(mystr)

#------------------------------

#Parse the command line
def ParseCommandLine():
    parser = argparse.ArgumentParser(description='A tool to compare to directories and move files')
    parser.add_argument('-debug',help='Enable debugging',action='store_true')
    args = parser.parse_args()

    if args.debug:
        import pdb
        pdb.set_trace()
        Logger('debug is on', getframeinfo(currentframe()))
    else:
        Logger('debug is off', getframeinfo(currentframe()))
#------------------------------

#This function starts a system file such as notepad.exe
def StartFile(filename, arg1='', arg2='', arg3=''):
    if arg1 == '':
        args = [filename]
    elif arg2 == '':
        args = [filename, arg1]
    elif arg3 == '':
        args = [filename, arg1, arg2]
    else:
        args = [filename, arg1, arg2, arg3]
    #args = filename

    Logger('StartFile arguments: ' + str(args), getframeinfo(currentframe()))
    ce = None
    try:
        ce = subprocess.call(args)
    except OSError:
        tkinter.messagebox.showerror('StartFile did a Badddddd thing ' , \
         'Arguments: ' + str(args) + '\nReturn code: ' + str(ce))
        return
#------------------------------
#returns string with status for a file
def FileStats(FilePath):
        FileStats = os.stat(FilePath)
        FileStatString = ''

        FileStatString += 'Full path: %s' % FilePath + '\n'
        FileStatString += 'Dir name: %s' % os.path.dirname(FilePath) + '\n'
        FileStatString += 'Base name: %s' % os.path.basename(FilePath) + '\n'
        FileStatString += 'File size: {:,}'.format(FileStats.st_size)+ '\n'
        FileStatString += 'Creation time: %s' % time.ctime(FileStats.st_ctime) + '\n'
        FileStatString += 'Modified time: %s' % time.ctime(FileStats.st_mtime) + '\n'
        FileStatString += 'Access time: %s' % time.ctime(FileStats.st_atime) + '\n'
        FileStatString += 'File mode bits: %o' % FileStats.st_mode + '\n'

        mode = FileStats[0]
        if mode & stat.S_ISLNK(FileStats[stat.ST_MODE]): FileStatString += 'File is a link\n'
        else:  FileStatString += 'File is not a link\n'
        if mode & stat.S_IREAD: FileStatString += 'File is readable\n'
        else: FileStatString += 'File is not readable\n'
        if mode & stat.S_IWRITE : FileStatString += 'File is writable\n'
        else: FileStatString += 'File is not writable\n'
        if mode & stat.S_IEXEC: FileStatString += 'File is executable\n'
        else: FileStatString += 'File is not executable\n'
        if stat.S_ISDIR(FileStats.st_mode): FileStatString += 'File is a directory\n'
        else: FileStatString += 'File is not a directory\n'
        if stat.S_ISREG(FileStats.st_mode): FileStatString += 'File is a regular file\n'
        else: FileStatString += 'File is a not regular file\n'

        return FileStatString
#------------------------------
if __name__ == '__main__':
    print(FileStats('DougModules.py'))
