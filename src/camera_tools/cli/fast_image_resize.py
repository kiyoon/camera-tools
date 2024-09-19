import os
from pathlib import Path
from typing import Annotated

import typer
import verboselogs

from camera_tools.utils.log import setup_logging


def fast_image_resize(
    source_dir: str,
    destination_dir: str,
    divide: Annotated[
        int,
        typer.Option(
            "--divide",
            "-d",
            help="Output image resolution (width, height) is divided by this factor.",
        ),
    ] = 2,
    minimum_height: Annotated[
        int,
        typer.Option(
            "--minimum-height",
            "-mh",
            help="Output image resolution (height) do not go below this. "
            "If the original is smaller, stick to the original resolution. "
            "Default value is the resolution with Canon R6 when crop mode is enabled.",
        ),
    ] = 2272,
    quality: Annotated[
        int, typer.Option("--quality", "-q", help="Output image jpeg quality.")
    ] = 95,
    resample: Annotated[
        str, typer.Option("--resample", "-r", help="Resampling algorithm.")
    ] = "bicubic",
    watermark: Annotated[
        bool,
        typer.Option(
            "--watermark",
            "-w",
            help="Watermark Instagram and YouTube channel on the image.",
        ),
    ] = False,
    exts_to_find: Annotated[
        list[str], typer.Option("--exts-to-find", help="Image file extensions to find.")
    ] = ["JPG", "PNG"],
):
    """
    Resize all of the images and output to another directory, faster using zune-image library.
    """
    import zil

    if resample == "bicubic":
        resample_method = zil.ResizeMethod.Bicubic
    elif resample == "bilinear":
        resample_method = zil.ResizeMethod.Bilinear
    else:
        raise ValueError(f"Invalid resample method: {resample}")

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
                    img = zil.Image.open(str(source_file))
                    img.auto_orient(in_place=True)
                    src_width, src_height = img.dimensions()
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

                    img.resize(
                        dest_width,
                        dest_height,
                        method=resample_method,
                        in_place=True,
                    )

                    # if "exif" in img.info:
                    #     # Change EXIF resolution info.
                    #     exif_dict = piexif.load(img.info["exif"])
                    #     # exif_dict['0th'][piexif.ImageIFD.ImageWidth] = width
                    #     # exif_dict['0th'][piexif.ImageIFD.ImageLength] = height
                    #     exif_dict["Exif"][piexif.ExifIFD.PixelXDimension] = dest_width
                    #     exif_dict["Exif"][piexif.ExifIFD.PixelYDimension] = dest_height
                    #     exif_bytes = piexif.dump(exif_dict)
                    #
                    #     if watermark:
                    #         img, _, inverse_transpose = exif_transpose_delete_exif(img)
                    #         img = watermark_signature(img).convert("RGB")
                    #         if inverse_transpose is not None:
                    #             img = img.transpose(inverse_transpose)
                    #     img.save(dest_file, quality=quality, exif=exif_bytes)
                    # else:
                    #     if watermark:
                    #         img = watermark_signature(img).convert("RGB")
                    #     img.save(dest_file, quality=quality)
                    img.save(str(dest_file), format=zil.ImageFormat.JPEG)

    if nb_warning > 0:
        logger.warning("%d warning(s) found.", nb_warning)

    if nb_error > 0:
        logger.error("%d error(s) found.", nb_error)
    else:
        logger.success("Resizing successful!")
