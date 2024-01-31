#!/bin/bash

# Calculates the magnitude of the optical flow between each frame of the previously extracted ARIS 
# recordings. This is not required, but was used to make matching sonar to GoPro data easier.
# 
# $1: the output folder of the previous script where the extracted aris recordings were placed in
# 
# example: ./aris_3_calc_all_optical_flow.bash ../data_processed/aris/day1

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path-to-aris-extraction-folders>"
    exit 1
fi

for aris_dir in $1/*/; do
    echo "$aris_dir ..."
    python3 ./src/aris_calc_optical_flow.py $aris_dir
done
