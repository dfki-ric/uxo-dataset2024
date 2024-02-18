#!/usr/bin/bash

# NOTE: this program assumes that the entire preprocessing has been done!
# 
# The final step of the dataprocessing, this script will collect, cut and extract the preprocessed
# data and places the data in a new folder.
# 
# $1: csv file from the previous step containing the matching recordings and offsets
# $2: the folder to export the data to
# 
# example: ./dataset_2_export.bash ../data_processed/matches_day1.csv ../data_export/

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <csv-match-file> <export-folder>"
    exit 1
fi

python3 ./src/dataset_export.py $1 $2
