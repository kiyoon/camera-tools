import os
from pathlib import Path
from typing import Annotated

import piexif
import verboselogs
from cyclopts import Parameter
from PIL import Image

from camera_tools.utils.burn_signature import watermark_signature
from camera_tools.utils.log import setup_logging
from camera_tools.utils.pil import resample_str_to_pil_code
from camera_tools.utils.pil_transpose import exif_transpose_delete_exif


def bulk_image_resize(
    source_dir: str,
    destination_dir: str,
    *,
    divide: Annotated[int, Parameter(name=["--divide", "-d"])] = 2,
    minimum_height: Annotated[int, Parameter(name=["--minimum-height", "-mh"])] = 2272,
    quality: Annotated[int, Parameter(name=["--quality", "-q"])] = 95,
    resample: Annotated[str, Parameter(name=["--resample", "-r"])] = "bicubic",
    watermark: Annotated[bool, Parameter(name=["--watermark", "-w"])] = False,
    exts_to_find: list[str] = ["JPG", "PNG"],  # noqa: B006
):
    """
    Resize all of the images and output to another directory.

    Author: Kiyoon Kim

    Args:
        divide: Output image resolution (width, height) is divided by this factor.
        minimum_height: Output image resolution (height) do not go below this.
            If the original is smaller, stick to the original resolution.
            Default value is the resolution with Canon R6 when crop mode is enabled.
        quality: Output image jpeg quality.
        resample: Resampling algorithm.
        watermark: Watermark Instagram and YouTube channel on the image.
        exts_to_find: Image file extensions to find.
    """
    logger = verboselogs.VerboseLogger(__name__)
    setup_logging()

    nb_error = 0
    nb_warning = 0

    source_dir = source_dir.rstrip("\\")
    source_dir = source_dir.rstrip("/")
    destination_dir = destination_dir.rstrip("\\")
    destination_dir = destination_dir.rstrip("/")

    logger.info("Creating directory: %s", destination_dir)
    Path(destination_dir).mkdir(parents=True, exist_ok=True)

    for root, dirs, files in os.walk(source_dir):
        dest_root = root.replace(source_dir, destination_dir, 1)
        root = Path(root)
        dest_root = Path(dest_root)

        for name in dirs:
            dest_dir = dest_root / name
            logger.info("Creating directory: %s", dest_dir)
            dest_dir.mkdir(parents=True, exist_ok=True)

        for name in sorted(files):
            name = Path(name)
            ext = name.suffix.lower()[1:]
            source_file = root / name
            dest_file = dest_root / name

            if dest_file.is_file():
                logger.error("File already exists: %s", dest_file)
                nb_error += 1
            else:
                exts = [x.lower() for x in exts_to_find]

                if ext in exts:
                    logger.info("Resizing file to: %s", dest_file)
                    img = Image.open(source_file)
                    src_width, src_height = img.size
                    if src_height <= minimum_height:
                        logger.info(
                            "Keeping the resolution and re-encoding to: %s", dest_file
                        )
                        dest_width, dest_height = src_width, src_height
                    else:
                        dest_width, dest_height = (
                            src_width // divide,
                            src_height // divide,
                        )
                        if dest_height < minimum_height:
                            dest_height = minimum_height
                            dest_width = round((src_width / src_height) * dest_height)
                            logger.info(
                                "Setting the resolution to the minimum height %d and saving to: %s",
                                dest_height,
                                dest_file,
                            )
                        else:
                            logger.info("Resizing file to: %s", dest_file)

                    img = img.resize(
                        (dest_width, dest_height),
                        resample=resample_str_to_pil_code(resample),
                    )

                    if "exif" in img.info:
                        # Change EXIF resolution info.
                        exif_dict = piexif.load(img.info["exif"])
                        # exif_dict['0th'][piexif.ImageIFD.ImageWidth] = width
                        # exif_dict['0th'][piexif.ImageIFD.ImageLength] = height
                        exif_dict["Exif"][piexif.ExifIFD.PixelXDimension] = dest_width
                        exif_dict["Exif"][piexif.ExifIFD.PixelYDimension] = dest_height
                        exif_bytes = piexif.dump(exif_dict)

                        if watermark:
                            img, _, inverse_transpose = exif_transpose_delete_exif(img)
                            img = watermark_signature(img).convert("RGB")
                            if inverse_transpose is not None:
                                img = img.transpose(inverse_transpose)
                        img.save(dest_file, quality=quality, exif=exif_bytes)
                    else:
                        if watermark:
                            img = watermark_signature(img).convert("RGB")
                        img.save(dest_file, quality=quality)

    if nb_warning > 0:
        logger.warning("%d warning(s) found.", nb_warning)

    if nb_error > 0:
        logger.error("%d error(s) found.", nb_error)
    else:
        logger.success("Resizing successful!")
