#!/usr/bin/env python
import src.aris_to_polar
import os
import sys

# Converts the raw ARIS sonar frames previously extracted to polar coordinates, This is not required, 
# but helps matching with GoPro footage and human interpretation.
#
# $1: the output folder of the previous script where the extracted aris recordings were placed in
#
# example: ./preprocess_aris_2_to_polar.bash ../data_processed/aris/day1

def usage():
    print(f"{sys.argv[0]} <path-to-aris-extraction-folders>")

if __name__ == "__main__":
    if not 2 <= len(sys.argv) < 3:
        usage()
        raise RuntimeError("Wrong number of arguments")

    dir_path = sys.argv[1]

    if dir_path.endswith("/"):
        dir_path = dir_path[:-1]

    files_dir = [
        f for f in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, f))
    ]
    
    for directory in files_dir:
        path = os.path.join(dir_path,directory)
        path_polar = os.path.join(path,'polar')
        src.aris_to_polar.main(path, path_polar)