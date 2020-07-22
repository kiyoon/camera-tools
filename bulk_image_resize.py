#!/usr/bin/env python3

from PIL import Image
from PIL.ExifTags import TAGS
import piexif

import os
import argparse
import coloredlogs, logging, verboselogs


from utils.burn_signature import watermark_signature
from utils.pil_transpose import exif_transpose_delete_exif

class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass

parser = argparse.ArgumentParser(
        description='''Resize all of the images and output to another directory.
Author: Kiyoon Kim (yoonkr33@gmail.com)''',
        formatter_class=Formatter)
parser.add_argument('source_dir', type=str, 
        help='Directory to resize')
parser.add_argument('destination_dir', type=str,
        help='Destination directory')
parser.add_argument('-d', '--divide', type=int, default=2,
        help='Output image resolution (width, height) is divided by this factor.')
parser.add_argument('-q', '--quality', type=int, default=95,
        help='Output image jpeg quality.')
parser.add_argument('-r', '--resample', type=str, choices=['nearest', 'bilinear', 'bicubic', 'lanczos'], default='bicubic',
        help='Resampling algorithm.')
parser.add_argument('-w', '--watermark', action='store_true',
        help='Watermark Instagram and YouTube channel on the image.')
parser.add_argument('--ext', type=str, nargs='*', default=['JPG', 'PNG'],
        help='Image file extensions to find.')

args = parser.parse_args()


def resample_str_to_pil_code(resample_str):
    resample_str = resample_str.lower()
    if resample_str == 'nearest':
        return Image.NEAREST
    elif resample_str == 'bilinear':
        return Image.BILINEAR
    elif resample_str == 'bicubic':
        return Image.BICUBIC
    elif resample_str == 'lanczos':
        return Image.LANCZOS

    raise NotImplementedError("'{}' not a recognised resampling algorithm.".format(resample_str))


if __name__ == '__main__':

    logger = verboselogs.VerboseLogger(__name__)
    coloredlogs.install(fmt='%(asctime)s - %(levelname)s - %(message)s', level='INFO', logger=logger)

    nb_error = 0
    nb_warning = 0

    args.source_dir = args.source_dir.rstrip('\\')
    args.source_dir = args.source_dir.rstrip('/')
    args.destination_dir = args.destination_dir.rstrip('\\')
    args.destination_dir = args.destination_dir.rstrip('/')

    logger.info("Creating directory: %s", args.destination_dir)
    os.makedirs(args.destination_dir, exist_ok=True)

    for root, dirs, files in os.walk(args.source_dir):
        dest_root = root.replace(args.source_dir, args.destination_dir, 1)

        for name in dirs:
            dest_dir = os.path.join(dest_root, name)
            logger.info("Creating directory: %s", dest_dir)
            os.makedirs(dest_dir, exist_ok=True)

        for name in files:
            ext = os.path.splitext(name)[1][1:].lower()
            source_file = os.path.join(root, name)
            dest_file = os.path.join(dest_root, name)
            
            if os.path.isfile(dest_file):
                logger.error("File already exists: %s", dest_file)
                nb_error += 1
            else:
                exts = [x.lower() for x in args.ext]

                if ext in exts:
                    logger.info("Resizing file to: %s", dest_file)
                    img = Image.open(source_file)
                    src_width, src_height = img.size
                    dest_width, dest_height = src_width // args.divide, src_height // args.divide 
                    img = img.resize((dest_width,dest_height), resample=resample_str_to_pil_code(args.resample))

                    # Change EXIF resolution info.
                    exif_dict = piexif.load(img.info['exif'])
                    #exif_dict['0th'][piexif.ImageIFD.ImageWidth] = args.width
                    #exif_dict['0th'][piexif.ImageIFD.ImageLength] = args.height
                    exif_dict['Exif'][piexif.ExifIFD.PixelXDimension] = dest_width
                    exif_dict['Exif'][piexif.ExifIFD.PixelYDimension] = dest_height
                    exif_bytes = piexif.dump(exif_dict)

                    if args.watermark:
                        img, _, inverse_transpose = exif_transpose_delete_exif(img)
                        img = watermark_signature(img).convert('RGB')
                        if inverse_transpose is not None:
                            img = img.transpose(inverse_transpose)
                    
                    img.save(dest_file, quality=args.quality, exif=exif_bytes)

    if nb_warning > 0:
        logger.warning("%d warning(s) found.", nb_warning)

    if nb_error > 0:
        logger.error("%d error(s) found.", nb_error)
    else:
        logger.success("Resizing successful!")
