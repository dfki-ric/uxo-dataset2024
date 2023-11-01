#!/bin/bash
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path-to-aris-extraction-folders>"
    exit 1
fi

for aris_dir in $1/*/; do
    echo "$aris_dir ..."
    python3 ./calc_optical_flow_aris.py $aris_dir
done
