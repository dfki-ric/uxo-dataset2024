#!/bin/bash

# Use this script to downsample GoPro footage to lower resolutions and remove the audio. Downsampling 
# takes a very, very long time for the 5.3k videos, so it's better to do this for the already cut 
# clips instead of the entire footage. On the other hand, if you're planning to try out different 
# resolutions, converting the complete videos first may be more efficient. Adjust the OPTIONS below 
# to choose your desired resolution, e.g. 640:360 for SD or 1920:1080 for FHD.
# 
# $1: folder containing the footage to downsample
# $2: folder to place the downsampled footage in
# 
# example: ./preprocess_gopro_2_downsample_all.bash ../data_processed/gopro/day1/clips_uhd/ ../data_processed/gopro/day1/clips_sd/

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <input-folder> <output-folder>"
    exit 1
fi

INDIR=$1
OUTDIR=$2
OPTIONS='-vf scale=640:360 -c:v libx264 -an'

mkdir -p "$OUTDIR"

for file in "$INDIR"/*.mp4; do
    echo "downsampling $file ..."
    ffmpeg -loglevel error -stats -i "$file" $OPTIONS "$OUTDIR"/$(basename $file .mp4).mp4
done
