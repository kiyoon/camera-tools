#!/usr/bin/env python3

import argparse
import os
from os import PathLike
from shutil import copy2, move

import coloredlogs
import verboselogs


class Formatter(
    argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter
):
    pass


parser = argparse.ArgumentParser(
    description="""Copy the images specified in the list (text file separated by return) to another directory.
Author: Kiyoon Kim (yoonkr33@gmail.com)""",
    formatter_class=Formatter,
)
parser.add_argument("source_dir", type=str, help="Directory to copy")
parser.add_argument("destination_dir", type=str, help="Destination directory")
parser.add_argument("image_list", type=str, help="Path to an image list file.")
parser.add_argument(
    "--encoding",
    type=str,
    default="utf-16",
    help="Set file encoding for the image list.",
)
parser.add_argument(
    "--copy_json",
    action="store_true",
    help="Copy the json files together with the images.",
)
parser.add_argument(
    "--copy_cr3",
    action="store_true",
    help="Copy the CR3 files together with the images.",
)
parser.add_argument(
    "--copy_arw",
    action="store_true",
    help="Copy the ARW files together with the images.",
)
parser.add_argument(
    "--delete_originals", action="store_true", help="Move files instead of copying."
)


args = parser.parse_args()


def copy_file(
    source_dir: str | PathLike,
    destination_dir: str | PathLike,
    name,
    copy_func=copy2,
    copy_msg="Copying",
):
    source_file = os.path.join(source_dir, name)
    dest_file = os.path.join(destination_dir, name)

    if not os.path.isfile(source_file):
        logger.error("File doesn't exist: %s", source_file)
        return False

    if os.path.isfile(dest_file):
        logger.error("File already exists: %s", dest_file)
        return False

    else:
        logger.info("%s file to: %s", copy_msg, dest_file)
        copy_func(source_file, dest_file)
        return True


if __name__ == "__main__":
    logger = verboselogs.VerboseLogger(__name__)
    coloredlogs.install(
        fmt="%(asctime)s - %(levelname)s - %(message)s", level="INFO", logger=logger
    )

    nb_error = 0
    nb_warning = 0

    args.source_dir = args.source_dir.rstrip("\\")
    args.source_dir = args.source_dir.rstrip("/")
    args.destination_dir = args.destination_dir.rstrip("\\")
    args.destination_dir = args.destination_dir.rstrip("/")

    logger.info("Creating directory: %s", args.destination_dir)
    os.makedirs(args.destination_dir, exist_ok=True)

    logger.info("Loading file list: %s", args.image_list)
    with open(args.image_list, "r", encoding=args.encoding) as f:
        image_name_list = f.read().splitlines()

    if args.delete_originals:
        copy_func = move
        copy_msg = "Moving"
    else:
        copy_func = copy2
        copy_msg = "Copying"

    for image_name in image_name_list:
        nb_error += not copy_file(
            args.source_dir, args.destination_dir, image_name, copy_func, copy_msg
        )

        if args.copy_json:
            # JSON
            json_name = image_name + ".json"
            nb_error += not copy_file(
                args.source_dir, args.destination_dir, json_name, copy_func, copy_msg
            )

        if args.copy_cr3:
            # CR3
            cr3_name = os.path.splitext(image_name)[0] + ".CR3"
            nb_error += not copy_file(
                args.source_dir, args.destination_dir, cr3_name, copy_func, copy_msg
            )

        if args.copy_arw:
            # ARW
            arw_name = os.path.splitext(image_name)[0] + ".ARW"
            nb_error += not copy_file(
                args.source_dir, args.destination_dir, arw_name, copy_func, copy_msg
            )

    if nb_warning > 0:
        logger.warning("%d warning(s) found.", nb_warning)

    if nb_error > 0:
        logger.error("%d error(s) found.", nb_error)
    else:
        logger.success("Copy file successful!")
