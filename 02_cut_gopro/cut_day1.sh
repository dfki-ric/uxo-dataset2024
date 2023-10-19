#!/bin/bash

# Erster Frame ist erster Frame mit Bewegung.
# Video stoppt sofort, wenn die Achse steht.

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path-to-output-folder>"
    exit 1
fi

INDIR="../../GoPro_2023_09_20"
OUTDIR="$1"

# Stream copy
#OPTIONS='-c copy'

# FullHD Downscaling
#OPTIONS='-vf scale=1920:1080 -c:v libx264 -c:a copy'

# SD Downscaling
OPTIONS='-vf scale=640:360 -c:v libx264 -an'


mkdir -p $OUTDIR

ffmpeg -ss 03:37.000 -i "$INDIR/GX010010.MP4" -ss 03:37.940 -to 04:33.973 $OPTIONS "$OUTDIR/GX010010_01.mp4"
ffmpeg -ss 17:18.000 -i "$INDIR/GX010010.MP4" -ss 17:18.361 -to 18:14.155 $OPTIONS "$OUTDIR/GX010010_02.mp4"
ffmpeg -ss 20:59.000 -i "$INDIR/GX010010.MP4" -ss 20:59.888 -to 21:56.393 $OPTIONS "$OUTDIR/GX010010_03.mp4"

ffmpeg -ss 23:20.000 -i "$INDIR/GX020009.MP4" -ss 23:20.701 -to 24:16.219 $OPTIONS "$OUTDIR/GX020009_01.mp4"

ffmpeg -ss 02:42.000 -i "$INDIR/GX020010.MP4" -ss 02:42.391 -to 03:44.723 $OPTIONS "$OUTDIR/GX020010_01.mp4"
ffmpeg -ss 08:29.000 -i "$INDIR/GX020010.MP4" -ss 08:29.283 -to 09:25.501 $OPTIONS "$OUTDIR/GX020010_02.mp4"
ffmpeg -ss 11:05.000 -i "$INDIR/GX020010.MP4" -ss 11:05.799 -to 12:02.403 $OPTIONS "$OUTDIR/GX020010_03.mp4"
ffmpeg -ss 13:36.000 -i "$INDIR/GX020010.MP4" -ss 13:36.832 -to 14:32.694 $OPTIONS "$OUTDIR/GX020010_04.mp4"
ffmpeg -ss 16:26.000 -i "$INDIR/GX020010.MP4" -ss 16:26.659 -to 17:24.385 $OPTIONS "$OUTDIR/GX020010_05.mp4"
ffmpeg -ss 21:31.000 -i "$INDIR/GX020010.MP4" -ss 21:31.792 -to 22:27.479 $OPTIONS "$OUTDIR/GX020010_06.mp4"
ffmpeg -ss 23:28.000 -i "$INDIR/GX020010.MP4" -ss 23:28.126 -to 24:24.060 $OPTIONS "$OUTDIR/GX020010_07.mp4"

ffmpeg -ss 02:13.000 -i "$INDIR/GX030010.MP4" -ss 02:13.303 -to 03:11.841 $OPTIONS "$OUTDIR/GX030010_01.mp4"
ffmpeg -ss 05:54.000 -i "$INDIR/GX030010.MP4" -ss 05:54.680 -to 06:51.330 $OPTIONS "$OUTDIR/GX030010_02.mp4"
ffmpeg -ss 08:10.000 -i "$INDIR/GX030010.MP4" -ss 08:10.290 -to 09:06.783 $OPTIONS "$OUTDIR/GX030010_03.mp4"
ffmpeg -ss 10:31.000 -i "$INDIR/GX030010.MP4" -ss 10:31.326 -to 11:26.907 $OPTIONS "$OUTDIR/GX030010_04.mp4"
ffmpeg -ss 12:26.000 -i "$INDIR/GX030010.MP4" -ss 12:26.378 -to 13:23.239 $OPTIONS "$OUTDIR/GX030010_05.mp4"
ffmpeg -ss 24:02.000 -i "$INDIR/GX030010.MP4" -ss 24:02.970 -to 24:44.200 $OPTIONS "$OUTDIR/GX030010_06.mp4"
