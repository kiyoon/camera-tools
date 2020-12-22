#!/usr/bin/env python3

# Requires python3.6 (only)

import DaVinciResolveScript as dvr
from datetime import datetime
import os
import tqdm

if __name__ == '__main__':
    resolve = dvr.scriptapp('Resolve')
    pm = resolve.GetProjectManager()
    proj = pm.GetCurrentProject()
    tl = proj.GetCurrentTimeline()
    mp = proj.GetMediaPool()

    frame_rate = proj.GetSetting('timelineFrameRate')
    #timeline_name = tl.GetName()
    print(frame_rate)

    if frame_rate in ['29.970', '59.940']:
        print("Warning: use Drop Frame Timecode for accuracy")

    if frame_rate == '23.976':
        sync_multiplier = 1000/1001  # 23.976 / 24
    else:
        #sync_multiplier = 1000/1001    # this seems more correct? IDK
        sync_multiplier = 1

    if frame_rate == '23.976':
        integer_fps = 24
    elif frame_rate.startswith('29.970'):
        integer_fps = 30
    elif frame_rate.startswith('59.940'):
        integer_fps = 60
    else:
        integer_fps = int(frame_rate)

    folder = mp.GetCurrentFolder()
    clips = folder.GetClips()


    print("Scanning and finding the earliest time..")
    earliest_date = None
    for i in clips:
        clip_fullname = (clips[i].GetClipProperty("Clip Name"))
        clip_name = os.path.splitext(clip_fullname)[0]

        date_str = clip_name[clip_name.find('_')+1:]
        date_time = datetime.strptime(date_str, "%Y%m%d_%H%M%S.%f%z")

        if earliest_date is None:
            earliest_date = date_time
        else:
            if (date_time - earliest_date).total_seconds() < 0:
                earliest_date = date_time

    print("Setting timecode according to " + str(earliest_date))
    for i in tqdm.tqdm(clips):
        clip_fullname = (clips[i].GetClipProperty("Clip Name"))
        clip_name = os.path.splitext(clip_fullname)[0]

        date_str = clip_name[clip_name.find('_')+1:]
        date_time = datetime.strptime(date_str, "%Y%m%d_%H%M%S.%f%z")

        time_difference = date_time - earliest_date
        time_fps_synced = time_difference * sync_multiplier     # for 23.976 that uses 24.00fps timecode
        total_secs_floored = int(time_fps_synced.total_seconds())
        hours, remainder = divmod(total_secs_floored, 3600)
        minutes, seconds = divmod(remainder, 60)

        microsecs = time_fps_synced.microseconds
        frame_num = round((microsecs / 1000000) * integer_fps)

        clips[i].SetClipProperty('Start TC', '{:2d}:{:2d}:{:2d}:{:2d}'.format(hours, minutes, seconds, frame_num))
