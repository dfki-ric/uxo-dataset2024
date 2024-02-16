#!/usr/bin/bash

# NOTE: this program assumes that all other preprocessing steps have been done!
# 
# Open a graphical tool for finding the offsets between the datasets (see README). There are some 
# predefined parametersets for day 1 and day 2, but you can also supply your own set of processed
# data folders. The outputs will be the match csv files found in the processed data folder.
# 
# $1: the day to use (1 or 2)
# 
# $1: extracted aris recordings root folder
# $2: gopro clips folder
# $3: gantry crane trajectories folder
# 
# example: ./dataset_1_match_recordings.bash 1

if [ "$#" -eq 1 ]; then
    python3 ./src/dataset_match_recordings.py --day $1
elif [ "$#" -eq 3 ]; then
    python3 ./src/dataset_match_recordings.py --dirs $1 $2 $3
else
    echo "Usage: $0 <1|2> OR $0 <aris-recordings> <gopro-recordings> <gantry-recordings>"
    exit 1
fi
