#!/bin/bash

# Script to cut the GoPro footage into individual clips, one per recorded trajectory.
# 
# The timestamps are specific to each clip and were manually extracted from the audio track, where it 
# is clearly visible when the motors engaged. The first frame of the clips will be the first frame 
# with movement. Since the footage was recorded at 5.3k/60fps, this may take a long time. While it is 
# possible to do the downsampling here (see options below), a separate script exists for this as well.
# 
# If you're planning to match the data yourself, extending the clips by 3-5s beyond the detected range
# can be helpful as some PTU motion may have been captured before the crane started moving. For the 
# final export we recut the clips to the correct range to make the dataset as tight as possible.
# 
# $1: resolution, one of uhd, fhd or sd
# $2: directory containing the footage
# $3: directory to put the extracted clips in
# 
# example: ./gopro_1_cut.bash uhd ../data_raw/gopro/ ../data_processed/gopro/

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <resolution> <path-to-input-folder> <path-to-output-folder>"
    exit 1
fi

# Downscaling is more efficient on the cut clips (see next script)
case "$1" in
"uhd")
    OPTIONS='-c copy -an'
    ;;
"fhd")
    OPTIONS='-vf scale=1920:1080 -c:v libx264 -an'
    ;;
"sd")
    OPTIONS='-vf scale=640:360 -c:v libx264 -an'
    ;;
*)
    echo "resolution '$1' not recognized, must be one of 'uhd', 'fhd', 'sd'"
    exit 1
esac

INDIR="$2"
OUTDIR="$3/clips_$1"

mkdir -p $OUTDIR

ffmpeg -i "$INDIR/20230920_GX010010.mp4" -ss 03:37.940 -to 04:33.973 $OPTIONS "$OUTDIR/20230920_GX010010_01.mp4"
ffmpeg -i "$INDIR/20230920_GX010010.mp4" -ss 17:18.361 -to 18:14.155 $OPTIONS "$OUTDIR/20230920_GX010010_02.mp4"
ffmpeg -i "$INDIR/20230920_GX010010.mp4" -ss 20:59.888 -to 21:56.393 $OPTIONS "$OUTDIR/20230920_GX010010_03.mp4"
ffmpeg -i "$INDIR/20230920_GX020009.mp4" -ss 23:20.701 -to 24:16.219 $OPTIONS "$OUTDIR/20230920_GX020009_01.mp4"
ffmpeg -i "$INDIR/20230920_GX020010.mp4" -ss 02:42.391 -to 03:44.723 $OPTIONS "$OUTDIR/20230920_GX020010_01.mp4"
ffmpeg -i "$INDIR/20230920_GX020010.mp4" -ss 08:29.283 -to 09:25.501 $OPTIONS "$OUTDIR/20230920_GX020010_02.mp4"
ffmpeg -i "$INDIR/20230920_GX020010.mp4" -ss 11:05.799 -to 12:02.403 $OPTIONS "$OUTDIR/20230920_GX020010_03.mp4"
ffmpeg -i "$INDIR/20230920_GX020010.mp4" -ss 13:36.832 -to 14:32.694 $OPTIONS "$OUTDIR/20230920_GX020010_04.mp4"
ffmpeg -i "$INDIR/20230920_GX020010.mp4" -ss 16:26.659 -to 17:24.385 $OPTIONS "$OUTDIR/20230920_GX020010_05.mp4"
ffmpeg -i "$INDIR/20230920_GX020010.mp4" -ss 21:31.792 -to 22:27.479 $OPTIONS "$OUTDIR/20230920_GX020010_06.mp4"
ffmpeg -i "$INDIR/20230920_GX020010.mp4" -ss 23:28.126 -to 24:24.060 $OPTIONS "$OUTDIR/20230920_GX020010_07.mp4"
ffmpeg -i "$INDIR/20230920_GX030010.mp4" -ss 02:13.303 -to 03:11.841 $OPTIONS "$OUTDIR/20230920_GX030010_01.mp4"
ffmpeg -i "$INDIR/20230920_GX030010.mp4" -ss 05:54.680 -to 06:51.330 $OPTIONS "$OUTDIR/20230920_GX030010_02.mp4"
ffmpeg -i "$INDIR/20230920_GX030010.mp4" -ss 08:10.290 -to 09:06.783 $OPTIONS "$OUTDIR/20230920_GX030010_03.mp4"
ffmpeg -i "$INDIR/20230920_GX030010.mp4" -ss 10:31.326 -to 11:26.907 $OPTIONS "$OUTDIR/20230920_GX030010_04.mp4"
ffmpeg -i "$INDIR/20230920_GX030010.mp4" -ss 12:26.378 -to 13:23.239 $OPTIONS "$OUTDIR/20230920_GX030010_05.mp4"
ffmpeg -i "$INDIR/20230920_GX030010.mp4" -ss 24:02.970 -to 24:44.200 $OPTIONS "$OUTDIR/20230920_GX030010_06.mp4"

ffmpeg -i "$INDIR/20230921_GX010012.mp4" -ss 06:28.010 -to 07:24.372 $OPTIONS "$OUTDIR/20230921_GX010012_01.mp4"
ffmpeg -i "$INDIR/20230921_GX010012.mp4" -ss 08:32.395 -to 09:32.385 $OPTIONS "$OUTDIR/20230921_GX010012_02.mp4"
ffmpeg -i "$INDIR/20230921_GX010012.mp4" -ss 11:18.378 -to 12:13.988 $OPTIONS "$OUTDIR/20230921_GX010012_03.mp4"
ffmpeg -i "$INDIR/20230921_GX010012.mp4" -ss 13:22.487 -to 14:20.003 $OPTIONS "$OUTDIR/20230921_GX010012_04.mp4"
ffmpeg -i "$INDIR/20230921_GX010012.mp4" -ss 15:43.338 -to 16:38.542 $OPTIONS "$OUTDIR/20230921_GX010012_05.mp4"
ffmpeg -i "$INDIR/20230921_GX010012.mp4" -ss 18:08.151 -to 19:03.308 $OPTIONS "$OUTDIR/20230921_GX010012_06.mp4"
ffmpeg -i "$INDIR/20230921_GX010012.mp4" -ss 22:07.653 -to 23:03.653 $OPTIONS "$OUTDIR/20230921_GX010012_07.mp4"
ffmpeg -i "$INDIR/20230921_GX010012.mp4" -ss 24:04.717 -to 25:00.268 $OPTIONS "$OUTDIR/20230921_GX010012_08.mp4"
ffmpeg -i "$INDIR/20230921_GX010014.mp4" -ss 02:33.868 -to 03:29.704 $OPTIONS "$OUTDIR/20230921_GX010014_01.mp4"
ffmpeg -i "$INDIR/20230921_GX010014.mp4" -ss 04:49.984 -to 05:45.650 $OPTIONS "$OUTDIR/20230921_GX010014_02.mp4"
ffmpeg -i "$INDIR/20230921_GX010014.mp4" -ss 06:56.123 -to 07:51.839 $OPTIONS "$OUTDIR/20230921_GX010014_03.mp4"
ffmpeg -i "$INDIR/20230921_GX010014.mp4" -ss 09:01.726 -to 09:57.154 $OPTIONS "$OUTDIR/20230921_GX010014_04.mp4"
ffmpeg -i "$INDIR/20230921_GX010014.mp4" -ss 11:13.980 -to 12:10.224 $OPTIONS "$OUTDIR/20230921_GX010014_05.mp4"
ffmpeg -i "$INDIR/20230921_GX010014.mp4" -ss 13:13.901 -to 14:14.363 $OPTIONS "$OUTDIR/20230921_GX010014_06.mp4"
ffmpeg -i "$INDIR/20230921_GX010014.mp4" -ss 16:51.705 -to 17:47.414 $OPTIONS "$OUTDIR/20230921_GX010014_07.mp4"
ffmpeg -i "$INDIR/20230921_GX010014.mp4" -ss 19:11.681 -to 20:08.443 $OPTIONS "$OUTDIR/20230921_GX010014_08.mp4"
ffmpeg -i "$INDIR/20230921_GX010014.mp4" -ss 23:34.628 -to 23:51.521 $OPTIONS "$OUTDIR/20230921_GX010014_09.mp4"
ffmpeg -i "$INDIR/20230921_GX010014.mp4" -ss 24:30.748 -to 25:26.671 $OPTIONS "$OUTDIR/20230921_GX010014_10.mp4"
ffmpeg -i "$INDIR/20230921_GX010015.mp4" -ss 02:10.835 -to 03:06.665 $OPTIONS "$OUTDIR/20230921_GX010015_01.mp4"
ffmpeg -i "$INDIR/20230921_GX010015.mp4" -ss 04:42.682 -to 05:37.963 $OPTIONS "$OUTDIR/20230921_GX010015_02.mp4"
ffmpeg -i "$INDIR/20230921_GX010015.mp4" -ss 07:31.234 -to 08:27.040 $OPTIONS "$OUTDIR/20230921_GX010015_03.mp4"
ffmpeg -i "$INDIR/20230921_GX010015.mp4" -ss 10:09.133 -to 11:03.573 $OPTIONS "$OUTDIR/20230921_GX010015_04.mp4"
ffmpeg -i "$INDIR/20230921_GX010018.mp4" -ss 00:35.519 -to 02:20.566 $OPTIONS "$OUTDIR/20230921_GX010018_01.mp4"
ffmpeg -i "$INDIR/20230921_GX010018.mp4" -ss 05:18.058 -to 07:03.011 $OPTIONS "$OUTDIR/20230921_GX010018_02.mp4"
ffmpeg -i "$INDIR/20230921_GX010018.mp4" -ss 09:28.521 -to 11:12.553 $OPTIONS "$OUTDIR/20230921_GX010018_03.mp4"
ffmpeg -i "$INDIR/20230921_GX010018.mp4" -ss 13:59.457 -to 14:40.972 $OPTIONS "$OUTDIR/20230921_GX010018_04.mp4"
ffmpeg -i "$INDIR/20230921_GX010018.mp4" -ss 14:45.243 -to 15:26.792 $OPTIONS "$OUTDIR/20230921_GX010018_05.mp4"
ffmpeg -i "$INDIR/20230921_GX010018.mp4" -ss 15:39.546 -to 16:21.128 $OPTIONS "$OUTDIR/20230921_GX010018_06.mp4"
ffmpeg -i "$INDIR/20230921_GX010018.mp4" -ss 16:33.414 -to 17:14.757 $OPTIONS "$OUTDIR/20230921_GX010018_07.mp4"
ffmpeg -i "$INDIR/20230921_GX020012.mp4" -ss 00:33.600 -to 01:30.119 $OPTIONS "$OUTDIR/20230921_GX020012_01.mp4"
ffmpeg -i "$INDIR/20230921_GX020012.mp4" -ss 03:03.275 -to 03:58.303 $OPTIONS "$OUTDIR/20230921_GX020012_02.mp4"
ffmpeg -i "$INDIR/20230921_GX020012.mp4" -ss 05:28.920 -to 06:24.587 $OPTIONS "$OUTDIR/20230921_GX020012_03.mp4"
ffmpeg -i "$INDIR/20230921_GX020012.mp4" -ss 08:51.828 -to 09:48.451 $OPTIONS "$OUTDIR/20230921_GX020012_04.mp4"
ffmpeg -i "$INDIR/20230921_GX020012.mp4" -ss 10:49.120 -to 11:47.595 $OPTIONS "$OUTDIR/20230921_GX020012_05.mp4"
ffmpeg -i "$INDIR/20230921_GX020012.mp4" -ss 19:11.539 -to 20:07.524 $OPTIONS "$OUTDIR/20230921_GX020012_06.mp4"
ffmpeg -i "$INDIR/20230921_GX020012.mp4" -ss 21:40.491 -to 22:34.740 $OPTIONS "$OUTDIR/20230921_GX020012_07.mp4"
ffmpeg -i "$INDIR/20230921_GX020012.mp4" -ss 22:43.702 -to 23:25.056 $OPTIONS "$OUTDIR/20230921_GX020012_08.mp4"
ffmpeg -i "$INDIR/20230921_GX020012.mp4" -ss 23:52.418 -to 24:52.703 $OPTIONS "$OUTDIR/20230921_GX020012_09.mp4"
ffmpeg -i "$INDIR/20230921_GX020012.mp4" -ss 25:02.686 -to 25:25.000 $OPTIONS "$OUTDIR/20230921_GX020012_10.mp4"
ffmpeg -i "$INDIR/20230921_GX020014.mp4" -ss 02:13.372 -to 03:08.277 $OPTIONS "$OUTDIR/20230921_GX020014_01.mp4"
ffmpeg -i "$INDIR/20230921_GX020014.mp4" -ss 04:57.612 -to 05:53.988 $OPTIONS "$OUTDIR/20230921_GX020014_02.mp4"
ffmpeg -i "$INDIR/20230921_GX020014.mp4" -ss 06:47.655 -to 07:43.360 $OPTIONS "$OUTDIR/20230921_GX020014_03.mp4"
ffmpeg -i "$INDIR/20230921_GX020014.mp4" -ss 08:38.767 -to 09:37.066 $OPTIONS "$OUTDIR/20230921_GX020014_04.mp4"
ffmpeg -i "$INDIR/20230921_GX020014.mp4" -ss 10:35.357 -to 11:31.774 $OPTIONS "$OUTDIR/20230921_GX020014_05.mp4"
ffmpeg -i "$INDIR/20230921_GX020014.mp4" -ss 12:37.955 -to 13:34.163 $OPTIONS "$OUTDIR/20230921_GX020014_06.mp4"
ffmpeg -i "$INDIR/20230921_GX020014.mp4" -ss 14:36.895 -to 15:32.418 $OPTIONS "$OUTDIR/20230921_GX020014_07.mp4"
ffmpeg -i "$INDIR/20230921_GX020014.mp4" -ss 17:31.563 -to 18:13.420 $OPTIONS "$OUTDIR/20230921_GX020014_08.mp4"
ffmpeg -i "$INDIR/20230921_GX020014.mp4" -ss 19:11.663 -to 19:52.958 $OPTIONS "$OUTDIR/20230921_GX020014_09.mp4"
ffmpeg -i "$INDIR/20230921_GX020014.mp4" -ss 20:44.070 -to 21:25.457 $OPTIONS "$OUTDIR/20230921_GX020014_10.mp4"
ffmpeg -i "$INDIR/20230921_GX020014.mp4" -ss 21:29.106 -to 22:10.379 $OPTIONS "$OUTDIR/20230921_GX020014_11.mp4"
ffmpeg -i "$INDIR/20230921_GX020014.mp4" -ss 22:33.423 -to 23:14.909 $OPTIONS "$OUTDIR/20230921_GX020014_12.mp4"
ffmpeg -i "$INDIR/20230921_GX020014.mp4" -ss 23:24.712 -to 24:06.008 $OPTIONS "$OUTDIR/20230921_GX020014_13.mp4"
ffmpeg -i "$INDIR/20230921_GX030012.mp4" -ss 04:46.327 -to 05:27.809 $OPTIONS "$OUTDIR/20230921_GX030012_01.mp4"
ffmpeg -i "$INDIR/20230921_GX030012.mp4" -ss 06:33.253 -to 07:14.451 $OPTIONS "$OUTDIR/20230921_GX030012_02.mp4"
ffmpeg -i "$INDIR/20230921_GX030012.mp4" -ss 08:17.393 -to 08:58.668 $OPTIONS "$OUTDIR/20230921_GX030012_03.mp4"
ffmpeg -i "$INDIR/20230921_GX030012.mp4" -ss 09:03.544 -to 09:44.829 $OPTIONS "$OUTDIR/20230921_GX030012_04.mp4"
ffmpeg -i "$INDIR/20230921_GX030012.mp4" -ss 09:55.838 -to 10:36.959 $OPTIONS "$OUTDIR/20230921_GX030012_05.mp4"
ffmpeg -i "$INDIR/20230921_GX030014.mp4" -ss 00:06.191 -to 01:02.442 $OPTIONS "$OUTDIR/20230921_GX030014_01.mp4"
ffmpeg -i "$INDIR/20230921_GX030014.mp4" -ss 03:43.224 -to 04:39.523 $OPTIONS "$OUTDIR/20230921_GX030014_02.mp4"
