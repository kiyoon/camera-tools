#!/usr/bin/env python3

import datetime

import srt


def srt_drift_fix_NTSC(  # noqa: N802
    srt_list: list[srt.Subtitle],
    offset_hour: int = 0,
    multiplier: float = 1001 / 1000,
):
    """
    Fix SRT drifting when using 23.976, 29.97 NDF, 59.94 NDF framerate.

    params:
        srt_list: srt.parse() converted to list
        offset_hour: if timecode starts from a certain hour, this value should be that.
        multiplier: 24 Timecode to 23.976 conversion rate. You probably won't need to change this, unless you don't want to convert (in which case it would be 1)

    Returns:
        None, but the input srt_list is in sync.
    """
    for subtitle in srt_list:
        subtitle.start = datetime.timedelta(
            seconds=(subtitle.start.total_seconds() - offset_hour * 3600) * multiplier
        )
        subtitle.end = datetime.timedelta(
            seconds=(subtitle.end.total_seconds() - offset_hour * 3600) * multiplier
        )


def srt_to_youtube_chapters(srt_list: list[srt.Subtitle]) -> str:
    youtube_chapters = []

    for subtitle in srt_list:
        content = subtitle.content.replace("<b>", "").replace("</b>", "")
        seconds = int(subtitle.start.total_seconds())
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        if hours == 0:
            youtube_chapters.append(f"{minutes:02d}:{seconds:02d} {content}")
        else:
            youtube_chapters.append(
                f"{hours:02d}:{minutes:02d}:{seconds:02d} {content}"
            )

    return "\n".join(youtube_chapters)
