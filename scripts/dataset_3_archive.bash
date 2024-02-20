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

archive="$(dirname $1)/$(basename $1).7z"
7z a -mx=5 -r "$archive" $1
echo "Created archive: $archive"
