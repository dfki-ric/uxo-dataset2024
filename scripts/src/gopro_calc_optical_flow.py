#!/usr/bin/env python
import sys
import os
import cv2
import pandas as pd
import argparse

from optical_flow import calc_optical_flow_lk, calc_optical_flow_farnerback


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
    parser = argparse.ArgumentParser()
    parser.add_argument('gopro_file')
    parser.add_argument('-m', '--method', choices=['lk', 'farnerback'], default='lk')
    parser.add_argument('-r', '--recalc', action=argparse.BooleanOptionalAction, default=True)
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
    
    iter = GoproIterator(args.gopro_file)
    
    if args.method == 'lk':
        flow = calc_optical_flow_lk(iter, args.method, flow_params_lk, feature_params_lk)
    elif args.method == 'farnerback':
        flow = calc_optical_flow_farnerback(iter, args.method, flow_params_farneback)
    else:
        raise ValueError('Invalid method')

    pd.DataFrame(flow).to_csv(out_file, header=None, index=None)
