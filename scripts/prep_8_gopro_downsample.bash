#!/bin/bash

# Use this script to downsample GoPro footage to lower resolutions and remove the audio. Downsampling 
# takes a very, very long time for the 5.3k videos, so it's better to do this for the already cut 
# clips instead of the entire footage. On the other hand, if you're planning to try out different 
# resolutions, converting the complete videos first may be more efficient. As with the python scripts,
# this script reads the config.yaml file and uses the options therein.

mydir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
gopro_clips=$(sed -n -e 's/^gopro_extract://p' "$mydir/config.yaml" | tr -d '"' | xargs)
resolutions=$(sed -n -e 's/^gopro_clip_resolution://p' "$mydir/config.yaml" | tr -d '"' | xargs)
indir="$gopro_clips/clips_uhd"

export IFS="+"
for res in "$resolutions"; do
    case "$res" in
    "uhd" | "copy")
        continue
        ;;
    "fhd")
        options='-vf scale=1920:1080 -c:v libx264 -an'
        ;;
    "sd")
        options='-vf scale=640:360 -c:v libx264 -an'
        ;;
    *)
        echo "resolution '$res' not recognized, must be one of 'uhd', 'fhd', 'sd'"
        exit 1
    esac

    outdir="$gopro_clips/clips_$res"
    mkdir -p "$outdir"
    trap "exit" INT

    for file in "$indir"/*.mp4; do
        echo "downsampling $file ..."
        ffmpeg -loglevel error -stats -i "$file" $options "$outdir"/$(basename $file .mp4).mp4
    done
