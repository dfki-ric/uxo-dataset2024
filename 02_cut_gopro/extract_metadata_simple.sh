#!/bin/bash


if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <path-to-gopro-folder> <out-file.csv>"
    exit 1
fi


echo "file,creation_time" > $2
for f in $1/*.MP4; do
    creation_time=$(ffprobe $f -loglevel error -of default -show_entries format:stream=creation_time | grep creation_time | cut -d "=" -f 2-)
    echo "$(basename $f ),$creation_time" >> $2
done
