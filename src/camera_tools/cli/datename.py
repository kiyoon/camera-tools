import glob
import os
import platform
import pprint
import re
from datetime import datetime
from enum import Enum
from os import PathLike
from pathlib import Path
from typing import Annotated, Any

import tqdm
from cyclopts import Parameter

from camera_tools import exiftool


def creation_date(file_path: str | PathLike):
    """
    Try to get the date that a file was created, falling back to when it was last modified if that isn't possible.

    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    file_path = Path(file_path)
    if platform.system() == "Windows":
        return file_path.stat().st_ctime
    else:
        stat = file_path.stat()
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux or Mac. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            print(
                "Warning: creation date is only supported on Windows. Using modified date"
            )
            return stat.st_mtime


def modified_date(file_path: str | PathLike):
    file_path = Path(file_path)

    if platform.system() == "Windows":
        return file_path.stat().st_mtime
    else:
        stat = file_path.stat()
        return stat.st_mtime


def path_no_overwrite_counter(path: str | PathLike, zfill=2):
    path = Path(path)
    path_wo_ext, fext = os.path.splitext(path)
    if path.is_file():
        counter = 2
        path = Path(path_wo_ext + "_" + str(counter).zfill(zfill) + fext)
        while path.is_file():
            counter += 1
            path = Path(path_wo_ext + "_" + str(counter).zfill(zfill) + fext)

    return path


def get_exif_batch(input_files: list[str]):
    glob_input_files = []
    for origpath in input_files:
        for path in glob.glob(origpath):  # glob: Windows wildcard support
            glob_input_files.append(path)

    # parallelly get exif data
    with exiftool.ExifTool() as et:
        metadata = et.get_metadata_batch(glob_input_files)

    result: dict[str, dict[str, Any]] = {}
    for glob_input_file, metadatum in zip(glob_input_files, metadata, strict=True):
        result[glob_input_file] = metadatum

    return result


class DateSourceOption(str, Enum):
    EXIF = "EXIF"
    file_created = "file_created"
    file_modified = "file_modified"


def datename(
    input_files: list[str],
    *,
    prefix: Annotated[str, Parameter(name=["--prefix", "-p"])] = "",
    date_source: DateSourceOption = DateSourceOption.EXIF,
    exif_date_key: str = "Composite:SubSecCreateDate",
    exif_date_format: str = "%Y:%m:%d %H:%M:%S.%f%z",
    undo: bool = True,
    save_exif: bool = True,
    rename_raw: bool = True,
    raw_ext: str = "CR3",
    timezone: Annotated[str | None, Parameter(name=["--timezone", "-tz"])] = None,
):
    """
    Change file names based on their file/EXIF creation/modified date.

    If you want to undo it, execute .datename_undo.sh or .datename_undo.bat

    Author: Kiyoon Kim

    Args:
        prefix: Prefix of the output names.
        date_source: Source of the date info.
        exif_date_key: Which EXIF data to use for the date.
            M50: Composite:SubSecCreateDate,
            Sony Cam: H264:DateTimeOriginal,
            Sony a6000: MakerNotes:SonyDateTime,
            Sony a6000 videos: XML:CreationDateValue
        exif_date_format: EXIF date format for reading the time.
            M50: %Y:%m:%d %H:%M:%S.%f%z,
            Sony a6000/Handycam: %Y:%m:%d %H:%M:%S%z
        undo: Generate an undo script (.datename_undo.sh or .datename_undo.bat)
        save_exif: Save exif info as json files. Useful backup in case some editing software messes up the exif info.
        rename_raw: Rename RAW files along with the JPG files.
        raw_ext: Extension of the RAW files.
        timezone: Change timezone (e.g. +0900 means Korea).
            Use when you forgot to reset the timezone when you were abroad.
            Leave it empty if you do not want to change the timezone.
    """
    if undo:
        if platform.system() == "Windows":
            undo_filename = ".datename_undo.bat"
            undo_command = "move"
        else:
            undo_filename = ".datename_undo.sh"
            undo_command = "mv"
    else:
        undo_filename = os.devnull
        undo_command = ""

    with open(undo_filename, "a") as undofile:
        num_jpg_files = 0
        for origpath in input_files:
            for _ in glob.glob(origpath):  # glob: Windows wildcard support
                num_jpg_files += 1

        progress = tqdm.tqdm(desc="Renaming", total=num_jpg_files)

        if date_source == DateSourceOption.EXIF:
            tqdm.tqdm.write("Getting all EXIF data...")
            input_file_to_exif = get_exif_batch(input_files)

        for origpath in input_files:
            for path in glob.glob(origpath):  # glob: Windows wildcard support
                path = Path(path)
                root = path.parent
                fname = path.stem
                fext = path.suffix

                metadata = None
                if date_source == DateSourceOption.EXIF:
                    # with exiftool.ExifTool() as et:
                    #     metadata = et.get_metadata(str(path))
                    metadata = input_file_to_exif[str(path)]

                    exif_date = metadata[exif_date_key]
                    # Python3.6 can't parse %z with colon (e.g. +09:00) so delete the colon (e.g. +0900)
                    exif_date = re.sub(
                        "([+-])([0-9]{2}):([0-9]{2})", r"\1\2\3", exif_date
                    )

                    photo_date = datetime.strptime(exif_date, exif_date_format)
                    # new_fname = metadata[args.exif_date]
                    # new_fname = new_fname.replace(':', '')
                    # new_fname = new_fname.replace(' ', '_')
                elif date_source == DateSourceOption.file_created:
                    photo_date = datetime.fromtimestamp(creation_date(path))
                else:  # date == 'file_modified':
                    photo_date = datetime.fromtimestamp(modified_date(path))

                # Change timezone
                if timezone:
                    new_timezone = datetime.strptime(timezone, "%z").tzinfo
                    photo_date = photo_date.astimezone(tz=new_timezone)

                new_fname = photo_date.strftime("%Y%m%d_%H%M%S.%f")[
                    :-4
                ] + photo_date.strftime("%z")

                new_path_wo_ext = root / (prefix + new_fname)

                # NOTE: filename contains dot, so we can't use with_suffix
                new_path = Path(str(new_path_wo_ext) + fext)

                new_path = path_no_overwrite_counter(new_path)

                tqdm.tqdm.write(f"{path} -> {new_path}")
                path.rename(new_path)

                raw_renamed = False
                if rename_raw and fext.lower() in ["jpg", ".jpg"]:
                    raw_path = Path(root) / (fname + "." + raw_ext)
                    if raw_path.exists():
                        # NOTE: filename contains dot, so we can't use with_suffix
                        raw_new_path = Path(str(new_path_wo_ext) + "." + raw_ext)
                        raw_new_path = path_no_overwrite_counter(raw_new_path)
                        tqdm.tqdm.write(f"{raw_path} -> {raw_new_path}")
                        raw_path.rename(raw_new_path)
                        raw_renamed = True

                undofile.write(f'{undo_command} "{new_path}" "{path}"\n')
                if raw_renamed:
                    undofile.write(f'{undo_command} "{raw_new_path}" "{raw_path}"\n')

                if save_exif and date_source != DateSourceOption.EXIF:
                    with exiftool.ExifTool() as et:
                        metadata = et.get_metadata(new_path)

                with open(str(new_path) + ".json", "w") as f:
                    f.write(pprint.pformat(metadata, indent=4))

                progress.update(1)
