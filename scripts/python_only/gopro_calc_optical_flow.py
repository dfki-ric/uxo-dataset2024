#!/usr/bin/env python
import sys
import os
import cv2
import pandas as pd
import argparse
import os
import getpass
from json import loads


from optical_flow import calc_optical_flow_lk, calc_optical_flow_farnerback

def read_json_dict():
    if os.path.isfile('.arisparameter'+getpass.getuser()) == True:
        with open('.arisparameter'+getpass.getuser(), 'r') as defaultread:
            jsondict = loads(defaultread.read())
        defaultread.closed
        in_dir_path=jsondict["gopro_downsample"]
        out_dir_path=jsondict["gopro_downsample"]
        if os.path.isdir(in_dir_path)==False:
            print("Automatically generated file-path of downsampled gopro-files not found")
            in_dir_path=input('Please insert it manually here:')
            in_dir_path=in_dir_path.replace("\\","/")
            out_dir_path=in_dir_path
    else:
        in_dir_path=""
        out_dir_path=""
    return in_dir_path,out_dir_path

flow_params_farneback = dict(
    pyr_scale = .5,
    levels = 3,
    winsize = 15,
    iterations = 2,
    poly_n = 5,
    poly_sigma = 1.2,
    flags = 0 #cv2.OPTFLOW_USE_INITIAL_FLOW,
)

flow_params_lk = dict(
    winSize = (10, 10),
    maxLevel = 1,
    criteria = (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 5, 0.03),
)

feature_params_lk = dict(
    maxCorners = 30,
    qualityLevel = 0.3,
    minDistance = 10,
    blockSize = 10,
)


if __name__ == '__main__':
    in_dir_path,out_dir_path=read_json_dict()
    listoffiles=[file for file in os.listdir(in_dir_path) if file.split(".")[-1]=="mp4"]
    
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
        
    for i,file in enumerate(listoffiles):
        parser = argparse.ArgumentParser()
        parser.add_argument('--gopro_file', default=os.path.join(in_dir_path,file))
        parser.add_argument('-m', '--method', choices=['lk', 'farnerback'], default=rmode)
        parser.add_argument('-r', '--recalc', choices=[True,False], default=rmode2)
        args = parser.parse_args()
        
        
        out_file = os.path.join(os.path.dirname(args.gopro_file), os.path.splitext(os.path.basename(args.gopro_file))[0] + '_flow.csv')
        if not args.recalc and os.path.isfile(out_file):
            print(f'{out_file} already exists, skipping')
            sys.exit(0)
        
        class GoproIterator:
            def __init__(self, gopro_file) -> None:
                self._clip = cv2.VideoCapture(args.gopro_file)
                self._num_frames = int(self._clip.get(cv2.CAP_PROP_FRAME_COUNT))
            
            def __iter__(self):
                for idx in range(len(self)):
                    self._clip.set(cv2.CAP_PROP_POS_FRAMES, idx)
                    has_frame, frame = self._clip.read()
                    if not has_frame:
                        break
                    yield cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
            def __len__(self):
                return self._num_frames
            
            def __next__(self):
                return
        
        iter = GoproIterator(args.gopro_file)
        print(f'{i+1}/{len(listoffiles)}')
        if args.method == 'lk':
            flow = calc_optical_flow_lk(iter, args.method, flow_params_lk, feature_params_lk)
        elif args.method == 'farnerback':
            flow = calc_optical_flow_farnerback(iter, args.method, flow_params_farneback)
        else:
            raise ValueError('Invalid method')
    
        pd.DataFrame(flow).to_csv(out_file, header=None, index=None)
