#!/usr/bin/env python3

COLOUR_RANGE_FULL = ["-color_range", "pc", "-colorspace", "bt709", "-color_trc", "bt709", "-color_primaries", "bt709", "-pix_fmt", "yuvj420p"]

import subprocess

import os
import argparse
import coloredlogs, logging, verboselogs


class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass

parser = argparse.ArgumentParser(
        description='''Resize all of the videos and output to another directory.
Author: Kiyoon Kim (yoonkr33@gmail.com)''',
        formatter_class=Formatter)
parser.add_argument('source_dir', type=str, 
        help='Directory to resize')
parser.add_argument('destination_dir', type=str,
        help='Destination directory')
parser.add_argument('--resize', action='store_true',
        help='Resize the video. Set --height.')
parser.add_argument('--height', type=int, default=720,
        help='Output resolution (height).')
parser.add_argument('--cpu', action='store_true',
        help='Use CPU instead of GPU to encode videos.')
parser.add_argument('--crf', type=int, default=21,
        help='crf (quality) for CPU encoding.')
parser.add_argument('-v', '--video_bitrate', type=int, default=4000,
        help='Kilo-bitrate for GPU encoding.')
parser.add_argument('-a', '--audio_bitrate', type=int, default=128,
        help='Kilo-bitrate for audio')
parser.add_argument('-s', '--audio_samplerate', type=int, default=48000,
        help='Sampling rate for audio')
parser.add_argument('-r', '--resample', type=str, choices=['nearest', 'bilinear', 'bicubic', 'lanczos'], default='bicubic',
        help='Resampling algorithm (for CPU). In GPU mode, always use super-sampling algorithm.')
parser.add_argument('--ext', type=str, nargs='*', default=['mp4'],
        help='Video file extensions to find.')

args = parser.parse_args()


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
                    logger.info("Encoding video to: %s", dest_file)
                    ffmpeg_cmd_head = ["ffmpeg", "-hide_banner", "-loglevel", "info"]
                    ffmpeg_cmd_nvdecode = ["-vsync", "0", "-hwaccel", "cuvid", "-c:v", "h264_cuvid"]
                    ffmpeg_youtube_recommended = ["-coder", "1", "-movflags", "+faststart", "-g", "12", "-bf", "2"]
                    if args.cpu:
                        ffmpeg_cmd_video = ["-i", source_file, "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-crf", "%d" % args.crf] + ffmpeg_youtube_recommended + COLOUR_RANGE_FULL
                        ffmpeg_cmd_resize = ["-vf", "scale=-2:{:d}".format(args.height), "-sws_flags", args.resample]
                    else:
                        ffmpeg_cmd_video = ffmpeg_cmd_nvdecode + ["-i", source_file, "-c:v", "h264_nvenc", "-rc:v", "vbr_hq", "-cq:v", "10", "-b:v", "%dk" % args.video_bitrate, "-maxrate:v", "%dk" % (args.video_bitrate * 2), "-profile:v", "high"] + ffmpeg_youtube_recommended + COLOUR_RANGE_FULL
                        ffmpeg_cmd_resize = ["-vf", "scale_npp=-2:{:d}:interp_algo=super".format(args.height)]

                    # -map 0 to copy all audio streams (and possibly metadata?)
                    # libfdk_aac codec has a higher quality (but defaults to a low-pass filter of 14kHz), so consider using it in case you have it enabled.
                    ffmpeg_cmd_audio_aac = ["-c:a", "aac", "-b:a", "%dk" % args.audio_bitrate, "-ar", "%d" % args.audio_samplerate, "-profile:a", "aac_low"]
                    ffmpeg_cmd_output = ["-f", "mp4", dest_file]

                    ffmpeg_cmd = ffmpeg_cmd_head + ffmpeg_cmd_video
                    if args.resize:
                        ffmpeg_cmd += ffmpeg_cmd_resize
                    ffmpeg_cmd += ffmpeg_cmd_audio_aac + ffmpeg_cmd_output

                    subprocess.run(ffmpeg_cmd,
                                    check=True)


    if nb_warning > 0:
        logger.warning("%d warning(s) found.", nb_warning)

    if nb_error > 0:
        logger.error("%d error(s) found.", nb_error)
    else:
        logger.success("Resizing successful!")
