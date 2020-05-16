#!/usr/bin/env python3

import argparse

class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass

parser = argparse.ArgumentParser(
        description='''Change file names based on their file/EXIF creation/modified date
If you want to undo it, execute .datename_undo.sh or .datename_undo.bat

Author: Kiyoon Kim (yoonkr33@gmail.com)''',
        formatter_class=Formatter)
parser.add_argument('input_files', type=str, nargs='+',
        help='files you want to change names into dates')
parser.add_argument('-p', '--prefix', type=str, default='',
        help='prefix of the names')
parser.add_argument('-d', '--date', type=str, default='EXIF', choices=["EXIF", "file_created", "file_modified"],
        help='source of the date info')
parser.add_argument('-e', '--exif-date', type=str, default='Composite:SubSecCreateDate',
        help='which EXIF data to use for the date. M50: Composite:SubSecCreateDate, Sony Cam: H264:DateTimeOriginal, Sony a6000: MakerNotes:SonyDateTime')
parser.add_argument('--undo', dest='undo', action='store_true',
        help='make undo file (.datename_undo.sh or .datename_undo.bat)')
parser.add_argument('--no-undo', dest='undo', action='store_false',
        help='do not make undo file (.datename_undo.sh or .datename_undo.bat)')
parser.set_defaults(undo=True)
parser.add_argument('--save-exif', dest='save_exif', action='store_true',
        help='save exif info in json files')
parser.add_argument('--no-save-exif', dest='save_exif', action='store_false',
        help='do not save exif info in json files')
parser.set_defaults(save_exif=True)
parser.add_argument('--rename-raw', dest='rename_raw', action='store_true',
        help='rename RAW files along with the JPG files.')
parser.add_argument('--no-rename-raw', dest='rename_raw', action='store_false',
        help='do not rename RAW files along with the JPG files.')
parser.add_argument('--raw-ext', type=str, default='CR3')
parser.add_argument('--timezone', type=str,
        help='change timezone (e.g. +0900 means Korea). Use when you forgot to reset the timezone when you were abroad. Leave it empty if you do not want to change the timezone.')
parser.set_defaults(rename_raw=True)

args = parser.parse_args()


import os, sys
import platform
import glob
from datetime import datetime

import exiftool
import pprint

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


def path_no_overwrite_counter(path, zfill=2):
    path_wo_ext, fext = os.path.splitext(path)
    if os.path.isfile(path):
        counter = 2
        path = path_wo_ext + "_" + str(counter).zfill(zfill) + fext
        while os.path.isfile(path):
            counter += 1
            path = path_wo_ext + "_" + str(counter).zfill(zfill) + fext

    return path


if __name__ == "__main__":
    if args.undo:
        if platform.system() == 'Windows':
            undo_filename = '.datename_undo.bat'
            undo_command = 'move'
        else:
            undo_filename = '.datename_undo.sh'
            undo_command = 'mv'
        undo = open(undo_filename, 'a')

    for origpath in args.input_files:
        for path in glob.glob(origpath):    # glob: Windows wildcard support
            root, fname_ext = os.path.split(path)
            fname, fext = os.path.splitext(fname_ext)

            if args.date == 'EXIF':
                with exiftool.ExifTool() as et:
                    metadata = et.get_metadata(path)
                photo_date = datetime.strptime(metadata[args.exif_date], '%Y:%m:%d %H:%M:%S.%f%z')
                #new_fname = metadata[args.exif_date]
                #new_fname = new_fname.replace(':', '')
                #new_fname = new_fname.replace(' ', '_')
            elif args.date == 'file_created':
                photo_date = datetime.fromtimestamp(creation_date(path))
            else:   # args.date == 'file_modified':
                photo_date = datetime.fromtimestamp(modified_date(path))

            # Change timezone
            if args.timezone:
                new_timezone = datetime.strptime(args.timezone, '%z').tzinfo
                photo_date = photo_date.astimezone(tz=new_timezone)

            new_fname = photo_date.strftime('%Y%m%d_%H%M%S.%f')[:-4] + photo_date.strftime('%z')

            new_path_wo_ext = os.path.join(root, args.prefix + new_fname)
            new_path = new_path_wo_ext + fext

            new_path = path_no_overwrite_counter(new_path)

            print(path + " -> " + new_path)
            os.rename(path, new_path)

            if args.rename_raw and fext.lower() in ["jpg", ".jpg"]:
                raw_path = os.path.join(root, fname + "." + args.raw_ext)
                raw_new_path = new_path_wo_ext + "." + args.raw_ext
                raw_new_path = path_no_overwrite_counter(raw_new_path)
                print(raw_path + " -> " + raw_new_path)
                os.rename(raw_path, raw_new_path)

            if args.undo:
                undo.write('%s "%s" "%s"\n' % (undo_command, new_path, path))
                if args.rename_raw and fext.lower() in ["jpg", ".jpg"]:
                    undo.write('%s "%s" "%s"\n' % (undo_command, raw_new_path, raw_path))
            
            if args.save_exif:
                if args.date != 'EXIF':
                    with exiftool.ExifTool() as et:
                        metadata = et.get_metadata(new_path)

                with open(new_path + '.json', 'w') as f:
                    f.write(pprint.pformat(metadata, indent=4))

    if args.undo:
        undo.close()

