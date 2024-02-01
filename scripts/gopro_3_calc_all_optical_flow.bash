#!/bin/bash

# Calculate the magnitude of the optical flow over the GoPro clips. This is similar to the script for
# calculating the optical flow magnitude for the ARIS recordings. Both of these solely exist to make
# matching ARIS and GoPro footage easier. The magnitudes will be written as one .csv file per clip in 
# the input folder.
# 
# $1: folder containing the cut (and downsampled) GoPro clips
# 
# example: ./gopro_3_calc_all_optical_flow.bash ../data_processed/gopro/day1/clips_sd/

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path-to-gopro-clip-folder>"
    exit 1
fi

for gopro_file in $1/*.mp4; do
    echo "$gopro_file ..."
    python3 ./src/gopro_calc_optical_flow.py $gopro_file
done
