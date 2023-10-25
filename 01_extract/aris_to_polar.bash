#!/bin/bash
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path-to-aris-extraction-folders>"
    exit 1
fi

for aris_dir in $1/*/; do
    echo "$aris_dir ..."
    python3 ./aris_to_polar.py $aris_dir $aris_dir/polar
done
