#!/usr/bin/bash

if [ "$#" -ne 1]; then
    echo "Usage: $0 <gantry-extraction-dir>"
    exit 1
fi

python3 ./src/gantry_find_offsets.py $1
