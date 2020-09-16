#!/usr/bin/env python3

import tqdm

import os
import sys
import argparse
import coloredlogs, logging, verboselogs

from PIL import Image


class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass

parser = argparse.ArgumentParser(
        description='''Find directories that contain images and make them into GIFs. Output filename will be the same as the dir name.
Author: Kiyoon Kim (yoonkr33@gmail.com)''',
        formatter_class=Formatter)
parser.add_argument('source_dir', type=str, 
        help='Directory to make gif')
parser.add_argument('--ext', type=str, nargs='*', default=['JPG', 'PNG'],
        help='Image file extensions to find.')
parser.add_argument('-d', '--divide', type=int, default=5,
        help='Output image resolution (width, height) is divided by this factor.')
parser.add_argument('-r', '--resample', type=str, choices=['nearest', 'bilinear', 'bicubic', 'lanczos'], default='bicubic',
        help='Resampling algorithm.')
parser.add_argument('-l', '--num_loops', type=int, default=0,
        help='Number of loops. 0 means infinite')
parser.add_argument('--duration', type=int, default=200,
        help='Duration for each frame in milliseconds.')
parser.add_argument('--no_optimise', action='store_false', dest='optimise',
        help="Don't optimise the output GIFs.")

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

    exts = [x.lower() for x in args.ext]

    for root, dirs, files in os.walk(args.source_dir):
        gif_frames = []
        for name in files:
            ext = os.path.splitext(name)[1][1:].lower()
            source_file = os.path.join(root, name)

            if ext in exts:
                img = Image.open(source_file)
                src_width, src_height = img.size
                dest_width, dest_height = src_width // args.divide, src_height // args.divide
                img = img.resize((dest_width,dest_height), resample=resample_str_to_pil_code(args.resample))
                gif_frames.append(img)

        if len(gif_frames) >= 2:        # requires at least 2 images
            output_gif_name = root + '.gif'
            if os.path.isfile(output_gif_name):
                logger.error('File already exists: %s', output_gif_name)
                nb_error += 1
            else:
                logger.info('Saving to %s', output_gif_name)
                gif_frames[0].save(output_gif_name,
                                save_all=True, append_images=gif_frames[1:], optimize=args.optimise, duration=args.duration, loop=args.num_loops)


    if nb_warning > 0:
        logger.warning("%d warning(s) found.", nb_warning)

    if nb_error > 0:
        logger.error("%d error(s) found.", nb_error)
    else:
        logger.success("Converting GIF successful!")
