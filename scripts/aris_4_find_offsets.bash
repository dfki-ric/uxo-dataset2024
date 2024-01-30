#!/usr/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <aris-recordings-root-folder>"
    exit 1
fi

python3 ./src/aris_find_offsets.py $1
