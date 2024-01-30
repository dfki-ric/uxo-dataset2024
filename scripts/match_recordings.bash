#!/usr/bin/bash

if [ "$#" -eq 1 ]; then
    python3 ./src/dataset_match_recordings.py --day $1
elif [ "$#" -eq 3 ]; then
    python3 ./src/dataset_match_recordings.py --dirs $1 $2 $3
else
    echo "Usage: $0 <1|2> OR $0 <aris-recordings> <gopro-recordings> <gantry-recordings>"
    exit 1
fi
