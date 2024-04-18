#!/usr/bin/env python
import sys
import os
import csv
import getpass
from json import loads
from json import dumps
import pandas as pd
from tqdm import tqdm


def usage():
    print(f'{sys.argv[0]} <gantry_extraction_folder>')
    
def read_json_dict():
    if os.path.isfile('.arisparameter'+getpass.getuser()) == True:
        with open('.arisparameter'+getpass.getuser(), 'r') as defaultread:
            jsondict = loads(defaultread.read())
        defaultread.closed
        in_dir_path=jsondict["gantry_extract"]
        out_dir_path=jsondict["gantry_extract"]
    else:
        in_dir_path=""
        out_dir_path=""
    return in_dir_path,out_dir_path


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
    # if len(sys.argv) != 2:
    #     usage()
    #     raise RuntimeError('Wrong number of arguments')
        
    csv_dir_path,out_dir_path=read_json_dict()
    listoffiles=[file for file in os.listdir(csv_dir_path) if file.split(".")[-1]=="csv"]
    for i,csv_file in enumerate(listoffiles):
        out_file_path = os.path.join(csv_dir_path, 'gantry_metadata.csv')
        with open(out_file_path, 'w') as out_file:
            writer = csv.writer(out_file)
            writer.writerow(['file', 'start_us', 'end_us', 'onset_us'])
            
            for csv_file in tqdm(sorted(os.listdir(csv_dir_path))):
                if not csv_file.lower().endswith('.csv'):
                    continue
                
                if csv_file == 'gantry_metadata.csv':
                    continue
                
                print(f'{csv_file} ... ', end='')
                start, end, onset = find_motion_onset(os.path.join(csv_dir_path, csv_file))
                print((onset - start) / 1e6)
                writer.writerow([csv_file, start, end, onset])
