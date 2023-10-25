#!/usr/bin/env python
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
    args = parser.parse_args()
    
    clip = cv2.VideoCapture(args.gopro_file)
    num_frames = int(clip.get(cv2.CAP_PROP_FRAME_COUNT))
    
    def gopro_frame_iterator():
        for idx in range(num_frames):
            clip.set(cv2.CAP_PROP_POS_FRAMES, idx)
            has_frame, frame = clip.read()
            if not has_frame:
                break
            yield cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    if args.method == 'lk':
        flow = calc_optical_flow_lk(gopro_frame_iterator, args.method, flow_params_lk, feature_params_lk)
    elif args.method == 'farnerback':
        flow = calc_optical_flow_farnerback(gopro_frame_iterator, args.method, flow_params_farneback)
    else:
        raise ValueError('Invalid method')

    out_file = os.path.join(os.path.dirname(args.gopro_file), os.path.splitext(os.path.basename(args.gopro_file))[0] + '_flow.csv')
    pd.DataFrame(flow).to_csv(out_file, header=None, index=None)
