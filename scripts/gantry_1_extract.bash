#!/usr/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <gantry-rosbags-dir> <output-dir>"
    exit 1
fi

python3 ./src/gantry_extract.py $1 $2
