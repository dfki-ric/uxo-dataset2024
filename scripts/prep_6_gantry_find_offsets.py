#!/usr/bin/env python
import os
import csv
import pandas as pd
from tqdm import tqdm

from common.config import get_config


def find_motion_onset(csv_file):
    data = pd.read_csv(csv_file)
    
    # Find index of first change in x or y
    # NOTE: don't use index before, as there may be a considerable delay
    diff = data['x'].diff() + data['y'].diff()
    diff[diff.isna()] = 0.
    onset_idx = diff.ne(0).idxmax()
    
    onset = data['timestamp_us'].iloc[onset_idx]
    start = data['timestamp_us'].iloc[0]
    end = data['timestamp_us'].iloc[-1]
    
    return start, end, onset


if __name__ == '__main__':
    config = get_config()
    
    input_path = config["gantry_extract"]
    metadata_file = os.path.join(input_path, "gantry_metadata.csv")

    with open(metadata_file, 'w') as out_file:
        writer = csv.writer(out_file)
        writer.writerow(['file', 'start_us', 'end_us', 'onset_us'])
        
        for csv_file in tqdm(sorted(os.listdir(input_path))):
            if not csv_file.lower().endswith('.csv'):
                continue
            
            if csv_file == 'gantry_metadata.csv':
                continue
            
            print(f'{csv_file} ... ', end='')
            start, end, onset = find_motion_onset(os.path.join(input_path, csv_file))
            print((onset - start) / 1e6)
            writer.writerow([csv_file, start, end, onset])
