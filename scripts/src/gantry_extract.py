#!/usr/bin/env python
import sys
import os
import argparse
import csv
import rosbag
from tqdm import tqdm


def stamp_to_microseconds(stamp):
    return int(stamp.secs * 1e6) + int(stamp.nsecs // 1e3)


def extract_bag(bag_file, out_dir_path, time_adjust=0.):
    basename = os.path.splitext(os.path.basename(bag_file))[0]
    bag = rosbag.Bag(bag_file)
    
    with open(os.path.join(out_dir_path, basename + '.csv'), 'w') as out_file:
        writer = csv.writer(out_file)
        
        # Header
        writer.writerow(['timestamp_us', 'x', 'y', 'z'])
        
        num_msgs = bag.get_message_count('/odom')
        for _, msg, _ in tqdm(bag.read_messages('/odom'), total=num_msgs):
            stamp = msg.header.stamp
            
            t = stamp_to_microseconds(stamp) + time_adjust * 3600 * 1e6
            x = msg.pose.pose.position.x
            y = msg.pose.pose.position.y
            z = msg.pose.pose.position.z
            
            writer.writerow([t, x, y, z])

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extracts gantry crane trajectory from a rosbag.' 
                                     'NOTE that the gantry crane backend uses local timestamps, '
                                     'which can be fixed by using the -z argument.')
    parser.add_argument('bag_file', type=str)
    parser.add_argument('out_dir_path', type=str)
    
    # The gantry crane backend uses localtime for timestamps :/
    parser.add_argument('-z', '--time_adjust', type=float, default='+2', help='adjust timestamps by that many hours (+/-)')
    args = parser.parse_args(sys.argv[1:])
    
    os.makedirs(args.out_dir_path, exist_ok=True)
    bag_file = args.bag_file
    extract_bag(bag_file, args.out_dir_path, args.time_adjust)
