#!/usr/bin/env python3

FFPROBE = ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-print_format", "json"]


import argparse

class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass

parser = argparse.ArgumentParser(
        description='''Read ffprobe data

Author: Kiyoon Kim (yoonkr33@gmail.com)''',
        formatter_class=Formatter)
parser.add_argument('input_files', type=str, nargs='+',
        help='files to read metadata')

args = parser.parse_args()


import glob

import os
import exiftool
import pprint

import json
import subprocess
def ffprobe(source_file):
    proc = subprocess.Popen(FFPROBE + [source_file], stdout=subprocess.PIPE, shell=False)
    (ffprobe_out, ffprobe_err) = proc.communicate()
    ffprobe_out = ffprobe_out.decode('utf-8')
    return json.loads(ffprobe_out)

if __name__ == "__main__":
    for origpath in args.input_files:
        for path in glob.glob(origpath):    # glob: Windows wildcard support
            root, fname_ext = os.path.split(path)
            fname, fext = os.path.splitext(fname_ext)

            metadata = ffprobe(path)

            print(path)
            pprint.pprint(metadata)
