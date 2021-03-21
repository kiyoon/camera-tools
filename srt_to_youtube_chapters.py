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

if __name__ == "__main__":

    with open(args.input_srt, 'r', encoding="utf8") as f:
        srt_lines = list(srt.parse(f))

    #print(srt_lines)
    for subtitle in srt_lines:
        content = subtitle.content.replace('<b>', '').replace('</b>', '')
        seconds = int(subtitle.start.total_seconds())
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        if hours == 0:
            print(f"{minutes:02d}:{seconds:02d} {content}")
        else:
            print(f"{hours:02d}:{minutes:02d}:{seconds:02d} {content}")

