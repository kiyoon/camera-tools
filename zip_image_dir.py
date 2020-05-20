#!/usr/bin/env python3

import zipfile
import tqdm

import os
import sys
import argparse
import coloredlogs, logging, verboselogs


class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass

parser = argparse.ArgumentParser(
        description='''Archive all of the images to a zip file, but skip the rest of the files.
Author: Kiyoon Kim (yoonkr33@gmail.com)''',
        formatter_class=Formatter)
parser.add_argument('source_dir', type=str, 
        help='Directory to archive')
parser.add_argument('destination_file', type=str,
        help='Destination zip file path')
parser.add_argument('--ext', type=str, nargs='*', default=['JPG', 'PNG'],
        help='Image file extensions to find.')
parser.add_argument('--subdirs', type=str, nargs='*',
        help="Name of the subdirectories to zip. If not specified, archive all files regardless of the directory they're put in.")

args = parser.parse_args()



if __name__ == '__main__':

    logger = verboselogs.VerboseLogger(__name__)
    coloredlogs.install(fmt='%(asctime)s - %(levelname)s - %(message)s', level='INFO', logger=logger)

    nb_error = 0
    nb_warning = 0

    args.source_dir = args.source_dir.rstrip('\\')
    args.source_dir = args.source_dir.rstrip('/')

    destination_dir = os.path.dirname(os.path.realpath(args.destination_file))
    logger.info("Creating directory: %s", destination_dir)
    os.makedirs(destination_dir, exist_ok=True)

    exts = [x.lower() for x in args.ext]

    logger.info("Creating zip file: %s", args.destination_file)
    if os.path.isfile(args.destination_file):
        overwrite = input("File already exists. Overwrite? (y/n) ").lower() == 'y'
        if not overwrite:
            sys.exit(1)
            

    zip_io = zipfile.ZipFile(args.destination_file, 'w', zipfile.ZIP_STORED)

    if args.subdirs is not None and len(args.subdirs) > 0:
        source_dirs = [os.path.join(args.source_dir, subdir) for subdir in args.subdirs]
    else:
        source_dirs = [args.source_dir]

    num_files_to_zip = 0
    for source_dir in source_dirs:
        for root, dirs, files in os.walk(source_dir):
            for name in files:
                ext = os.path.splitext(name)[1][1:].lower()
                if ext in exts:
                    num_files_to_zip += 1


    progress = tqdm.tqdm(desc='Archiving', total=num_files_to_zip)

    for source_dir in source_dirs:
        for root, dirs, files in os.walk(source_dir):
            for name in files:
                ext = os.path.splitext(name)[1][1:].lower()
                source_file = os.path.join(root, name)

                if ext in exts:
                    progress.update(1)
                    tqdm.tqdm.write("Adding file to zip: %s" % (source_file))
                    zip_io.write(source_file)

    progress.close()
    zip_io.close()

    if nb_warning > 0:
        logger.warning("%d warning(s) found.", nb_warning)

    if nb_error > 0:
        logger.error("%d error(s) found.", nb_error)
    else:
        logger.success("Zip archiving successful!")
