#Parse the command line
def ParseCommandLine():
    Logger('ParseCommandLine', getframeinfo(currentframe()))
    #Test that the file exists on the path
    def is_valid_file(parser, arg):
        if len(arg) == 0: arg = FileSourceEntry.get()
        if arg == '.': arg = ''
        if not os.path.isfile(arg) and arg != '':
            tkinter.messagebox.showerror('Source file error' , \
                'The source file does not exist or is not a file\n' + arg)
            Logger('The source file does not exist or is not a file ' + arg,
            getframeinfo(currentframe()))
        else:
            FileSourceEntry.delete(0, END)
            FileSourceEntry.insert(0, arg)
            Vars.SourceInfoVar.set(FileStat(FileSourceEntry.get()))
            Logger('Source from command line: >>' + arg + '<<',
            getframeinfo(currentframe()))

    def is_valid_project(parser, arg):
        if not os.path.isfile(arg):
            tkinter.messagebox.showerror('Project file error' , \
                'The project file does not exist or is not a file\n' + arg)
            Logger('The project file does not exist or is not a file ' + arg,
            getframeinfo(currentframe()))
            return
        else:
            Vars. ProjectFileNameVar.set(arg)
            Logger('Project file from command line: >>' + arg, getframeinfo(currentframe()))

    parser = argparse.ArgumentParser(description='A tool to help copy or move files.')

    #parser.add_argument('-s', '--source', dest='filename', required=False,
    #   help='Source file to use', metavar='FILE', type=lambda x: is_valid_file(parser,x))
    parser.add_argument('source', nargs='?', default='', type=lambda x: is_valid_file(parser,x))
    parser.add_argument('-d', '--debug', help='Enable debugging', action='store_true', required=False)
    parser.add_argument('-p', '--project', dest='filename', required=False,
        help='Specify a project file to use', metavar='FILE',
        type=lambda x: is_valid_project(parser,x))

    args = parser.parse_args()

    if args.debug:
        import pdb
        pdb.set_trace()
        Logger('debug is on', getframeinfo(currentframe()))
    else:
        Logger('debug is off', getframeinfo(currentframe()))
