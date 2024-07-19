#!/bin/bash

# Script to cut the GoPro footage into individual clips, one per recorded trajectory.
# 
# The timestamps are specific to each clip and were manually extracted from the audio track, where it 
# is clearly visible when the motors engaged. The first frame of the clips will be the first frame 
# with movement. Since the footage was recorded at 5.3k/60fps, this may take a long time. While it is 
# possible to do the downsampling here, it is more efficiently done separately (see next script).
# 
# If you're planning to match the data yourself, extending the clips by 3-5s beyond the detected range
# can be helpful as some PTU motion may have been captured before the crane started moving. For the 
# final export we recut the clips to the correct range to make the dataset as tight as possible.
# 
# As with the python scripts, this script reads the config.yaml file and uses the options therein.

mydir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
indir=$(sed -n -e 's/^gopro_input://p' "$mydir/config.yaml" | tr -d '"' | xargs)/uhd
outdir=$(sed -n -e 's/^gopro_extract://p' "$mydir/config.yaml" | tr -d '"' | xargs)/clips_uhd

# Downscaling is more efficient on the cut clips (see next script)
options='-c copy -an'

mkdir -p $outdir
trap "exit" INT

ffmpeg -i "$indir/20230920_GX010010.mp4" -ss 03:37.940 -to 04:33.973 $options "$outdir/20230920_GX010010_01.mp4"
ffmpeg -i "$indir/20230920_GX010010.mp4" -ss 17:18.361 -to 18:14.155 $options "$outdir/20230920_GX010010_02.mp4"
ffmpeg -i "$indir/20230920_GX010010.mp4" -ss 20:59.888 -to 21:56.393 $options "$outdir/20230920_GX010010_03.mp4"
ffmpeg -i "$indir/20230920_GX020009.mp4" -ss 23:20.701 -to 24:16.219 $options "$outdir/20230920_GX020009_01.mp4"
ffmpeg -i "$indir/20230920_GX020010.mp4" -ss 02:42.391 -to 03:44.723 $options "$outdir/20230920_GX020010_01.mp4"
ffmpeg -i "$indir/20230920_GX020010.mp4" -ss 08:29.283 -to 09:25.501 $options "$outdir/20230920_GX020010_02.mp4"
ffmpeg -i "$indir/20230920_GX020010.mp4" -ss 11:05.799 -to 12:02.403 $options "$outdir/20230920_GX020010_03.mp4"
ffmpeg -i "$indir/20230920_GX020010.mp4" -ss 13:36.832 -to 14:32.694 $options "$outdir/20230920_GX020010_04.mp4"
ffmpeg -i "$indir/20230920_GX020010.mp4" -ss 16:26.659 -to 17:24.385 $options "$outdir/20230920_GX020010_05.mp4"
ffmpeg -i "$indir/20230920_GX020010.mp4" -ss 21:31.792 -to 22:27.479 $options "$outdir/20230920_GX020010_06.mp4"
ffmpeg -i "$indir/20230920_GX020010.mp4" -ss 23:28.126 -to 24:24.060 $options "$outdir/20230920_GX020010_07.mp4"
ffmpeg -i "$indir/20230920_GX030010.mp4" -ss 02:13.303 -to 03:11.841 $options "$outdir/20230920_GX030010_01.mp4"
ffmpeg -i "$indir/20230920_GX030010.mp4" -ss 05:54.680 -to 06:51.330 $options "$outdir/20230920_GX030010_02.mp4"
ffmpeg -i "$indir/20230920_GX030010.mp4" -ss 08:10.290 -to 09:06.783 $options "$outdir/20230920_GX030010_03.mp4"
ffmpeg -i "$indir/20230920_GX030010.mp4" -ss 10:31.326 -to 11:26.907 $options "$outdir/20230920_GX030010_04.mp4"
ffmpeg -i "$indir/20230920_GX030010.mp4" -ss 12:26.378 -to 13:23.239 $options "$outdir/20230920_GX030010_05.mp4"
ffmpeg -i "$indir/20230920_GX030010.mp4" -ss 24:02.970 -to 24:44.200 $options "$outdir/20230920_GX030010_06.mp4"

ffmpeg -i "$indir/20230921_GX010012.mp4" -ss 06:28.010 -to 07:24.372 $options "$outdir/20230921_GX010012_01.mp4"
ffmpeg -i "$indir/20230921_GX010012.mp4" -ss 08:32.395 -to 09:32.385 $options "$outdir/20230921_GX010012_02.mp4"
ffmpeg -i "$indir/20230921_GX010012.mp4" -ss 11:18.378 -to 12:13.988 $options "$outdir/20230921_GX010012_03.mp4"
ffmpeg -i "$indir/20230921_GX010012.mp4" -ss 13:22.487 -to 14:20.003 $options "$outdir/20230921_GX010012_04.mp4"
ffmpeg -i "$indir/20230921_GX010012.mp4" -ss 15:43.338 -to 16:38.542 $options "$outdir/20230921_GX010012_05.mp4"
ffmpeg -i "$indir/20230921_GX010012.mp4" -ss 18:08.151 -to 19:03.308 $options "$outdir/20230921_GX010012_06.mp4"
ffmpeg -i "$indir/20230921_GX010012.mp4" -ss 22:07.653 -to 23:03.653 $options "$outdir/20230921_GX010012_07.mp4"
ffmpeg -i "$indir/20230921_GX010012.mp4" -ss 24:04.717 -to 25:00.268 $options "$outdir/20230921_GX010012_08.mp4"
ffmpeg -i "$indir/20230921_GX010014.mp4" -ss 02:33.868 -to 03:29.704 $options "$outdir/20230921_GX010014_01.mp4"
ffmpeg -i "$indir/20230921_GX010014.mp4" -ss 04:49.984 -to 05:45.650 $options "$outdir/20230921_GX010014_02.mp4"
ffmpeg -i "$indir/20230921_GX010014.mp4" -ss 06:56.123 -to 07:51.839 $options "$outdir/20230921_GX010014_03.mp4"
ffmpeg -i "$indir/20230921_GX010014.mp4" -ss 09:01.726 -to 09:57.154 $options "$outdir/20230921_GX010014_04.mp4"
ffmpeg -i "$indir/20230921_GX010014.mp4" -ss 11:13.980 -to 12:10.224 $options "$outdir/20230921_GX010014_05.mp4"
ffmpeg -i "$indir/20230921_GX010014.mp4" -ss 13:13.901 -to 14:14.363 $options "$outdir/20230921_GX010014_06.mp4"
ffmpeg -i "$indir/20230921_GX010014.mp4" -ss 16:51.705 -to 17:47.414 $options "$outdir/20230921_GX010014_07.mp4"
ffmpeg -i "$indir/20230921_GX010014.mp4" -ss 19:11.681 -to 20:08.443 $options "$outdir/20230921_GX010014_08.mp4"
ffmpeg -i "$indir/20230921_GX010014.mp4" -ss 23:34.628 -to 23:51.521 $options "$outdir/20230921_GX010014_09.mp4"
ffmpeg -i "$indir/20230921_GX010014.mp4" -ss 24:30.748 -to 25:26.671 $options "$outdir/20230921_GX010014_10.mp4"
ffmpeg -i "$indir/20230921_GX010015.mp4" -ss 02:10.835 -to 03:06.665 $options "$outdir/20230921_GX010015_01.mp4"
ffmpeg -i "$indir/20230921_GX010015.mp4" -ss 04:42.682 -to 05:37.963 $options "$outdir/20230921_GX010015_02.mp4"
ffmpeg -i "$indir/20230921_GX010015.mp4" -ss 07:31.234 -to 08:27.040 $options "$outdir/20230921_GX010015_03.mp4"
ffmpeg -i "$indir/20230921_GX010015.mp4" -ss 10:09.133 -to 11:03.573 $options "$outdir/20230921_GX010015_04.mp4"
ffmpeg -i "$indir/20230921_GX010018.mp4" -ss 00:35.519 -to 02:20.566 $options "$outdir/20230921_GX010018_01.mp4"
ffmpeg -i "$indir/20230921_GX010018.mp4" -ss 05:18.058 -to 07:03.011 $options "$outdir/20230921_GX010018_02.mp4"
ffmpeg -i "$indir/20230921_GX010018.mp4" -ss 09:28.521 -to 11:12.553 $options "$outdir/20230921_GX010018_03.mp4"
ffmpeg -i "$indir/20230921_GX010018.mp4" -ss 13:59.457 -to 14:40.972 $options "$outdir/20230921_GX010018_04.mp4"
ffmpeg -i "$indir/20230921_GX010018.mp4" -ss 14:45.243 -to 15:26.792 $options "$outdir/20230921_GX010018_05.mp4"
ffmpeg -i "$indir/20230921_GX010018.mp4" -ss 15:39.546 -to 16:21.128 $options "$outdir/20230921_GX010018_06.mp4"
ffmpeg -i "$indir/20230921_GX010018.mp4" -ss 16:33.414 -to 17:14.757 $options "$outdir/20230921_GX010018_07.mp4"
ffmpeg -i "$indir/20230921_GX020012.mp4" -ss 00:33.600 -to 01:30.119 $options "$outdir/20230921_GX020012_01.mp4"
ffmpeg -i "$indir/20230921_GX020012.mp4" -ss 03:03.275 -to 03:58.303 $options "$outdir/20230921_GX020012_02.mp4"
ffmpeg -i "$indir/20230921_GX020012.mp4" -ss 05:28.920 -to 06:24.587 $options "$outdir/20230921_GX020012_03.mp4"
ffmpeg -i "$indir/20230921_GX020012.mp4" -ss 08:51.828 -to 09:48.451 $options "$outdir/20230921_GX020012_04.mp4"
ffmpeg -i "$indir/20230921_GX020012.mp4" -ss 10:49.120 -to 11:47.595 $options "$outdir/20230921_GX020012_05.mp4"
ffmpeg -i "$indir/20230921_GX020012.mp4" -ss 19:11.539 -to 20:07.524 $options "$outdir/20230921_GX020012_06.mp4"
ffmpeg -i "$indir/20230921_GX020012.mp4" -ss 21:40.491 -to 22:34.740 $options "$outdir/20230921_GX020012_07.mp4"
ffmpeg -i "$indir/20230921_GX020012.mp4" -ss 22:43.702 -to 23:25.056 $options "$outdir/20230921_GX020012_08.mp4"
ffmpeg -i "$indir/20230921_GX020012.mp4" -ss 23:52.418 -to 24:52.703 $options "$outdir/20230921_GX020012_09.mp4"
ffmpeg -i "$indir/20230921_GX020012.mp4" -ss 25:02.686 -to 25:25.000 $options "$outdir/20230921_GX020012_10.mp4"
ffmpeg -i "$indir/20230921_GX020014.mp4" -ss 02:13.372 -to 03:08.277 $options "$outdir/20230921_GX020014_01.mp4"
ffmpeg -i "$indir/20230921_GX020014.mp4" -ss 04:57.612 -to 05:53.988 $options "$outdir/20230921_GX020014_02.mp4"
ffmpeg -i "$indir/20230921_GX020014.mp4" -ss 06:47.655 -to 07:43.360 $options "$outdir/20230921_GX020014_03.mp4"
ffmpeg -i "$indir/20230921_GX020014.mp4" -ss 08:38.767 -to 09:37.066 $options "$outdir/20230921_GX020014_04.mp4"
ffmpeg -i "$indir/20230921_GX020014.mp4" -ss 10:35.357 -to 11:31.774 $options "$outdir/20230921_GX020014_05.mp4"
ffmpeg -i "$indir/20230921_GX020014.mp4" -ss 12:37.955 -to 13:34.163 $options "$outdir/20230921_GX020014_06.mp4"
ffmpeg -i "$indir/20230921_GX020014.mp4" -ss 14:36.895 -to 15:32.418 $options "$outdir/20230921_GX020014_07.mp4"
ffmpeg -i "$indir/20230921_GX020014.mp4" -ss 17:31.563 -to 18:13.420 $options "$outdir/20230921_GX020014_08.mp4"
ffmpeg -i "$indir/20230921_GX020014.mp4" -ss 19:11.663 -to 19:52.958 $options "$outdir/20230921_GX020014_09.mp4"
ffmpeg -i "$indir/20230921_GX020014.mp4" -ss 20:44.070 -to 21:25.457 $options "$outdir/20230921_GX020014_10.mp4"
ffmpeg -i "$indir/20230921_GX020014.mp4" -ss 21:29.106 -to 22:10.379 $options "$outdir/20230921_GX020014_11.mp4"
ffmpeg -i "$indir/20230921_GX020014.mp4" -ss 22:33.423 -to 23:14.909 $options "$outdir/20230921_GX020014_12.mp4"
ffmpeg -i "$indir/20230921_GX020014.mp4" -ss 23:24.712 -to 24:06.008 $options "$outdir/20230921_GX020014_13.mp4"
ffmpeg -i "$indir/20230921_GX030012.mp4" -ss 04:46.327 -to 05:27.809 $options "$outdir/20230921_GX030012_01.mp4"
ffmpeg -i "$indir/20230921_GX030012.mp4" -ss 06:33.253 -to 07:14.451 $options "$outdir/20230921_GX030012_02.mp4"
ffmpeg -i "$indir/20230921_GX030012.mp4" -ss 08:17.393 -to 08:58.668 $options "$outdir/20230921_GX030012_03.mp4"
ffmpeg -i "$indir/20230921_GX030012.mp4" -ss 09:03.544 -to 09:44.829 $options "$outdir/20230921_GX030012_04.mp4"
ffmpeg -i "$indir/20230921_GX030012.mp4" -ss 09:55.838 -to 10:36.959 $options "$outdir/20230921_GX030012_05.mp4"
ffmpeg -i "$indir/20230921_GX030014.mp4" -ss 00:06.191 -to 01:02.442 $options "$outdir/20230921_GX030014_01.mp4"
ffmpeg -i "$indir/20230921_GX030014.mp4" -ss 03:43.224 -to 04:39.523 $options "$outdir/20230921_GX030014_02.mp4"
