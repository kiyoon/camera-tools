#!/usr/bin/env python3

import argparse


class Formatter(
    argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter
):
    pass


parser = argparse.ArgumentParser(
    description="""Read EXIF data

Author: Kiyoon Kim (yoonkr33@gmail.com)""",
    formatter_class=Formatter,
)
parser.add_argument("input_files", type=str, nargs="+", help="files to read metadata")

args = parser.parse_args()


import glob
import os
import pprint

from camera_tools import exiftool

if __name__ == "__main__":
    for origpath in args.input_files:
        for path in glob.glob(origpath):  # glob: Windows wildcard support
            root, fname_ext = os.path.split(path)
            fname, fext = os.path.splitext(fname_ext)

            with exiftool.ExifTool() as et:
                metadata = et.get_metadata(path)

            print(path)
            pprint.pprint(metadata)
