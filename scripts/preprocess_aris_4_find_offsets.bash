#!/usr/bin/bash

# This is a graphical tool to step through the ARIS recordings and manually/visually identify, when
# the sonar starts moving. Use the arrow keys (or numpad 2,4,6,8) to step 1 or 10 frames at a time.
# Once you have identified the motion onset, press '0' to mark the frame. You can place additional
# marks using 'm'. Press enter to save your marks and move to the next dataset, or 's' to move to 
# the next one without saving. Exit the app with 'q'.
# 
# $1: the output folder of the previous script where the extracted aris recordings were placed in
# 
# example: ./preprocess_aris_4_find_offsets.bash ../data_processed/aris/day1

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <aris-recordings-root-folder>"
    exit 1
fi

python3 ./src/aris_find_offsets.py $1
