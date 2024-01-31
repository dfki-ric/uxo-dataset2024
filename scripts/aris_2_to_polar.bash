#!/bin/bash

# Converts the raw ARIS sonar frames previously extracted to polar coordinates, This is not required, 
# but helps matching with GoPro footage and human interpretation.
#
# $1: the output folder of the previous script where the extracted aris recordings were placed in
#
# example: ./aris_2_to_polar.bash ../data_processed/aris/day1

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path-to-aris-extraction-folders>"
    exit 1
fi

for aris_dir in $1/*/; do
    echo "$aris_dir ..."
    python3 ./src/aris_to_polar.py $aris_dir $aris_dir/polar
done
