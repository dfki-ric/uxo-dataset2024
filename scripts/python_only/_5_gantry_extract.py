#!/usr/bin/env python
import sys
import os
import argparse
import csv
import rosbag
import os
import getpass
from json import loads
from json import dumps
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
            
def read_json_dict():
    if os.path.isfile('.arisparameter'+getpass.getuser()) == True:
        with open('.arisparameter'+getpass.getuser(), 'r') as defaultread:
            jsondict = loads(defaultread.read())
        defaultread.closed
        in_dir_path=jsondict["gantryinput"]
        out_dir_path=jsondict["gantry_extract"]
    else:
        in_dir_path=""
        out_dir_path=""
    return in_dir_path,out_dir_path
            

    
if __name__ == '__main__':
    in_dir_path,out_dir_path=read_json_dict()
    os.makedirs(out_dir_path, exist_ok=True)
    listoffiles=[file for file in os.listdir(in_dir_path) if file.split(".")[-1]=="bag"]
    time_adjust=0
    print("The gantry crane backend uses local timestamps")
    print("Choose local time adjust in hours (default=0):")
    try:
        time_adjust = float(input('Input:'))
    except:
        raise ValueError("no number input, using 0 instead")
    
    for i,bag in enumerate(listoffiles):
        #parser = argparse.ArgumentParser(description='Extracts gantry crane trajectory from a rosbag.' 
        #                                  'NOTE that the gantry crane backend uses local timestamps, '
        #                                  'which can be fixed by using the -z argument.')
        #parser.add_argument('bag_file', type=str,deafult=in_dir_path)
        #parser.add_argument('out_dir_path', type=str)
        
        ## The gantry crane backend uses localtime for timestamps :/
        #parser.add_argument('-z', '--time_adjust', type=float, default='+2', help='adjust timestamps by that many hours (+/-)')
        #args = parser.parse_args(sys.argv[1:])
        #args = parser.parse_args()
        
        #os.makedirs(args.out_dir_path, exist_ok=True)
        #bag_file = args.bag_file
        print(f'{bag} ({i+1}/{len(listoffiles)})')
        extract_bag(os.path.join(in_dir_path,bag), out_dir_path,time_adjust)
