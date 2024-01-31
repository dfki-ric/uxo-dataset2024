#!/bin/bash

# This script will extract the raw frames from the ARIS recordings. It will iterate over all .aris 
# files in the supplied directory ($1), and then place the frames in in a new directory in the 
# supplied output folder ($2). The directory will be named after the .aris file (minus the extension). 
# It will also extract the file and frame metadata and place them in the same directory as .yaml and 
# .csv files. The frames will be .pgm single channel images.
# 
# $1: input folder containing the .aris recordings
# $2: output folder to place the extracted frames and metadata in
# 
# example: ./aris_1_extract_all.bash ../data_raw/aris/day1 ../data_processed/aris/day1


if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <path-to-aris-folder> <output-folder>"
    exit 1
fi

for aris in $1/*.aris; do
    echo "extracting $aris ..."
    python3 ./src/aris_extract_full.py $aris $2
done
