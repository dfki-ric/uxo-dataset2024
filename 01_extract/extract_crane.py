#!/usr/bin/env python
import sys
import os
import csv
import rosbag


def usage():
    print(f'{sys.argv[0]} <rosbags-dir> <output-dir>')


def extract_bag(bag_file, out_dir_path):
    basename = os.path.splitext(os.path.basename(bag_file))[0]
    bag = rosbag.Bag(bag_file)
    
    with open(os.path.join(out_dir_path, basename + '.csv'), 'w') as out_file:
        writer = csv.writer(out_file)
        
        # Header
        writer.writerow(['timestamp_s', 'timestamp_ns', 'x', 'y', 'z'])
        
        for _, msg, _ in bag.read_messages('/odom'):
            stamp = msg.header.stamp
            x = msg.pose.pose.position.x
            y = msg.pose.pose.position.y
            z = msg.pose.pose.position.z
            
            writer.writerow([stamp.secs, stamp.nsecs, x, y, z])

    
if __name__ == '__main__':
    if len(sys.argv) != 3:
        usage()
        raise RuntimeError('Wrong number of arguments')
    
    bags_dir_path = sys.argv[1]
    out_dir_path = sys.argv[2]
    bags = sorted(f for f in os.listdir(bags_dir_path) if f.lower().endswith('.bag'))
    os.makedirs(out_dir_path, exist_ok=True)
    
    for bag_file in bags:
        basename = os.path.splitext(os.path.basename(bag_file))[0]
        print(f'extracting {basename} ...')
        extract_bag(os.path.join(bags_dir_path, bag_file), out_dir_path)
