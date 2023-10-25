#!/usr/bin/env python
import os
import cv2
import pandas as pd
import argparse

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
    parser = argparse.ArgumentParser()
    parser.add_argument('aris_data_dir')
    parser.add_argument('-m', '--method', choices=['lk', 'farnerback'], default='lk')
    args = parser.parse_args()
    
    if args.aris_data_dir.endswith('/'):
        args.aris_data_dir = args.aris_data_dir[:-1]
    
    frames_path = os.path.join(args.aris_data_dir, 'polar')
    if not os.path.isdir(frames_path):
        print(f'{args.aris_data_dir} does not contain polar frames, using raw frames instead')
        frames_path = args.aris_data_dir
    aris_frames = sorted(os.path.join(frames_path, f) for f in os.listdir(frames_path) if f.lower().endswith('.pgm'))
    
    def aris_frame_iterator():
        for idx in range(len(aris_frames)):
            yield cv2.imread(aris_frames[idx], cv2.IMREAD_UNCHANGED)
    
    if args.method == 'lk':
        flow = calc_optical_flow_lk(aris_frame_iterator, args.method, flow_params_lk, feature_params_lk)
    elif args.method == 'farnerback':
        flow = calc_optical_flow_farnerback(aris_frame_iterator, args.method, flow_params_farneback)
    else:
        raise ValueError('Invalid method')
    
    out_file = os.path.join(args.aris_data_dir, os.path.split(args.aris_data_dir)[-1] + '_flow.csv')
    pd.DataFrame(flow).to_csv(out_file, header=None, index=None)
