import DaVinciResolveScript as dvr

if __name__ == "__main__":
    resolve = dvr.scriptapp("Resolve")
    pm = resolve.GetProjectManager()
    proj = pm.GetCurrentProject()
    # tl = proj.GetCurrentTimeline()
    mp = proj.GetMediaPool()

    # Add file to media pool
    media_path = "/media/kiyoon/NVME1T/Videos/BTS_Dynamite.mp4"
    media_items = mp.ImportMedia([media_path])

    media_fps = media_items[0].GetClipProperty("FPS")
    print(f"Media FPS: {media_fps}")

    # Create new timeline
    tl = mp.CreateEmptyTimeline("cut_detection_timeline")

    proj.SetSetting("timelineFrameRate", media_fps)

    # Add media to timeline
    mp.AppendToTimeline(media_items)

    # Timeline start timecode
    # By default it starts from 1 hour. Change it to 0 hour.
    tl.SetStartTimecode("00:00:00:00")

    success = tl.DetectSceneCuts()
    print(success)

    clips = tl.GetItemsInTrack("video", 1)

    for idx, clip in clips.items():
        clip_start = clip.GetStart()
        clip_end = clip.GetEnd()
        clip_duration = clip_end - clip_start

        print()
        print(f"{clip_start = }")
        print(f"{clip_end = }")
        print(f"{clip_duration = }")
