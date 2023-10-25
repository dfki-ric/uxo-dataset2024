#!/usr/bin/env python
import sys
import os
import numpy as np
import pandas as pd
import cv2

from aris import get_beamcount_from_pingmode, BeamWidthsAris3000_64, BeamWidthsAris3000_128


def usage():
    print(f'{sys.argv[0]} <input-folder> <output-folder>')


def aris_frame_to_polar(frame, frame_idx, metadata):
    frame_meta = metadata.iloc[frame_idx]
    pingmode = frame_meta['PingMode']
    bin_count = int(frame_meta['SamplesPerBeam'])
    beam_count = get_beamcount_from_pingmode(pingmode)
    
    if beam_count == 64:
        beam_angles = BeamWidthsAris3000_64
    elif beam_count == 128:
        beam_angles = BeamWidthsAris3000_128
    else:
        raise ValueError(f'Unexpected pingmode {pingmode}')
    
    beam_range = beam_angles[-1][2] - beam_angles[0][1]
    frame_half_w = int(np.ceil(bin_count * np.tan(np.deg2rad(beam_range / 2))))
    polar_frame = np.zeros((bin_count, frame_half_w * 2), dtype=np.uint8)
    
    for beam_idx in range(beam_count):
        start_angle = beam_angles[beam_idx][1]
        end_angle = beam_angles[beam_idx][2]
        
        for bin_idx in range(bin_count):
            intensity = frame[bin_idx, beam_idx]
            cv2.ellipse(polar_frame, (frame_half_w, bin_count), (bin_idx, bin_idx), 0, 270 + start_angle, 270 + end_angle, int(intensity), 1)
        
    # In ARIS frames, beams are ordered right to left
    return cv2.flip(polar_frame, 1)


if __name__ == '__main__':
    if len(sys.argv) != 3:
       usage()
       raise RuntimeError('Wrong number of arguments')
    
    in_dir_path = sys.argv[1]
    out_dir_path = sys.argv[2]
    
    if in_dir_path.endswith('/'):
        in_dir_path = in_dir_path[:-1]
    basename = os.path.basename(in_dir_path)
    
    os.makedirs(out_dir_path, exist_ok=True)
    
    with open(os.path.join(in_dir_path, f'{basename}_frames.csv'), 'r') as frames_meta_file:
        metadata = pd.read_csv(frames_meta_file)
    
        for f in sorted(os.listdir(in_dir_path)):
            if not f.lower().endswith('.pgm'):
                continue
            
            frame_idx = int(f.split('_')[1].split('.')[0])
            frame = cv2.imread(os.path.join(in_dir_path, f), cv2.IMREAD_UNCHANGED)
            polar = aris_frame_to_polar(frame, frame_idx, metadata)
            
            cv2.imwrite(os.path.join(out_dir_path, os.path.basename(f)), polar)
    