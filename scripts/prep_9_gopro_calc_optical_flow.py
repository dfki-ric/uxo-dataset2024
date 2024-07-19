#!/usr/bin/env python
import sys
import os
import cv2
import pandas as pd
from tqdm import tqdm, trange

from common.config import get_config
from common.optical_flow import calc_optical_flow_lk, calc_optical_flow_farnerback


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
    config = get_config()

    input_path = config["gopro_extract"]
    resolutions = config["gopro_clip_resolution"]
    method = config.get("gopro_optical_flow_method", "lk")
    recalc = config.get("gopro_optical_flow_recalc", True)

    for res in resolutions.split('+'):
        gopro_clips = sorted([os.listdir(os.path.join(input_path, "clips_" + res))])

        for clip in tqdm(gopro_clips):
            clip_path = os.path.join(input_path, clip)

            out_file = os.path.join(
                os.path.dirname(clip_path), 
                os.path.splitext(os.path.basename(clip_path))[0] + '_flow.csv'
            )
            if not recalc and os.path.isfile(out_file):
                print(f'{out_file} already exists, skipping')
                sys.exit(0)
            
            class GoproIterator:
                def __init__(self, video) -> None:
                    self._clip = cv2.VideoCapture(video)
                    self._num_frames = int(self._clip.get(cv2.CAP_PROP_FRAME_COUNT))
                
                def __iter__(self):
                    for idx in trange(len(self)):
                        self._clip.set(cv2.CAP_PROP_POS_FRAMES, idx)
                        has_frame, frame = self._clip.read()
                        if not has_frame:
                            break
                        yield cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        
                def __len__(self):
                    return self._num_frames
            
            iter = GoproIterator(clip_path)
            
            if method == 'lk':
                flow = calc_optical_flow_lk(iter, method, flow_params_lk, feature_params_lk)
            elif method == 'farnerback':
                flow = calc_optical_flow_farnerback(iter, method, flow_params_farneback)
            else:
                raise ValueError('Invalid method')

            pd.DataFrame(flow).to_csv(out_file, header=None, index=None)
