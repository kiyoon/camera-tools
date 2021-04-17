#!/usr/bin/env python3


import argparse

class Formatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass

parser = argparse.ArgumentParser(
        description='''Convert SRT subtitles to YouTube timestamp chapters.

Author: Kiyoon Kim (yoonkr33@gmail.com)''',
        formatter_class=Formatter)
parser.add_argument('input_srt', type=str,
        help='Subtitles file to read.')

args = parser.parse_args()

import os, sys
import srt
import time
import srt_utils

if __name__ == "__main__":

    with open(args.input_srt, 'r', encoding="utf8") as f:
        srt_lines = list(srt.parse(f))

    youtube_chapters = srt_utils.srt_to_youtube_chapters(srt_lines)
    print(youtube_chapters)
