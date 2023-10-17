#!/usr/bin/env python
import sys
import os
import csv
import numpy as np
import pandas as pd


def usage():
    print(f'{sys.argv[0]} <gantry_extraction_folder>')


def find_motion_onset(csv_file):
    data = pd.read_csv(csv_file)
    data['diff'] = (data['x'].shift() != data['x']) | (data['y'].shift() != data['y'])
    onset_idx = data['diff'].idxmax()
    
    onset = data['timestamp_us'].iloc[onset_idx]
    start = data['timestamp_us'].iloc[0]
    end = data['timestamp_us'].iloc[-1]
    
    return start, end, onset


if __name__ == '__main__':
    if len(sys.argv) != 2:
        usage()
        raise RuntimeError('Wrong number of arguments')
    
    csv_dir_path = sys.argv[1]
    out_file_path = os.path.join(csv_dir_path, 'gantry_metadata.csv')
    
    with open(out_file_path, 'w') as out_file:
        writer = csv.writer(out_file)
        writer.writerow(['file', 'start_us', 'end_us', 'onset_us'])
        
        for csv_file in sorted(os.listdir(csv_dir_path)):
            if not csv_file.lower().endswith('.csv'):
                continue
            
            if csv_file == 'gantry_metadata.csv':
                continue
            
            print(f'{csv_file} ... ', end='')
            start, end, onset = find_motion_onset(os.path.join(csv_dir_path, csv_file))
            print(onset / 1e6)
            writer.writerow([csv_file, start, end, onset])
