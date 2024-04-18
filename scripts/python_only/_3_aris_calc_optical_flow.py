#!/usr/bin/env python
import sys
import os
import cv2
import pandas as pd
import argparse
import getpass
import os
from json import loads
from json import dumps

from optical_flow import calc_optical_flow_lk, calc_optical_flow_farnerback

def read_json_dict():
    if os.path.isfile('.arisparameter'+getpass.getuser()) == True:
        with open('.arisparameter'+getpass.getuser(), 'r') as defaultread:
            jsondict = loads(defaultread.read())
        defaultread.closed
        in_dir_path=jsondict["aris_extract_full_out"]
        out_dir_path=jsondict["aris_calc_optical_flow_out"]
    else:
        in_dir_path=""
        out_dir_path=""
    return in_dir_path,out_dir_path



flow_params_farneback = dict(
    pyr_scale = .5,
    levels = 5,
    winsize = 5,
    iterations = 2,
    poly_n = 9,
    poly_sigma = 2,
    flags = 0 #cv2.OPTFLOW_USE_INITIAL_FLOW,
)

flow_params_lk = dict(
    winSize = (5, 5),
    maxLevel = 5,
    criteria = (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 5, 0.03),
)

feature_params_lk = dict(
    maxCorners = 30,
    qualityLevel = 0.4,
    minDistance = 10,
    blockSize = 10,
)   


if __name__ == '__main__':
    in_dir_path,out_dir_path=read_json_dict()
    subfolders = [ f.path for f in os.scandir(in_dir_path) if f.is_dir()]
    print("Choose method:")
    print("(1) lk")
    print("(2) farnerback")
    try:
        mode = int(input('Input:'))
        if mode==1:
            rmode="lk"
        elif mode==2:
            rmode="farnerback"
        else:
            raise ValueError("invalid number")
            
    except ValueError:
        print("Not a number")
    
    print("Recalculating:")
    print("(1) True")
    print("(2) False")
    try:
        mode = int(input('Input:'))
        if mode==1:
            rmode2="True"
        elif mode==2:
            rmode2="False"
        else:
            raise ValueError("invalid number")
            
    except ValueError:
        print("Not a number")
    for sub in subfolders:
        parser = argparse.ArgumentParser()

        parser.add_argument('-m', '--method', choices=['lk', 'farnerback'], default=rmode)
        parser.add_argument('-r', '--recalc', choices=[True,False],default=rmode2)
        parser.add_argument('-d', '--aris_data_dir',default=sub)
        args = parser.parse_args()
        
        if args.aris_data_dir.endswith('/'):
            args.aris_data_dir = args.aris_data_dir[:-1]
            
        out_file = os.path.join(args.aris_data_dir, os.path.split(args.aris_data_dir)[-1] + '_flow.csv')
        if not args.recalc and os.path.isfile(out_file):
            print(f'{out_file} already exists, skipping')
            sys.exit(0)
        
        #frames_path = os.path.join(args.aris_data_dir, 'polar')
        frames_path=sub
        if not os.path.isdir(frames_path):
            print(f'{args.aris_data_dir} does not contain polar frames, using raw frames instead')
            frames_path = args.aris_data_dir
        aris_frames = sorted(os.path.join(frames_path, f) for f in os.listdir(frames_path) if f.lower().endswith('.pgm'))
        
        class ImageFileIterator:
            def __init__(self, image_files) -> None:
                self._image_files = image_files
            
            def __iter__(self):
                for idx in range(len(self._image_files)):
                    yield cv2.imread(self._image_files[idx], cv2.IMREAD_UNCHANGED)
                    
            def __len__(self):
                return len(self._image_files)
            
            def __next__(self):
                return 
                
        
        iter = ImageFileIterator(aris_frames)
        
        if args.method == 'lk':
            flow = calc_optical_flow_lk(iter, args.method, flow_params_lk, feature_params_lk)
        elif args.method == 'farnerback':
            flow = calc_optical_flow_farnerback(iter, args.method, flow_params_farneback)
        else:
            raise ValueError('Invalid method')
        
        # if args.method == 'lk':
        #     flow = calc_optical_flow_lk([cv2.imread(i, cv2.IMREAD_UNCHANGED) for i in aris_frames], args.method, flow_params_lk, feature_params_lk)
        # elif args.method == 'farnerback':
        #     flow = calc_optical_flow_farnerback([cv2.imread(i, cv2.IMREAD_UNCHANGED) for i in aris_frames], args.method, flow_params_farneback)
        # else:
        #     raise ValueError('Invalid method')
        
        
        pd.DataFrame(flow).to_csv(out_file, header=None, index=None)
        #print(flow.shape)
