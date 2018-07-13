#!python3
import os, sys
import platform
import getopt
import glob
from datetime import datetime

def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            print("Warning: creation date is not supported in Linux. Using modified date")
            return stat.st_mtime

def modified_date(path_to_file):
    if platform.system() == 'Windows':
        return os.path.getmtime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        return stat.st_mtime

def help():
    print("Usage: %s [options..] [files..]" % sys.argv[0])
    print("Author: Kiyoon Kim (yoonkr33@gmail.com)")
    print("Description: Change file names based on their creation/modified date")
    print()
    print("Options:")
    print(" -h, --help\t\tprint this help list")
    print(" -m, --modified\t\tuse modified date instead of birth date")
    print(" -p, --prefix SOMETEXT\tset prefix to SOMETEXT")
    print()
    print("if you want to undo it, execute .datename_undo.sh or .datename_undo.bat")

if __name__ == "__main__":
    try:
        opts,args = getopt.getopt(sys.argv[1:], "hmp:", ["help", "modified=", "prefix="])
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)

    num_options = 0
    time_func = creation_date
    prefix = ""
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            num_options += 1
            help()
            sys.exit()
        elif opt in ('-m', '--modified'):
            num_options += 1
            time_func = modified_date
        elif opt in ('-p', '--prefix'):
            if opt == '-p':
                num_options += 2
            else:
                num_options += 1
            prefix = arg
    
    files = sys.argv[1+num_options:]
    if not files:
        help()
        print("aa")
        sys.exit(2)

    if platform.system() == 'Windows':
        undo_filename = '.datename_undo.bat'
        undo_command = 'move'
    else:
        undo_filename = '.datename_undo.sh'
        undo_command = 'mv'
    with open(undo_filename, 'a') as undo:
        for origpath in files:
            for path in glob.glob(origpath):    # glob: Windows wildcard support
                root, fname_ext = os.path.split(path)
                fname, fext = os.path.splitext(fname_ext)

                new_fname = datetime.fromtimestamp(time_func(path)).strftime('%Y%m%d_%H%M%S')
                new_path_wo_ext = os.path.join(root, prefix + new_fname)
                new_path = new_path_wo_ext + fext
                if os.path.isfile(new_path):
                    counter = 2
                    new_path = new_path_wo_ext + "_" + str(counter) + fext
                    while os.path.isfile(new_path):
                        counter += 1
                        new_path = new_path_wo_ext + "_" + str(counter) + fext

                print(path + " -> " + new_path)
                os.rename(path, new_path)
                undo.write('%s "%s" "%s"\n' % (undo_command, new_path, path))

