#!/usr/bin/env python
import sys
import os
import ffmpeg
import csv
import argparse

from timestamps import day1, day2


def basename(s):
    return os.path.split(s)[-1]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('gopro_dir_path')
    parser.add_argument('out_file_path')
    parser.add_argument('--day1', action=argparse.BooleanOptionalAction)
    parser.add_argument('--day2', action=argparse.BooleanOptionalAction)
    
    args = parser.parse_args()
    
    if not args.day1 and not args.day2:
        parser.print_help()
        print('You must specify either --day1 or --day2')
        sys.exit(1)
    
    with open(args.out_file_path, 'w') as out_file:
        writer = csv.writer(out_file)
        writer.writerow(['file', 'creation_time', 'start', 'end'])
        
        for gopro_file in sorted(os.listdir(args.gopro_dir_path)):
            if not gopro_file.lower().endswith('.mp4'):
                continue
            
            gopro_filename = basename(gopro_file)
            
            if args.day1 and gopro_filename in day1:
                timestamps = day1[gopro_filename]
            elif args.day2 and gopro_filename in day2:
                timestamps = day2[gopro_filename]
            else:
                print(f'"{gopro_filename}" not found in dataset')
                continue
            
            print(gopro_file)
            gopro_basename = os.path.splitext(gopro_filename)[0]
            metadata = ffmpeg.probe(os.path.join(args.gopro_dir_path, gopro_file))
            creation_time = metadata['format']['tags']['creation_time']
            
            for idx,stamp in enumerate(timestamps):
                writer.writerow([f'{gopro_basename}_{idx+1:02}.MP4', creation_time, stamp.start, stamp.stop])
