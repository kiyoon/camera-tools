# Change file names to date taken

## Requirements

### Ubuntu

`sudo apt install libimage-exiftool-perl`

## Usage

`datename.py *.JPG`

or

`datename.py *.MP4`

It will rename the image or video files into the EXIF datetime, whilst creating undo script and json files containing EXIF information.

## Settings Per Camera
This section describes the "full" option for each camera. Default settings are optimised for Canon M50.
### Canon M50

Default settings are optimised for Canon M50.

Below is the recommended options for M50. Prefix, undo, save-exif, and rename-cr3 (compressed RAW) are optional.

`datename.py --prefix M50_ --date EXIF --exif-date Composite:SubSecCreateDate --undo --save-exif --rename-cr3 *.JPG`

### Sony HandyCam

Recommended options for Sony HandyCam is:

`datename.py --prefix SonyCam_ --date EXIF --exif-date H264:DateTimeOriginal --undo --save-exif --no-rename-cr3 *.MTS`

Prefix, undo and save-exif are optional.

# Back up files but skip RAW files, and compress video files

## Requirements

`pip3 install coloredlogs verboselogs`

ffmpeg with NVIDIA hardware acceleration enabled.

## Usage

`backup_camera_dir_compress_video.py /home/user/Picture/Canon /home/user/onedrive/Photo/Canon`



# Bulk resize images

## Requirements

`pip3 install coloredlogs verboselogs pillow piexif`


## Usage

`bulk_image_resize.py /home/user/Picture/Canon /home/user/Picture/Canon_resized`


# SRT framerate conversion

## Requirements

`pip3 install srt coloredlogs verboselogs`
