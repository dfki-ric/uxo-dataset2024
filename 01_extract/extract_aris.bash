#!/bin/bash
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <path-to-aris-folder> <output-folder>"
    exit 1
fi

for aris in $1/*.aris; do
    echo "extracting $aris ..."
    python3 ./aris_full_export/python/extract_full.py $aris $2
done
