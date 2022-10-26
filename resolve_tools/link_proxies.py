#!/usr/bin/env python3

# For Resolve 18.
# Python 3.10

print('a')
import DaVinciResolveScript as dvr
from datetime import datetime
import os
from tqdm import tqdm

if __name__ == '__main__':
    resolve = dvr.scriptapp('Resolve')
    pm = resolve.GetProjectManager()
    proj = pm.GetCurrentProject()
    tl = proj.GetCurrentTimeline()
    mp = proj.GetMediaPool()

    frame_rate = proj.GetSetting('timelineFrameRate')
    #timeline_name = tl.GetName()
    print(frame_rate)

    folder = mp.GetCurrentFolder()
    clips = folder.GetClips()


    # print("Scanning and finding the earliest time..")
    # earliest_date = None
    # for i in clips:
    #     clip_fullname = (clips[i].GetClipProperty("Clip Name"))
    #     clip_name = os.path.splitext(clip_fullname)[0]

    #     date_str = clip_name[clip_name.find('_')+1:]
    #     date_time = datetime.strptime(date_str, "%Y%m%d_%H%M%S.%f%z")

    #     if earliest_date is None:
    #         earliest_date = date_time
    #     else:
    #         if (date_time - earliest_date).total_seconds() < 0:
    #             earliest_date = date_time

    print("Linking proxies")
    for i in tqdm(clips):
        clip_fullpath = (clips[i].GetClipProperty("File Path"))
        clip_fullpath_wo_ext, ext = os.path.splitext(clip_fullpath)

        if ext.lower() == '.mp4':
            proxy_path = clip_fullpath_wo_ext.replace('G:\\Video', 'I:\OneDrive - University of Edinburgh\Davinci Resolve\\Proxies', 1) + '.mov'

            tqdm.write(f'Linking {clip_fullpath}')
            tqdm.write(f'To proxy: {proxy_path}')

            clips[i].LinkProxyMedia(proxy_path)
