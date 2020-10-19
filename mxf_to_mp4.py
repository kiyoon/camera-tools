#!/usr/bin/env python3

COLOUR_RANGE_FULL = ["-color_range", "pc", "-colorspace", "bt709", "-color_trc", "bt709", "-color_primaries", "bt709", "-pix_fmt", "yuvj420p"]
COLOUR_RANGE_LIMITED = ["-color_range", "tv", "-colorspace", "bt709", "-color_trc", "bt709", "-color_primaries", "bt709", "-pix_fmt", "yuvj420p"]


import argparse

class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass

parser = argparse.ArgumentParser(
        description='''Convert MXF high resolution files to MP4 using FFMPEG.
Always assume that the files are in limited colour range.

Author: Kiyoon Kim (yoonkr33@gmail.com)''',
        formatter_class=Formatter)
parser.add_argument('input_files', type=str, nargs='+',
        help='files you want to change names into dates')
parser.add_argument('--cpu', action='store_true',
        help='Use CPU instead of GPU to encode videos.')
parser.add_argument('--crf', type=int, default=17,
        help='crf (quality) for CPU encoding.')
parser.add_argument('-v', '--video_bitrate', type=int, default=15000,
        help='Kilo-bitrate for GPU encoding.')
parser.add_argument('-r', '--rescale_height', type=int, default=None,
        help='Height value for rescaling. (Only cpu support)')
parser.add_argument('-a', '--audio_bitrate', type=int, default=384,
        help='Kilo-bitrate for audio')
parser.add_argument('-s', '--audio_samplerate', type=int, default=48000,
        help='Sampling rate for audio')

args = parser.parse_args()

if not args.cpu and args.rescale_height is not None:
    parser.error("--cpu and --rescale_height can't come together.")

import coloredlogs, logging, verboselogs

import os, sys
import glob
import subprocess


if __name__ == "__main__":
    logger = verboselogs.VerboseLogger(__name__)
    coloredlogs.install(fmt='%(asctime)s - %(levelname)s - %(message)s', level='INFO', logger=logger)

    nb_error = 0
    nb_warning = 0

    num_mxf_files = 0
    for origpath in args.input_files:
        for path in glob.glob(origpath):    # glob: Windows wildcard support
            num_mxf_files += 1

    logger.info("%d files to encode", num_mxf_files)

    for origpath in args.input_files:
        for source_file in glob.glob(origpath):    # glob: Windows wildcard support
            root, fname_ext = os.path.split(source_file)
            fname, fext = os.path.splitext(fname_ext)

            dest_file = os.path.join(root, fname + ".mp4")

            if os.path.isfile(dest_file):
                nb_error += 1
                logger.error("Destination file already exists: %s", dest_file)
            else:
                # ffmpeg
                logger.info("Encoding video to %s", dest_file)

                colour_range = COLOUR_RANGE_LIMITED


                ffmpeg_cmd_head = ["ffmpeg", "-hide_banner", "-loglevel", "info"]

                ffmpeg_youtube_recommended = ["-coder", "1", "-movflags", "+faststart", "-g", "12", "-bf", "2"]
                if args.cpu:
                    ffmpeg_cmd_video = ["-i", source_file, "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-crf", "%d" % args.crf] + ffmpeg_youtube_recommended + colour_range
                    if args.rescale_height is not None:
                        ffmpeg_cmd_video += ["-vf", "scale=-2:%d" % args.rescale_height]
                else:
                    ffmpeg_cmd_video = ["-i", source_file, "-c:v", "h264_nvenc", "-rc:v", "vbr_hq", "-cq:v", "10", "-b:v", "%dk" % args.video_bitrate, "-maxrate:v", "%dk" % (args.video_bitrate * 2), "-profile:v", "high"] + ffmpeg_youtube_recommended + colour_range

                # -map 0 to copy all audio streams (and possibly metadata?)
                # libfdk_aac codec has a higher quality (but defaults to a low-pass filter of 14kHz), so consider using it in case you have it enabled.
                ffmpeg_cmd_audio_aac = ["-c:a", "aac", "-b:a", "%dk" % args.audio_bitrate, "-ar", "%d" % args.audio_samplerate, "-profile:a", "aac_low"]
                ffmpeg_cmd_output = ["-f", "mp4", dest_file]

                ffmpeg_cmd = ffmpeg_cmd_head + ffmpeg_cmd_video + ffmpeg_cmd_audio_aac + ffmpeg_cmd_output

                subprocess.run(ffmpeg_cmd,
                                check=True)

    if nb_warning > 0:
        logger.warning("%d warning(s) found.", nb_warning)

    if nb_error > 0:
        logger.error("%d error(s) found.", nb_error)
    else:
        logger.success("Conversion successful!")
