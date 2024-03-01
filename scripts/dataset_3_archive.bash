#!/usr/bin/bash

# Compress and archive a folder. This script serves both for convenience and documentation purposes.
# 
# $1: the folder to archive
# 
# example: ./dataset_3_archive.bash ../data_export

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <folder>"
    exit 1
fi

archive="$(dirname $1)/$(basename $1)"

# Archive everything but the polar transformed images
7z a -mx=5 -r "${archive}.7z" $1 -xr'!*/aris_polar/*'

# Archive only the polar transformed images
7z a -mx=5 -r "${archive}_polar.7z" -ir"!${1}*/aris_polar/*"

echo "Created archive: $archive"
