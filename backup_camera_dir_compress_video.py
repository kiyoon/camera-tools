#!/usr/bin/env python3

import os
import subprocess
import argparse
from shutil import copy2
import filecmp
import coloredlogs, logging, verboselogs
import exiftool

EXIF_CAMERA_MODEL = 'EXIF:Model'
#EXIF_VIDEO_WIDTH = "EXIF:RelatedImageWidth"
EXIF_VIDEO_HEIGHT = "EXIF:RelatedImageHeight"
EXIF_VIDEO_FPS = "QuickTime:VideoFrameRate"
DOUBLE_BITRATE_FPS = [40,80]
QUADRUPLE_BITRATE_FPS = [80, 150]

class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass

parser = argparse.ArgumentParser(
        description='''Copy a directory, but skips the files that are already copied (note that it doesn't compare the file content but only performs os.stat() comparison) and skips CR3 files, and if there are Canon M50 videos then compress them using NVIDIA hardware acceleration. Written for backing up my photo and video collection taken with Canon M50. Full HD videos are encoded to bitrate 8000k, and 4K videos to 32000k. You can also change the desired bitrate optionally.
Author: Kiyoon Kim (yoonkr33@gmail.com)''',
        formatter_class=Formatter)
parser.add_argument('source_dir', type=str, 
        help='Directory to copy')
parser.add_argument('destination_dir', type=str,
        help='Destination directory')
parser.add_argument('-H', '--hd_bitrate', type=int, default=4000,
        help='Kilo-bitrate for 720p videos. Double this if the frame rate is higher than 40.')
parser.add_argument('-f', '--fullhd_bitrate', type=int, default=8000,
        help='Kilo-bitrate for Full HD videos. Double this if the frame rate is higher than 40.')
parser.add_argument('-u', '--uhd_bitrate', type=int, default=32000,
        help='Kilo-bitrate for 4K videos. Double this if the frame rate is higher than 40')
parser.add_argument('--exif_camera_model', type=str, default='Canon EOS M50',
        help='Bitrate for 4K videos')
parser.add_argument('--skip_ext', type=str, nargs='*', default=['CR3'],
        help='File extensions to skip')

args = parser.parse_args()

class CopyFile(Exception): pass
class DontCopyFile(Exception): pass

def check_file_canon_video(source_file):
    if ext == "mp4":
        with exiftool.ExifTool() as et:
            metadata = et.get_metadata(source_file)

        if EXIF_CAMERA_MODEL in metadata.keys():
            camera_model = metadata[EXIF_CAMERA_MODEL]

            if camera_model == args.exif_camera_model:  # Check if the video is taken from the predefined camera
                return True, metadata
    return False, None


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
                if filecmp.cmp(source_file,dest_file,shallow=True):     # doesn't compare file content
                    logger.info("Skipping file (already exists): %s", dest_file)
                else:
                    if check_file_canon_video(source_file)[0]:
                        logger.info("Skipping compressed video (warning: might not be encoded properly but not verifying): %s", dest_file)
                    else:
                        logger.error("File already exists but not identical: %s", dest_file)
                        nb_error += 1
            else:
                try:
                    skip_ext = [x.lower() for x in args.skip_ext]

                    if ext in skip_ext:
                        logger.info("Skipping file (skip rule): %s", dest_file)
                        raise DontCopyFile()

                    is_canon_video, metadata = check_file_canon_video(source_file)
                    if is_canon_video:
                        #video_width = int(metadata[EXIF_VIDEO_WIDTH])
                        video_height = int(metadata[EXIF_VIDEO_HEIGHT])
                        video_fps = float(metadata[EXIF_VIDEO_FPS])
                        #logger.warning("%d %d %f", video_width, video_height, video_fps)
                        if video_height == 720:
                            bitrate = args.hd_bitrate
                        elif video_height == 1080:
                            bitrate = args.fullhd_bitrate
                        elif video_height == 2160:
                            bitrate = args.uhd_bitrate
                        else:
                            logger.warning("Video height not recognised. Copying file (instead of compressing) to %s", dest_file)
                            nb_warning += 1
                            raise CopyFile()

                        if DOUBLE_BITRATE_FPS[0] <= video_fps < DOUBLE_BITRATE_FPS[1]:
                            bitrate *= 2
                        elif QUADRUPLE_BITRATE_FPS[0] <= video_fps < QUADRUPLE_BITRATE_FPS[1]:
                            bitrate *= 4

                        # ffmpeg
                        
                        logger.info("Encoding video to %s", dest_file)
                        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "info", "-hwaccel", "cuvid", "-c:v", "h264_cuvid", "-i", source_file, "-c:v", "h264_nvenc", "-rc:v", "vbr_hq", "-cq:v", "10", "-b:v", "%dk" % bitrate, "-maxrate:v", "%dk" % (bitrate * 2), "-profile:v", "high", "-color_range", "pc", "-colorspace", "bt709", "-color_trc", "bt709", "-color_primaries", "bt709", "-c:a", "copy", dest_file])

                        raise DontCopyFile()

                    logger.info("Copying file to: %s", dest_file)
                    raise CopyFile()
                        
                except CopyFile:
                    copy2(source_file, dest_file)

                except DontCopyFile:
                    pass

                except subprocess.CalledProcessError:
                    logger.error("ffmpeg exited with non-zero return code: %s", dest_file)
                    nb_error += 1



    if nb_warning > 0:
        logger.warning("%d warning(s) found.", nb_warning)

    if nb_error > 0:
        logger.error("%d error(s) found.", nb_error)
    else:
        logger.success("Back up successful!")
