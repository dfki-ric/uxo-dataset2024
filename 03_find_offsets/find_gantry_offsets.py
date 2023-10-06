#!/usr/bin/env python
import sys
import os
import csv
import numpy as np
import rosbag


def usage():
    print(f'{sys.argv[0]} <rosbag_folder> <output-file.csv>')


# TODO return start, onset and end instead
def find_motion_onset(bag_file):    
    bag = rosbag.Bag(bag_file)
    prev_msg = None
    
    for _, msg, _ in bag.read_messages('/odom'):
        if prev_msg:
            if    not np.isclose(msg.pose.pose.position.x, prev_msg.pose.pose.position.x) \
               or not np.isclose(msg.pose.pose.position.y, prev_msg.pose.pose.position.y):
                stamp = prev_msg.header.stamp
                return stamp.secs, stamp.nsecs
        
        prev_msg = msg
        
    return -1, 0


if __name__ == '__main__':
    if len(sys.argv) != 3:
        usage()
        raise RuntimeError('Wrong number of arguments')
    
    bag_dir_path = sys.argv[1]
    out_file_path = sys.argv[2]
    
    with open(out_file_path, 'w') as out_file:
        writer = csv.writer(out_file, delimiter=';')
        writer.writerow(['file', 'onset_s', 'onset_ns'])
        
        for bag_file in sorted(os.listdir(bag_dir_path)):
            if not bag_file.lower().endswith('.bag'):
                continue
            
            print(f'{bag_file} ... ', end='')
            onset_s, onset_ns = find_motion_onset(os.path.join(bag_dir_path, bag_file))
            print(onset_s)
            writer.writerow([bag_file, onset_s, onset_ns])
