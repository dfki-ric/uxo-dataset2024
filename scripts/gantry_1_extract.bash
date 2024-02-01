#!/usr/bin/bash

# Extracts the gantry crane trajectories from their rosbags and exports them as .csv files.
# 
# $1: directory where the rosbags have been saved
# $2: directory where the extracted .csv files will be saved
# 
# example: ./gantry_1_extract.bash ../data_raw/gantry/day1/ ../data_processed/gantry/day1/

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <gantry-rosbags-dir> <output-dir>"
    exit 1
fi

for gantry in $1/*.bag; do
    echo "extracting $gantry ..."
    python3 ./src/gantry_extract.py $gantry $2
done
