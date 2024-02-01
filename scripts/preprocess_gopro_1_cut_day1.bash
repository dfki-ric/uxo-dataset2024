#!/bin/bash

# Script to cut the GoPro footage from day ONE (!) into individual clips, one per recorded trajectory.
# The timestamps are specific to day 1 and were manually extracted from the audio track, where it is
# clearly visible when the motors engaged. The first frame of the clips will be the first frame with 
# movement. Since the footage was recorded at 5.3k/60fps, this may take a long time. While it is 
# possible to do the downsampling here (see options below), a separate script exists for this as well.
# 
# $1: directory containing the day 1 footage
# $2: directory to put the extracted clips in
# 
# example: ./preprocess_gopro_1_cut_day1.bash ../data_raw/gopro/day1/ ../data_processed/gopro/day1/clips_uhd/

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <path-to-day1-input-folder> <path-to-output-folder>"
    exit 1
fi

INDIR="$1"
OUTDIR="$2"

# Stream copy
OPTIONS='-c copy'

# FullHD Downscaling
#OPTIONS='-vf scale=1920:1080 -c:v libx264 -c:a copy'

# SD Downscaling
#OPTIONS='-vf scale=640:360 -c:v libx264 -an'


mkdir -p $OUTDIR

# End times are all +5s after the detected end of crane motion as sometimes there was some PTU motion that can be helpful later
ffmpeg -i "$INDIR/GX010010.mp4" -ss 03:37.940 -to 04:38.973 $OPTIONS "$OUTDIR/GX010010_01.mp4"
ffmpeg -i "$INDIR/GX010010.mp4" -ss 17:18.361 -to 18:19.155 $OPTIONS "$OUTDIR/GX010010_02.mp4"
ffmpeg -i "$INDIR/GX010010.mp4" -ss 20:59.888 -to 22:01.393 $OPTIONS "$OUTDIR/GX010010_03.mp4"

ffmpeg -i "$INDIR/GX020009.mp4" -ss 23:20.701 -to 24:21.219 $OPTIONS "$OUTDIR/GX020009_01.mp4"

ffmpeg -i "$INDIR/GX020010.mp4" -ss 02:42.391 -to 03:49.723 $OPTIONS "$OUTDIR/GX020010_01.mp4"
ffmpeg -i "$INDIR/GX020010.mp4" -ss 08:29.283 -to 09:30.501 $OPTIONS "$OUTDIR/GX020010_02.mp4"
ffmpeg -i "$INDIR/GX020010.mp4" -ss 11:05.799 -to 12:07.403 $OPTIONS "$OUTDIR/GX020010_03.mp4"
ffmpeg -i "$INDIR/GX020010.mp4" -ss 13:36.832 -to 14:37.694 $OPTIONS "$OUTDIR/GX020010_04.mp4"
ffmpeg -i "$INDIR/GX020010.mp4" -ss 16:26.659 -to 17:29.385 $OPTIONS "$OUTDIR/GX020010_05.mp4"
ffmpeg -i "$INDIR/GX020010.mp4" -ss 21:31.792 -to 22:32.479 $OPTIONS "$OUTDIR/GX020010_06.mp4"
ffmpeg -i "$INDIR/GX020010.mp4" -ss 23:28.126 -to 24:29.060 $OPTIONS "$OUTDIR/GX020010_07.mp4"

ffmpeg -i "$INDIR/GX030010.mp4" -ss 02:13.303 -to 03:16.841 $OPTIONS "$OUTDIR/GX030010_01.mp4"
ffmpeg -i "$INDIR/GX030010.mp4" -ss 05:54.680 -to 06:56.330 $OPTIONS "$OUTDIR/GX030010_02.mp4"
ffmpeg -i "$INDIR/GX030010.mp4" -ss 08:10.290 -to 09:11.783 $OPTIONS "$OUTDIR/GX030010_03.mp4"
ffmpeg -i "$INDIR/GX030010.mp4" -ss 10:31.326 -to 11:31.907 $OPTIONS "$OUTDIR/GX030010_04.mp4"
ffmpeg -i "$INDIR/GX030010.mp4" -ss 12:26.378 -to 13:28.239 $OPTIONS "$OUTDIR/GX030010_05.mp4"
ffmpeg -i "$INDIR/GX030010.mp4" -ss 24:02.970 -to 24:49.200 $OPTIONS "$OUTDIR/GX030010_06.mp4"
