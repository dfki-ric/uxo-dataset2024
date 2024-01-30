#!/bin/bash

# Downsampling takes a very, very long time for the 5.3k videos, so it's better to do this for the already cut clips

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
    ffmpeg -loglevel error -stats -i "$file" $OPTIONS "$OUTDIR"/$(basename $file .mp4)_sd.mp4
done
