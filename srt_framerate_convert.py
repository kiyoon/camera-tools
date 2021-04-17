#!/usr/bin/env python3


import argparse

class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass

parser = argparse.ArgumentParser(
        description='''Convert 24fps SRT files to 23.976 fps.
Davinci Resolve project exports in 24fps even when the project is in 23.976, so this conversion is needed to prevent the SRT files from drifting.

Author: Kiyoon Kim (yoonkr33@gmail.com)''',
        formatter_class=Formatter)
parser.add_argument('input_files', type=str, nargs='+',
        help='files you want to change names into dates')

args = parser.parse_args()

import coloredlogs, logging, verboselogs

import os, sys
import glob
import srt
import datetime

import srt_utils


if __name__ == "__main__":
    logger = verboselogs.VerboseLogger(__name__)
    coloredlogs.install(fmt='%(asctime)s - %(levelname)s - %(message)s', level='INFO', logger=logger)

    nb_error = 0
    nb_warning = 0

    num_input_files = 0
    for origpath in args.input_files:
        for path in glob.glob(origpath):    # glob: Windows wildcard support
            num_input_files += 1

    logger.info("%d files to convert", num_input_files)

    for origpath in args.input_files:
        for source_file in glob.glob(origpath):    # glob: Windows wildcard support
            root, fname_ext = os.path.split(source_file)
            fname, fext = os.path.splitext(fname_ext)

            dest_file = source_file

            logger.info("Converting SRT to %s", dest_file)

            with open(source_file, 'r', encoding="utf8") as f:
                srt_lines = list(srt.parse(f))

            srt_utils.srt_drift_fix_NTSC(srt_lines)

            with open(dest_file, 'w', encoding="utf8") as f:
                f.write(srt.compose(srt_lines))

    if nb_warning > 0:
        logger.warning("%d warning(s) found.", nb_warning)

    if nb_error > 0:
        logger.error("%d error(s) found.", nb_error)
    else:
        logger.success("Conversion successful!")
