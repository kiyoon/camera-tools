#!/usr/bin/env python3

from PIL import Image

import os
import argparse
import coloredlogs, logging, verboselogs


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
parser.add_argument('-H', '--height', type=int, default=2000,
        help='Output image height.')
parser.add_argument('-W', '--width', type=int, default=3000,
        help='Output image width.')
parser.add_argument('-q', '--quality', type=int, default=95,
        help='Output image jpeg quality.')
parser.add_argument('-r', '--resample', type=str, choices=['nearest', 'bilinear', 'bicubic', 'lanczos'], default='bicubic',
        help='Resampling algorithm.')
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
 # My image is a 200x374 jpeg that is 102kb large
                    img = Image.open(source_file)
                    img = img.resize((args.width,args.height), resample=resample_str_to_pil_code(args.resample))
                    img.save(dest_file, quality=args.quality)

    if nb_warning > 0:
        logger.warning("%d warning(s) found.", nb_warning)

    if nb_error > 0:
        logger.error("%d error(s) found.", nb_error)
    else:
        logger.success("Resizing successful!")