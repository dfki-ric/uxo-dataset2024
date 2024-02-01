#!/bin/bash

# Script to cut the GoPro footage from day TWO (!) into individual clips, one per recorded trajectory.
# The timestamps are specific to day 2 and were manually extracted from the audio track, where it is
# clearly visible when the motors engaged. The first frame of the clips will be the first frame with 
# movement. Since the footage was recorded at 5.3k/60fps, this may take a long time. While it is 
# possible to do the downsampling here (see options below), a separate script exists for this as well.
# 
# $1: directory containing the day 2 footage
# $2: directory to put the extracted clips in
# 
# example: ./gopro_1_cut_day2.bash ../data_raw/gopro/day2/ ../data_processed/gopro/day2/clips_uhd/

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <path-to-day2-input-folder> <path-to-output-folder>"
    exit 1
fi

INDIR="$1"
OUTDIR="$2"

# Stream copy
#OPTIONS='-c copy'

# FullHD Downscaling
#OPTIONS='-vf scale=1920:1080 -c:v libx264 -c:a copy'

# SD Downscaling
OPTIONS='-vf scale=640:360 -c:v libx264 -an'


mkdir -p $OUTDIR

# End times are all +5s after the detected end of crane motion as sometimes there was some PTU motion that can be helpful later
ffmpeg -i "$INDIR/GX010012.mp4" -ss 06:28.010 -to 07:29.372 $OPTIONS "$OUTDIR/GX010012_01.mp4"
ffmpeg -i "$INDIR/GX010012.mp4" -ss 08:32.395 -to 09:37.385 $OPTIONS "$OUTDIR/GX010012_02.mp4"
ffmpeg -i "$INDIR/GX010012.mp4" -ss 11:18.378 -to 12:18.988 $OPTIONS "$OUTDIR/GX010012_03.mp4"
ffmpeg -i "$INDIR/GX010012.mp4" -ss 13:22.487 -to 14:25.003 $OPTIONS "$OUTDIR/GX010012_04.mp4"
ffmpeg -i "$INDIR/GX010012.mp4" -ss 15:43.338 -to 16:43.542 $OPTIONS "$OUTDIR/GX010012_05.mp4"
ffmpeg -i "$INDIR/GX010012.mp4" -ss 18:08.151 -to 19:08.308 $OPTIONS "$OUTDIR/GX010012_06.mp4"
ffmpeg -i "$INDIR/GX010012.mp4" -ss 22:07.653 -to 23:08.653 $OPTIONS "$OUTDIR/GX010012_07.mp4"
ffmpeg -i "$INDIR/GX010012.mp4" -ss 24:04.717 -to 25:05.268 $OPTIONS "$OUTDIR/GX010012_08.mp4"

ffmpeg -i "$INDIR/GX010014.mp4" -ss 02:33.868 -to 03:34.704 $OPTIONS "$OUTDIR/GX010014_01.mp4"
ffmpeg -i "$INDIR/GX010014.mp4" -ss 04:49.984 -to 05:50.650 $OPTIONS "$OUTDIR/GX010014_02.mp4"
ffmpeg -i "$INDIR/GX010014.mp4" -ss 06:56.123 -to 07:56.839 $OPTIONS "$OUTDIR/GX010014_03.mp4"
ffmpeg -i "$INDIR/GX010014.mp4" -ss 09:01.726 -to 10:02.154 $OPTIONS "$OUTDIR/GX010014_04.mp4"
ffmpeg -i "$INDIR/GX010014.mp4" -ss 11:13.980 -to 12:15.224 $OPTIONS "$OUTDIR/GX010014_05.mp4"
ffmpeg -i "$INDIR/GX010014.mp4" -ss 13:13.901 -to 14:19.363 $OPTIONS "$OUTDIR/GX010014_06.mp4"
ffmpeg -i "$INDIR/GX010014.mp4" -ss 16:51.705 -to 17:52.414 $OPTIONS "$OUTDIR/GX010014_07.mp4"
ffmpeg -i "$INDIR/GX010014.mp4" -ss 19:11.681 -to 20:13.443 $OPTIONS "$OUTDIR/GX010014_08.mp4"
ffmpeg -i "$INDIR/GX010014.mp4" -ss 23:34.628 -to 23:56.521 $OPTIONS "$OUTDIR/GX010014_09.mp4"
ffmpeg -i "$INDIR/GX010014.mp4" -ss 24:30.748 -to 25:31.671 $OPTIONS "$OUTDIR/GX010014_10.mp4"

ffmpeg -i "$INDIR/GX010015.mp4" -ss 02:10.835 -to 03:11.665 $OPTIONS "$OUTDIR/GX010015_01.mp4"
ffmpeg -i "$INDIR/GX010015.mp4" -ss 04:42.682 -to 05:42.963 $OPTIONS "$OUTDIR/GX010015_02.mp4"
ffmpeg -i "$INDIR/GX010015.mp4" -ss 07:31.234 -to 08:32.040 $OPTIONS "$OUTDIR/GX010015_03.mp4"
ffmpeg -i "$INDIR/GX010015.mp4" -ss 10:09.133 -to 11:08.573 $OPTIONS "$OUTDIR/GX010015_04.mp4"

ffmpeg -i "$INDIR/GX010018.mp4" -ss 00:35.519 -to 02:25.566 $OPTIONS "$OUTDIR/GX010018_01.mp4"
ffmpeg -i "$INDIR/GX010018.mp4" -ss 05:18.058 -to 07:08.011 $OPTIONS "$OUTDIR/GX010018_02.mp4"
ffmpeg -i "$INDIR/GX010018.mp4" -ss 09:28.521 -to 11:17.553 $OPTIONS "$OUTDIR/GX010018_03.mp4"
ffmpeg -i "$INDIR/GX010018.mp4" -ss 13:59.457 -to 14:45.972 $OPTIONS "$OUTDIR/GX010018_04.mp4"
ffmpeg -i "$INDIR/GX010018.mp4" -ss 14:45.243 -to 15:31.792 $OPTIONS "$OUTDIR/GX010018_05.mp4"
ffmpeg -i "$INDIR/GX010018.mp4" -ss 15:39.546 -to 16:26.128 $OPTIONS "$OUTDIR/GX010018_06.mp4"
ffmpeg -i "$INDIR/GX010018.mp4" -ss 16:33.414 -to 17:19.757 $OPTIONS "$OUTDIR/GX010018_07.mp4"

ffmpeg -i "$INDIR/GX020012.mp4" -ss 00:33.600 -to 01:35.119 $OPTIONS "$OUTDIR/GX020012_01.mp4"
ffmpeg -i "$INDIR/GX020012.mp4" -ss 03:03.275 -to 04:03.303 $OPTIONS "$OUTDIR/GX020012_02.mp4"
ffmpeg -i "$INDIR/GX020012.mp4" -ss 05:28.920 -to 06:29.587 $OPTIONS "$OUTDIR/GX020012_03.mp4"
ffmpeg -i "$INDIR/GX020012.mp4" -ss 08:51.828 -to 09:53.451 $OPTIONS "$OUTDIR/GX020012_04.mp4"
ffmpeg -i "$INDIR/GX020012.mp4" -ss 10:49.120 -to 11:52.595 $OPTIONS "$OUTDIR/GX020012_05.mp4"
ffmpeg -i "$INDIR/GX020012.mp4" -ss 19:11.539 -to 20:12.524 $OPTIONS "$OUTDIR/GX020012_06.mp4"
ffmpeg -i "$INDIR/GX020012.mp4" -ss 21:40.491 -to 22:39.740 $OPTIONS "$OUTDIR/GX020012_07.mp4"
ffmpeg -i "$INDIR/GX020012.mp4" -ss 22:43.702 -to 23:30.056 $OPTIONS "$OUTDIR/GX020012_08.mp4"
ffmpeg -i "$INDIR/GX020012.mp4" -ss 23:52.418 -to 24:57.703 $OPTIONS "$OUTDIR/GX020012_09.mp4"
ffmpeg -i "$INDIR/GX020012.mp4" -ss 25:02.686 -to 25:30.000 $OPTIONS "$OUTDIR/GX020012_10.mp4"

ffmpeg -i "$INDIR/GX020014.mp4" -ss 02:13.372 -to 03:13.277 $OPTIONS "$OUTDIR/GX020014_01.mp4"
ffmpeg -i "$INDIR/GX020014.mp4" -ss 04:57.612 -to 05:58.988 $OPTIONS "$OUTDIR/GX020014_02.mp4"
ffmpeg -i "$INDIR/GX020014.mp4" -ss 06:47.655 -to 07:48.360 $OPTIONS "$OUTDIR/GX020014_03.mp4"
ffmpeg -i "$INDIR/GX020014.mp4" -ss 08:38.767 -to 09:42.066 $OPTIONS "$OUTDIR/GX020014_04.mp4"
ffmpeg -i "$INDIR/GX020014.mp4" -ss 10:35.357 -to 11:36.774 $OPTIONS "$OUTDIR/GX020014_05.mp4"
ffmpeg -i "$INDIR/GX020014.mp4" -ss 12:37.955 -to 13:39.163 $OPTIONS "$OUTDIR/GX020014_06.mp4"
ffmpeg -i "$INDIR/GX020014.mp4" -ss 14:36.895 -to 15:37.418 $OPTIONS "$OUTDIR/GX020014_07.mp4"
ffmpeg -i "$INDIR/GX020014.mp4" -ss 17:31.563 -to 18:18.420 $OPTIONS "$OUTDIR/GX020014_08.mp4"
ffmpeg -i "$INDIR/GX020014.mp4" -ss 19:11.663 -to 19:57.958 $OPTIONS "$OUTDIR/GX020014_09.mp4"
ffmpeg -i "$INDIR/GX020014.mp4" -ss 20:44.070 -to 21:30.457 $OPTIONS "$OUTDIR/GX020014_10.mp4"
ffmpeg -i "$INDIR/GX020014.mp4" -ss 21:29.106 -to 22:15.379 $OPTIONS "$OUTDIR/GX020014_11.mp4"
ffmpeg -i "$INDIR/GX020014.mp4" -ss 22:33.423 -to 23:19.909 $OPTIONS "$OUTDIR/GX020014_12.mp4"
ffmpeg -i "$INDIR/GX020014.mp4" -ss 23:24.712 -to 24:11.008 $OPTIONS "$OUTDIR/GX020014_13.mp4"

ffmpeg -i "$INDIR/GX030012.mp4" -ss 04:46.327 -to 05:32.809 $OPTIONS "$OUTDIR/GX030012_01.mp4"
ffmpeg -i "$INDIR/GX030012.mp4" -ss 06:33.253 -to 07:19.451 $OPTIONS "$OUTDIR/GX030012_02.mp4"
ffmpeg -i "$INDIR/GX030012.mp4" -ss 08:17.393 -to 09:03.668 $OPTIONS "$OUTDIR/GX030012_03.mp4"
ffmpeg -i "$INDIR/GX030012.mp4" -ss 09:03.544 -to 09:49.829 $OPTIONS "$OUTDIR/GX030012_04.mp4"
ffmpeg -i "$INDIR/GX030012.mp4" -ss 09:55.838 -to 10:41.959 $OPTIONS "$OUTDIR/GX030012_05.mp4"

ffmpeg -i "$INDIR/GX030014.mp4" -ss 00:06.191 -to 01:07.442 $OPTIONS "$OUTDIR/GX030014_01.mp4"
ffmpeg -i "$INDIR/GX030014.mp4" -ss 03:43.224 -to 04:44.523 $OPTIONS "$OUTDIR/GX030014_02.mp4"
