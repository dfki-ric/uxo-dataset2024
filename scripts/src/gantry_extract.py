#!/usr/bin/env python
import os
import csv
import rosbag
from tqdm import tqdm

from common import get_config


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
    config = get_config()

    input_path = config["gantry_input"]
    output_path = config["gantry_output"]
    time_adjust = str(config.get("gantry_time_adjust", "0"))

    os.makedirs(output_path, exist_ok=True)
    bag_files = sorted([x for x in os.listdir(input_path) if x.endswith(".bag")])

    for bag in tqdm(bag_files):
        bag_path = os.path.join(input_path, bag)
        extract_bag(bag_path, output_path, time_adjust)
