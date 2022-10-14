#!/usr/bin/env python3

import os
import subprocess
import argparse
from shutil import copy2
import filecmp
import coloredlogs, logging, verboselogs
import exiftool
from fractions import Fraction

EXIF_CAMERA_MODEL = 'EXIF:Model'
#EXIF_VIDEO_WIDTH = "EXIF:RelatedImageWidth"
#EXIF_VIDEO_HEIGHT = "EXIF:RelatedImageHeight"
EXIF_VIDEO_HEIGHT = "QuickTime:ImageHeight"
EXIF_VIDEO_FPS = "QuickTime:VideoFrameRate"
EXIF_MKV_VIDEO_HEIGHT = "Matroska:ImageHeight"
EXIF_MKV_VIDEO_FPS = "Matroska:VideoFrameRate"
DOUBLE_BITRATE_FPS = [40,80]
QUADRUPLE_BITRATE_FPS = [80, 150]

EXIF_OBS_GRAPHICS_MODE = 'QuickTime:GraphicsMode'
EXIF_OBS_TRACK2NAME = 'QuickTime:Track2Name'
OBS_AUDIOTRACK_NAME = 'All (recording)'         # Assuming that the first audio track is names as this for all OBS videos.

COLOUR_RANGE_FULL = ["-color_range", "pc", "-colorspace", "bt709", "-color_trc", "bt709", "-color_primaries", "bt709"]


FFPROBE = ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-print_format", "json"]

class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass

parser = argparse.ArgumentParser(
        description='''Find and copy all Canon MP4 files to HEVC 10bit 4:2:0 MOV proxy files using Nvidia-accelerated encoding.
Uses short GOP for faster decoding.
Always force to 1080p quality.
Suitable, but not limited to Canon Log files shot with R3, R5, R6, and R7.
Author: Kiyoon Kim (yoonkr33@gmail.com)''',
        formatter_class=Formatter)
parser.add_argument('source_dir', type=str, 
        help='Directory to search original videos. Tip: use C:\\path\\.\\example\\demo to indicate destination directory should include directories after the dot, in this case "example\\demo" directory.')
parser.add_argument('destination_dir', type=str,
        help='Destination to make proxy files.')
parser.add_argument('-b', '--bitrate', type=int, default=10000,
        help='Kilo-bitrate for Full HD videos. Double this if the frame rate is higher than 40.')
parser.add_argument('--verify_encoded_videos', action='store_true',
        help='Verify if the encoding has not failed, by seeing if duration almost matches (up to a second)')

args = parser.parse_args()


import json
def ffprobe(source_file):
    proc = subprocess.Popen(FFPROBE + [source_file], stdout=subprocess.PIPE, shell=False)
    (ffprobe_out, ffprobe_err) = proc.communicate()
    ffprobe_out = ffprobe_out.decode('utf-8')
    return json.loads(ffprobe_out)

eligible_cameras = ['R3', 'R5', 'R6', 'R7']
def check_file_eligible_video(source_file, ext):
    if ext == "mp4":
        try:
            with exiftool.ExifTool() as et:
                metadata = et.get_metadata(source_file)
        except json.decoder.JSONDecodeError:
            ffprobe_out = ffprobe(source_file)
            return 'failed', None, ffprobe_out      # failed to read the metadata. Possibly Korean filename?

        if EXIF_CAMERA_MODEL in metadata.keys():
            camera_model = metadata[EXIF_CAMERA_MODEL]

            if camera_model == 'Canon EOS R5':  # Check if the video is taken from the predefined camera
                return 'R5', metadata, None
            elif camera_model == 'Canon EOS R6':  # Check if the video is taken from the predefined camera
                return 'R6', metadata, None
            elif camera_model == 'Canon EOS R7':  # Check if the video is taken from the predefined camera
                return 'R7', metadata, None
            elif camera_model == 'Canon EOS R3':  # Check if the video is taken from the predefined camera
                return 'R3', metadata, None
    return 'unknown', None, None


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

    # If source_dir contains /./ add relative directory to the destination from this point.
    # Similar to how rsync works.
    relative_point = args.source_dir.find(os.path.sep + '.' + os.path.sep)    

    for root, dirs, files in os.walk(args.source_dir):
        if relative_point > 0:
            dest_root = root.replace(args.source_dir,
                    os.path.join(args.destination_dir, args.source_dir[relative_point+3:]), 1)
        else:
            dest_root = root.replace(args.source_dir, args.destination_dir, 1)

        for name in files:
            ext = os.path.splitext(name)[1][1:].lower()
            source_file = os.path.join(root, name)
            dest_file = os.path.join(dest_root, os.path.splitext(name)[0] + '.mov')

            if ext != 'mp4':
                continue
            
            if os.path.isfile(dest_file):
                if filecmp.cmp(source_file,dest_file,shallow=True):     # doesn't compare file content
                    logger.info("Skipping file (already exists): %s", dest_file)
                else:
                    camera_brand, _, ffprobe_source = check_file_eligible_video(source_file, ext)
                    if camera_brand in eligible_cameras:
                        if args.verify_encoded_videos:
                            if ffprobe_source is None:
                                ffprobe_source = ffprobe(source_file)
                            ffprobe_dest = ffprobe(dest_file)
                            if abs(float(ffprobe_source['streams'][0]['duration']) - float(ffprobe_dest['streams'][0]['duration'])) > 1.0:
                                logger.error("Video not encoded properly! Skipping: %s", dest_file)
                                nb_error += 1
                            else:
                                logger.info("Skipping compressed video: %s", dest_file)
                        else:
                            logger.info("Skipping compressed video (warning: might not be encoded properly but not verifying): %s", dest_file)
                    else:
                        logger.error("File already exists but not identical: %s", dest_file)
                        nb_error += 1
            else:
                try:
                    camera_brand, metadata, ffprobe_out = check_file_eligible_video(source_file, ext)

                    if camera_brand == 'failed':
                        logger.warning("Cannot identify metadata from video: %s. Korean file names may not be supported.", source_file)
                        nb_warning += 1
                        continue
                    elif camera_brand == 'unknown':
                        logger.info("Skipping non-supported videos not taken from Canon: %s", source_file)
                        continue


                    if metadata is not None:
                        video_height = int(metadata[EXIF_VIDEO_HEIGHT])
                        video_fps = float(metadata[EXIF_VIDEO_FPS])
                    elif ffprobe_out is not None:
                        # read video height and fps using ffprobe
                        video_height = int(ffprobe_out['streams'][0]['height'])
                        video_fps = float(Fraction(ffprobe_out['streams'][0]['r_frame_rate']))
                    else:
                        raise Exception("Can't read metadata")

                    bitrate = args.bitrate
                    if DOUBLE_BITRATE_FPS[0] <= video_fps < DOUBLE_BITRATE_FPS[1]:
                        bitrate *= 2
                    elif QUADRUPLE_BITRATE_FPS[0] <= video_fps < QUADRUPLE_BITRATE_FPS[1]:
                        bitrate *= 4
                    elif video_fps >= QUADRUPLE_BITRATE_FPS[1]:
                        bitrate *= 8

                    # ffmpeg
                    logger.info("Encoding video to %s", dest_file)

                    ffmpeg_cmd_head = ["ffmpeg", "-hide_banner", "-loglevel", "info"]
                    ffmpeg_cmd_video = ["-i", source_file,
                            "-vf", "scale=-2:1080", 
                            "-c:v", "hevc_nvenc",
                            "-pix_fmt", "p010le",
                            "-rc:v", "vbr_hq", "-cq:v", "10",
                            "-movflags", "+faststart", "-g", "12",
                            "-b:v", "%dk" % bitrate, "-maxrate:v", "%dk" % (bitrate * 2),
                            ] + COLOUR_RANGE_FULL

                    # -map 0 to copy all streams (including metadata?)
                    # -map 0:a to copy all audio streams
                    ffmpeg_cmd_audio_copy = ["-c:a", "copy", "-map", "0"]
                    # libfdk_aac codec has a higher quality (but defaults to a low-pass filter of 14kHz), so consider using it in case you have it enabled.
                    #ffmpeg_cmd_audio_aac = ["-c:a", "aac", "-b:a", "256k", "-ar", "48000"]
                    ffmpeg_cmd_output = [dest_file]
                    ffmpeg_cmd = ffmpeg_cmd_head + ffmpeg_cmd_video + ffmpeg_cmd_audio_copy + ffmpeg_cmd_output

                    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                    subprocess.run(ffmpeg_cmd,
                            check=True)


                except subprocess.CalledProcessError:
                    logger.exception("ffmpeg exited with non-zero return code: %s", dest_file)
                    nb_error += 1
                    logger.info("Removing %s", dest_file)
                    os.remove(dest_file)



    if nb_warning > 0:
        logger.warning("%d warning(s) found.", nb_warning)

    if nb_error > 0:
        logger.error("%d error(s) found.", nb_error)
    else:
        logger.success("Proxy successfully generated!")
