#!/usr/bin/env python3

import argparse
import filecmp
import logging
import os
import subprocess
import sys
from shutil import copy2, move

import coloredlogs
import verboselogs

import exiftool


class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass

parser = argparse.ArgumentParser(
        description='''Copy the source directory to destination directory, maintaining the directory structure of another directory. 
More precisely, match the files with only file names and try to copy. The source directory should only have unique file names.
Author: Kiyoon Kim (yoonkr33@gmail.com)''',
        formatter_class=Formatter)
parser.add_argument('source_dir', type=str, 
        help='Directory to copy')
parser.add_argument('destination_dir', type=str,
        help='Destination directory')
parser.add_argument('dir_like', type=str,
        help='Organised directory.')
parser.add_argument('--copy_json', action='store_true',
        help='Copy the json files together with the images.')
parser.add_argument('--copy_cr3', action='store_true',
        help='Copy the CR3 files together with the images.')
parser.add_argument('--copy_arw', action='store_true',
        help='Copy the ARW files together with the images.')
parser.add_argument('--delete_originals', action='store_true',
        help='Move files instead of copying.')

args = parser.parse_args()


if __name__ == '__main__':

    logger = verboselogs.VerboseLogger(__name__)
    coloredlogs.install(fmt='%(asctime)s - %(levelname)s - %(message)s', level='INFO', logger=logger)

    nb_error = 0
    nb_warning = 0

    args.source_dir = args.source_dir.rstrip('\\')
    args.source_dir = args.source_dir.rstrip('/')
    args.destination_dir = args.destination_dir.rstrip('\\')
    args.destination_dir = args.destination_dir.rstrip('/')
    args.dir_like = args.dir_like.rstrip('\\')
    args.dir_like = args.dir_like.rstrip('/')

    logger.info("Analysing source directory..")
    filename_to_source_path = {}
    for root, dirs, files in os.walk(args.source_dir):
        for name in files:
            ext = os.path.splitext(name)[1][1:].lower()
            if ext == 'jpg':
                sourcepath = os.path.join(root, name)
                if name in filename_to_source_path.keys():
                    logger.error("Multiple files with the same name in the source folder detected:")
                    logger.error(f"{filename_to_source_path[name]} and {sourcepath}")
                    logger.error(f"This script detects the folder structure of `args.dir_like`, and organises the source directory just like that.")
                    logger.error(f"So the file names in the source directory should be unique, and the folder structure is completely ignored in that directory.")
                    logger.error(f"Otherwise it cannot match the file.")
                    sys.exit(1)
                filename_to_source_path[name] = sourcepath

    
    logger.info("Creating directory: %s", args.destination_dir)
    os.makedirs(args.destination_dir, exist_ok=True)

    
    if args.delete_originals:
        copy_func = move
        copy_msg = "Moving"
    else:
        copy_func = copy2
        copy_msg = "Copying"
    
    for root, dirs, files in os.walk(args.dir_like):
        dest_root = root.replace(args.dir_like, args.destination_dir, 1)

        for name in dirs:
            dest_dir = os.path.join(dest_root, name)
            logger.info("Creating directory: %s", dest_dir)
            os.makedirs(dest_dir, exist_ok=True)

        for name in files:
            ext = os.path.splitext(name)[1][1:].lower()
            if ext == 'jpg':
                source_file = filename_to_source_path[name]
                dest_file = os.path.join(dest_root, name)
                logger.info("%s file to: %s", copy_msg, dest_file)
                if os.path.isfile(source_file):
                    copy_func(source_file, dest_file)
                else:
                    logger.error("File doesn't exist: %s", source_file)
                    nb_error += 1

                if args.copy_json:
                    json_name = name + '.json'
                    source_file = filename_to_source_path[name] + '.json'
                    dest_file = os.path.join(dest_root, json_name)
                    logger.info("%s file to: %s", copy_msg, dest_file)

                    if os.path.isfile(source_file):
                        copy_func(source_file, dest_file)
                    else:
                        logger.warning("File doesn't exist: %s", source_file)
                        nb_warning += 1

                if args.copy_cr3:
                    source_file = os.path.splitext(filename_to_source_path[name])[0] + '.CR3'
                    cr3_name = os.path.splitext(name)[0] + '.CR3'
                    dest_file = os.path.join(dest_root, cr3_name)
                    logger.info("%s file to: %s", copy_msg, dest_file)
                    if os.path.isfile(source_file):
                        copy_func(source_file, dest_file)
                    else:
                        logger.warning("File doesn't exist: %s", source_file)
                        nb_warning += 1

                if args.copy_arw:
                    source_file = os.path.splitext(filename_to_source_path[name])[0] + '.ARW'
                    arw_name = os.path.splitext(name)[0] + '.ARW'
                    dest_file = os.path.join(dest_root, arw_name)
                    logger.info("%s file to: %s", copy_msg, dest_file)
                    if os.path.isfile(source_file):
                        copy_func(source_file, dest_file)
                    else:
                        logger.warning("File doesn't exist: %s", source_file)
                        nb_warning += 1


    if nb_warning > 0:
        logger.warning("%d warning(s) found.", nb_warning)

    if nb_error > 0:
        logger.error("%d error(s) found.", nb_error)
    else:
        logger.success("Copy file successful!")
