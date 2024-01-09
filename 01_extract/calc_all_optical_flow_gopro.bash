#!/bin/bash
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path-to-gopro-clip-folder>"
    exit 1
fi

for gopro_file in $1/*.mp4; do
    echo "$gopro_file ..."
    python3 ./calc_optical_flow_gopro.py $gopro_file
done