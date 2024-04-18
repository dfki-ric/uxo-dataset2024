#!/usr/bin/env python
import sys
import os
import cv2
import pandas as pd
from tqdm import tqdm, trange

from common import get_config
from optical_flow import calc_optical_flow_lk, calc_optical_flow_farnerback


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
    config = get_config()

    input_path = config["aris_extract"]
    method = config.get("aris_optical_flow_method", "lk")
    recalc = config.get("aris_optical_flow_recalc", True)

    recordings = sorted([x for x in os.listdir(input_path) if os.path.isdir(x)])

    for rec_name in tqdm(recordings):
        aris_data_dir = os.path.join(input_path, rec_name)
        
        if aris_data_dir.endswith('/'):
            aris_data_dir = aris_data_dir[:-1]
            
        out_file = os.path.join(aris_data_dir, os.path.split(aris_data_dir)[-1] + '_flow.csv')
        if not recalc and os.path.isfile(out_file):
            print(f'{out_file} already exists, skipping')
            sys.exit(0)
        
        frames_path = os.path.join(aris_data_dir, 'polar')
        if not os.path.isdir(frames_path):
            print(f'{aris_data_dir} does not contain polar frames, using raw frames instead')
            frames_path = aris_data_dir
        aris_frames = sorted(
            os.path.join(frames_path, f) 
            for f in os.listdir(frames_path) 
            if f.lower().endswith('.pgm')
        )
        
        class ImageFileIterator:
            def __init__(self, image_files) -> None:
                self._image_files = image_files
            
            def __iter__(self):
                for idx in trange(len(self._image_files)):
                    yield cv2.imread(self._image_files[idx], cv2.IMREAD_UNCHANGED)
                    
            def __len__(self):
                return len(self._image_files)
        
        iter = ImageFileIterator(aris_frames)
        
        if method == 'lk':
            flow = calc_optical_flow_lk(iter, method, flow_params_lk, feature_params_lk)
        elif method == 'farnerback':
            flow = calc_optical_flow_farnerback(iter, method, flow_params_farneback)
        else:
            raise ValueError('Invalid method')
        
        pd.DataFrame(flow).to_csv(out_file, header=None, index=None)
        #print(flow.shape)
