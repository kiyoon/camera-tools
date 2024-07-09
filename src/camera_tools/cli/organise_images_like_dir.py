import os
import sys
from os import PathLike
from pathlib import Path
from shutil import copy2, move
from typing import Annotated

import coloredlogs
import typer
import verboselogs


def organise_images_like_dir(
    source_dir: Annotated[str | PathLike, typer.Argument(help="Directory to copy")],
    destination_dir: Annotated[
        str | PathLike, typer.Argument(help="Destination directory")
    ],
    dir_like: Annotated[str | PathLike, typer.Argument(help="Organised directory.")],
    copy_json: Annotated[
        bool, typer.Option(help="Copy the json files along with the images.")
    ] = True,
    copy_cr3: Annotated[
        bool, typer.Option(help="Copy the CR3 files along with the images.")
    ] = True,
    copy_arw: Annotated[
        bool, typer.Option(help="Copy the ARW files along with the images.")
    ] = False,
    delete_originals: Annotated[
        bool, typer.Option(help="Move files instead of copying.")
    ] = False,
):
    """
    Copy the source directory to destination directory, maintaining the directory structure of another directory.

    More precisely, match the files with only file names and try to copy.
    The source directory should only have unique file names.
    Author: Kiyoon Kim
    """
    logger = verboselogs.VerboseLogger(__name__)
    coloredlogs.install(
        fmt="%(asctime)s - %(levelname)s - %(message)s", level="INFO", logger=logger
    )

    nb_error = 0
    nb_warning = 0

    source_dir = str(source_dir).rstrip("\\")
    source_dir = str(source_dir).rstrip("/")
    destination_dir = str(destination_dir).rstrip("\\")
    destination_dir = str(destination_dir).rstrip("/")
    dir_like = str(dir_like).rstrip("\\")
    dir_like = str(dir_like).rstrip("/")

    logger.info("Analysing source directory..")
    filename_to_source_path: dict[str, Path] = {}
    for root, _dirs, files in os.walk(source_dir):
        root = Path(root)
        for name in files:
            ext = Path(name).suffix.lower()
            if ext == ".jpg":
                sourcepath = root / name
                if name in filename_to_source_path:
                    logger.error(
                        "Multiple files with the same name in the source folder detected:\n"
                        f"{filename_to_source_path[name]} and {sourcepath}\n"
                        f"This script detects the folder structure of `dir_like`, "
                        "and organises the source directory just like that.\n"
                        "So the file names in the source directory should be unique, "
                        "and the folder structure is completely ignored in that directory.\n"
                        "Otherwise it cannot match the file."
                    )
                    sys.exit(1)
                filename_to_source_path[name] = sourcepath

    logger.info("Creating directory: %s", destination_dir)
    Path(destination_dir).mkdir(parents=True, exist_ok=True)

    if delete_originals:
        copy_func = move
        copy_msg = "Moving"
    else:
        # in Windows, copy
        # in Linux and macOS, hard link

        if os.name == "nt":
            copy_func = copy2
            copy_msg = "Copying"
        else:
            copy_func = os.link
            copy_msg = "Hard linking"

    for root, dirs, files in os.walk(dir_like):
        dest_root = root.replace(dir_like, destination_dir, 1)
        dest_root = Path(dest_root)

        for name in dirs:
            dest_dir = dest_root / name
            logger.info("Creating directory: %s", dest_dir)
            dest_dir.mkdir(parents=True, exist_ok=True)

        for name in files:
            ext = Path(name).suffix.lower()
            if ext == ".jpg":
                try:
                    source_file = filename_to_source_path[name]
                except KeyError:
                    logger.error("File doesn't exist in source directory: %s", name)
                    nb_error += 1
                    continue

                dest_file = dest_root / name
                logger.info("%s file to: %s", copy_msg, dest_file)
                if source_file.is_file():
                    copy_func(source_file, dest_file)
                else:
                    logger.error("File doesn't exist: %s", source_file)
                    nb_error += 1

                if copy_json:
                    source_file = Path(f"{filename_to_source_path[name]}.json")
                    dest_file = dest_root / f"{name}.json"
                    logger.info("%s file to: %s", copy_msg, dest_file)

                    if source_file.is_file():
                        copy_func(source_file, dest_file)
                    else:
                        logger.warning("File doesn't exist: %s", source_file)
                        nb_warning += 1

                if copy_cr3:
                    source_file = filename_to_source_path[name].with_suffix(".CR3")
                    dest_file = dest_root / Path(name).with_suffix(".CR3")
                    logger.info("%s file to: %s", copy_msg, dest_file)
                    if source_file.is_file():
                        copy_func(source_file, dest_file)
                    else:
                        logger.warning("File doesn't exist: %s", source_file)
                        nb_warning += 1

                if copy_arw:
                    source_file = filename_to_source_path[name].with_suffix(".ARW")
                    dest_file = dest_root / Path(name).with_suffix(".ARW")
                    logger.info("%s file to: %s", copy_msg, dest_file)
                    if source_file.is_file():
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
