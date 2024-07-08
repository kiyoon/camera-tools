# camera-tools: Collection of useful tools for managing photos and videos

## 🛠️ Installation

```
pip install .
```

## 📦 Features
### Change file names to date taken

It will rename the image or video files into the EXIF datetime, whilst creating undo script and json files containing EXIF information.

```bash
# For Canon R6
camera-tools datename '7E1A*.JPG' '7E1A*.MP4' -p R6_

# For Canon M50
camera-tools datename 'IMG_*.JPG' 'MVI_*.MP4' -p M50_

# For Sony a6000
camera-tools datename 'DSC*.JPG' -p a6000_ --raw-ext ARW --date_source file_modified
camera-tools datename 'C*.MP4' -p a6000_ --exif-date-key XML:CreationDateValue --exif-date-format "%Y:%m:%d %H:%M:%S%z"

# For Sony HandyCam
camera-tools datename '0*.MTS' -p handycam_ --exif-date-key H264:DateTimeOriginal --exif-date-format "%Y:%m:%d %H:%M:%S%z"
```

### Back up files but skip RAW files, and compress video files

Requirements: ffmpeg with NVIDIA hardware acceleration enabled.

`backup_camera_dir_compress_video.py /home/user/Picture/Canon /home/user/onedrive/Photo/Canon`



### Bulk resize images

```bash
camera-tools bulk-image-resize R6_original R6_compressed -r lanczos --watermark
```


### SRT to YouTube Chapters (and framerate conversion)

