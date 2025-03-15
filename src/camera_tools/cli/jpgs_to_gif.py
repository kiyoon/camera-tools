import os
from enum import Enum
from pathlib import Path
from typing import Annotated

import coloredlogs
import verboselogs
from cyclopts import Parameter
from PIL import Image

from camera_tools.utils.pil import resample_str_to_pil_code
from camera_tools.utils.pil_transpose import exif_transpose_delete_exif


class ResampleOptions(str, Enum):
    nearest = "nearest"
    bilinear = "bilinear"
    bicubic = "bicubic"
    lanczos = "lanczos"


def jpgs_to_gif(
    source_dir: str,
    *,
    divide: Annotated[int, Parameter(name=["--divide", "-d"])] = 5,
    resample: Annotated[
        ResampleOptions, Parameter(name=["--resample", "-r"])
    ] = ResampleOptions.bicubic,
    num_loops: Annotated[int, Parameter(name=["--num-loops", "-l"])] = 0,
    duration: int = 200,
    optimise: bool = True,
    exts_to_find: list[str] = ["JPG", "PNG"],
):
    """
    Find directories that contain images and make them into GIFs.

    Output filename will be the same as the dir name.

    Author: Kiyoon Kim

    Args:
        source_dir: Directory of images to make a GIF.
        divide: Output image resolution is divided by this factor.
        resample: Resampling algorithm.
        num_loops: Number of loops. 0 means infinite.
        duration: Duration for each frame in milliseconds.
        optimise: Optimise the output GIFs.
        exts_to_find: Image file extensions to find.
    """
    logger = verboselogs.VerboseLogger(__name__)
    coloredlogs.install(
        fmt="%(asctime)s - %(levelname)s - %(message)s", level="INFO", logger=logger
    )

    nb_error = 0
    nb_warning = 0

    source_dir = source_dir.rstrip("\\")
    source_dir = source_dir.rstrip("/")

    exts = [x.lower() for x in exts_to_find]

    for root, _dirs, files in os.walk(source_dir):
        root = Path(root)
        gif_frames = []
        for name in sorted(files):
            name = Path(name)
            ext = name.suffix[1:].lower()
            source_file = root / name

            if ext in exts:
                img = Image.open(source_file)
                img, _, _ = exif_transpose_delete_exif(img)
                src_width, src_height = img.size
                dest_width, dest_height = (
                    src_width // divide,
                    src_height // divide,
                )
                img = img.resize(
                    (dest_width, dest_height),
                    resample=resample_str_to_pil_code(resample),
                )
                gif_frames.append(img)

        if len(gif_frames) >= 2:  # requires at least 2 images
            output_gif_name = Path(f"{root}.gif")
            if output_gif_name.is_file():
                logger.error("File already exists: %s", output_gif_name)
                nb_error += 1
            else:
                logger.info("Saving to %s", output_gif_name)
                gif_frames[0].save(
                    output_gif_name,
                    save_all=True,
                    append_images=gif_frames[1:],
                    optimize=optimise,
                    duration=duration,
                    loop=num_loops,
                )

    if nb_warning > 0:
        logger.warning("%d warning(s) found.", nb_warning)

    if nb_error > 0:
        logger.error("%d error(s) found.", nb_error)
    else:
        logger.success("Converting GIF successful!")
