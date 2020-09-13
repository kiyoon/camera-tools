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

#COLOUR_RANGE_FULL = ["-color_range", "pc", "-colorspace", "bt709", "-color_trc", "bt709", "-color_primaries", "bt709", "-pix_fmt", "yuvj420p"]
COLOUR_RANGE_FULL = ["-color_range", "pc", "-colorspace", "bt709", "-color_trc", "bt709", "-color_primaries", "bt709"]
#COLOUR_RANGE_LIMITED_NTSC = ["-color_range", "tv", "-colorspace", "smpte170m", "-color_trc", "smpte170m", "-color_primaries", "smpte170m", "-pix_fmt", "yuv420p"]
#COLOUR_RANGE_LIMITED_PAL = ["-color_range", "tv", "-colorspace", "bt470bg", "-color_trc", "gamma28", "-color_primaries", "bt470bg", "-pix_fmt", "yuv420p"]

"""
if ffprobe_out['streams'][0]['color_space'] == 'bt709':
    colour_range = COLOUR_RANGE_FULL
elif ffprobe_out['streams'][0]['color_space'] == 'smpte170m':
    colour_range = COLOUR_RANGE_LIMITED_NTSC
elif ffprobe_out['streams'][0]['color_space'] == 'bt470bg':
    colour_range = COLOUR_RANGE_LIMITED_PAL
"""


FFPROBE = ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-print_format", "json"]

class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass

parser = argparse.ArgumentParser(
        description='''Copy a directory, but skips the files that are already copied (note that it doesn't compare the file content but only performs os.stat() comparison) and skips CR3 files, and if there are Canon M50 videos then compress them using NVIDIA hardware acceleration. Written for backing up my photo and video collection taken with Canon M50. Full HD videos are encoded to bitrate 8000k, and 4K videos to 32000k. You can also change the desired bitrate optionally. We assume that all Canon videos have full range (pc) colour space, which is not true for some 10bit cameras (feature needs to be implemented).
It can be used for OBS files when --detect is set to OBS. It'll detect the colour space (full or limited) and encode accordingly.
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
parser.add_argument('--detect', type=str, default='camera', choices=['camera', 'OBS'],
        help='Whether to detect camera videos or OBS videos')
parser.add_argument('--action_detect_failed', type=str, default='copy', choices=['copy', 'encode'],
        help='When video detection is failed (due to Korean file name), copy the file or encode the file?')
parser.add_argument('--skip_ext', type=str, nargs='*', default=['CR3', 'ARW'],
        help='File extensions to skip')

args = parser.parse_args()

class CopyFile(Exception): pass
class DontCopyFile(Exception): pass

import json
def ffprobe(source_file):
    proc = subprocess.Popen(FFPROBE + [source_file], stdout=subprocess.PIPE, shell=False)
    (ffprobe_out, ffprobe_err) = proc.communicate()
    ffprobe_out = ffprobe_out.decode('utf-8')
    return json.loads(ffprobe_out)


def check_file_OBS_video(source_file, ext):
    """MP4 doesn't support an audio stream title, so we use exiftool to obtain this information.
    On the other hand, we use ffprobe for MKV.
    Detects OBS video with the first audio trackname as "All (recording)" and the colour space is bt709 (full range).
    """
    if ext == "mp4":
        try:
            with exiftool.ExifTool() as et:
                metadata = et.get_metadata(source_file)
        except json.decoder.JSONDecodeError:
            ffprobe_out = ffprobe(source_file)
            return 'failed', None, ffprobe_out      # failed to read the metadata. Possibly Korean filename?

        if EXIF_OBS_GRAPHICS_MODE in metadata.keys():
            graphics_mode = metadata[EXIF_OBS_GRAPHICS_MODE]
            if graphics_mode == 0:  # srcCopy

                if EXIF_OBS_TRACK2NAME in metadata.keys():
                    track2_name = metadata[EXIF_OBS_TRACK2NAME]
                    if track2_name == OBS_AUDIOTRACK_NAME:  # Assuming that the first audio track is names as this for all OBS videos.
                        ffprobe_out = ffprobe(source_file)
                        if ffprobe_out['streams'][0]['color_space'] == 'bt709':
                            return 'OBS', metadata, ffprobe_out
    elif ext == "mkv":
        try:
            with exiftool.ExifTool() as et:
                metadata = et.get_metadata(source_file)
        except json.decoder.JSONDecodeError:
            metadata = None         # failed to read the metadata. Possibly Korean filename?

        ffprobe_out = ffprobe(source_file)
        if ffprobe_out['streams'][1]['tags']['title'] == OBS_AUDIOTRACK_NAME:
            # Assuming that the first audio track is names as this for all OBS videos.
            if ffprobe_out['streams'][0]['color_space'] == 'bt709':
                return 'OBS', metadata, ffprobe_out

    return 'unknown', None, None

def check_file_M50_video(source_file, ext):
    if ext == "mp4":
        with exiftool.ExifTool() as et:
            metadata = et.get_metadata(source_file)

        if EXIF_CAMERA_MODEL in metadata.keys():
            camera_model = metadata[EXIF_CAMERA_MODEL]

            if camera_model == 'Canon EOS M50':  # Check if the video is taken from the predefined camera
                return 'M50', metadata, None
    return 'unknown', None, None

def check_file_a6000_video(source_file, ext):
    if ext == "mp4":
        with exiftool.ExifTool() as et:
            metadata = et.get_metadata(source_file)

        EXIF_MANUFACTURER = 'XML:DeviceManufacturer'
        if EXIF_MANUFACTURER in metadata.keys():
            manufacturer = metadata[EXIF_MANUFACTURER]

            if manufacturer == 'Sony':  # Check if the video is taken from the predefined camera
                return 'a6000', metadata, None
    return 'unknown', None, None


def check_file_camera_video(source_file, ext):
    brand, metadata, _ = check_file_M50_video(source_file, ext)
    if brand == 'unknown':
        brand, metadata, _ = check_file_a6000_video(source_file, ext)

    return brand, metadata, None


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

    check_file_camera_or_obs_video = check_file_camera_video if args.detect == 'camera' else check_file_OBS_video

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
            
            # Convert MKV to MP4 for OBS videos
            if args.detect == 'OBS':
                if ext == 'mkv':
                    if check_file_camera_or_obs_video(source_file, ext)[0] == 'OBS':
                        dest_file = dest_file[:-3] + 'mp4'

            if os.path.isfile(dest_file):
                if filecmp.cmp(source_file,dest_file,shallow=True):     # doesn't compare file content
                    logger.info("Skipping file (already exists): %s", dest_file)
                else:
                    if check_file_camera_or_obs_video(source_file, ext)[0] not in ['unknown', 'failed']:
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

                    camera_brand, metadata, ffprobe_out = check_file_camera_or_obs_video(source_file, ext)

                    if camera_brand == 'failed':
                        logger.warning("Cannot identify metadata from video: %s. Korean file names may not be supported.", source_file)
                        nb_warning += 1

                    camera_file_detected = camera_brand not in ['unknown', 'failed']
                    failed_but_encode = camera_brand == 'failed' and args.action_detect_failed == 'encode'

                    if camera_file_detected or failed_but_encode:
                        if metadata is not None:
                            if ext == "mp4":
                                video_height = int(metadata[EXIF_VIDEO_HEIGHT])
                                video_fps = float(metadata[EXIF_VIDEO_FPS])
                            elif ext == "mkv":
                                video_height = int(metadata[EXIF_MKV_VIDEO_HEIGHT])
                                video_fps = float(metadata[EXIF_MKV_VIDEO_FPS])
                            else:
                                raise Exception("Not supported file type")
                        elif ffprobe_out is not None:
                            # read video height and fps using ffprobe
                            video_height = int(ffprobe_out['streams'][0]['height'])
                            video_fps = float(Fraction(ffprobe_out['streams'][0]['r_frame_rate']))
                        else:
                            raise Exception("Can't read metadata")


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

                        ffmpeg_cmd_head = ["ffmpeg", "-hide_banner", "-loglevel", "info"]
                        ffmpeg_cmd_nvdecode = ["-hwaccel", "cuvid", "-c:v", "h264_cuvid"]
                        ffmpeg_cmd_video = ["-i", source_file, "-c:v", "h264_nvenc", "-rc:v", "vbr_hq", "-cq:v", "10", "-b:v", "%dk" % bitrate, "-maxrate:v", "%dk" % (bitrate * 2), "-profile:v", "high"] + COLOUR_RANGE_FULL

                        # -map 0 to copy all audio streams (and possibly metadata?)
                        ffmpeg_cmd_audio_copy = ["-c:a", "copy", "-map", "0"]
                        # (a6000 has time metadata, but dropping it because -movflags use_metadata_tags and -map_metadata 0 didn't work)
                        # libfdk_aac codec has a higher quality (but defaults to a low-pass filter of 14kHz), so consider using it in case you have it enabled.
                        ffmpeg_cmd_audio_aac = ["-c:a", "aac", "-b:a", "256k", "-ar", "48000"]
                        ffmpeg_cmd_output = [dest_file]
                        if camera_brand in ['M50', 'OBS', 'failed']:
                            # h264 nvidia decode, encode
                            # copy audio
                            ffmpeg_cmd = ffmpeg_cmd_head + ffmpeg_cmd_nvdecode + ffmpeg_cmd_video + ffmpeg_cmd_audio_copy + ffmpeg_cmd_output
                        elif camera_brand == 'a6000':
                            # h264 nvidia decode, encode
                            # audio aac 256k
                            ffmpeg_cmd = ffmpeg_cmd_head + ffmpeg_cmd_nvdecode + ffmpeg_cmd_video + ffmpeg_cmd_audio_aac + ffmpeg_cmd_output
                        else:
                            raise Exception("Not recognised camera brand: %s" % camera_brand)


                        subprocess.run(ffmpeg_cmd,
                                check=True)
                        # CPU
                        #subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "info", "-i", source_file, "-c:v", "libx264", "-rc:v", "vbr_hq", "-cq:v", "10", "-b:v", "%dk" % bitrate, "-maxrate:v", "%dk" % (bitrate * 2), "-profile:v", "high"] + colour_range + ["-c:a", "copy", "-map", "0", dest_file])

                        raise DontCopyFile()


                    # else:
                    logger.info("Copying file to: %s", dest_file)
                    raise CopyFile()
                        
                except CopyFile:
                    copy2(source_file, dest_file)

                except DontCopyFile:
                    pass

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
        logger.success("Back up successful!")
