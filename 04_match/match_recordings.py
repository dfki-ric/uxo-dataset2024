#!/usr/bin/env python

import sys
import os
import matplotlib.pyplot as plt
import rosbag
import cv2


def usage():
    print(f'{sys.argv[0]} <aris-folder> <gantry-folger> <gopro-folder>')


if __name__ == '__main__':
    if len(sys.argv) != 4:
        usage()
        raise RuntimeError('Wrong number of arguments')

    aris_dir_path = sys.argv[1]
    gantry_dir_path = sys.argv[2]
    gopro_dir_path = sys.argv[3]
    
    aris_data_dirs = sorted(f for f in os.listdir(aris_dir_path))
    gantry_bags

