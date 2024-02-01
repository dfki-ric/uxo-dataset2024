#!/usr/bin/bash

# Goes over the previously extracted gantry crane trajectories and checks for every trajectory, 
# where the motion starts. This is done by value, i.e. the first entry where the xyz values are 
# not equal to the previous row. The onsets will be written to a csv file with one entry per 
# trajectory.
# 
# $1: directory containing the previously extracted .csv gantry crane trajectories
# 
# example: ./preprocess_gantry_2_find_offsets.bash ../data_processed/gantry/day1/

if [ "$#" -ne 1]; then
    echo "Usage: $0 <gantry-extraction-dir>"
    exit 1
fi

python3 ./src/gantry_find_offsets.py $1
