#!/usr/bin/bash

# NOTE: this program assumes that the export has completed!
# 
# Simple script for stepping through an exported recording
# 
# $1: the folder where the recording was exported
# 
# example: ./view_recording.bash ../data_export/recordings/2023-09-20_171105/

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <recording-folder>"
    exit 1
fi

python3 ./src/view_recording.py $1
