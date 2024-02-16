#!/usr/bin/env python
import sys
import os
import numpy as np
import pandas as pd
import cv2

from aris_definitions import get_beamcount_from_pingmode, BeamWidthsAris3000_64, BeamWidthsAris3000_128, FrameHeaderFields


def usage():
    print(f'{sys.argv[0]} <input-folder> <output-folder>')


def aris_frame_to_polar(frame, frame_idx, metadata, norm_intensity=True, scale=1.):
    frame_meta = metadata.iloc[frame_idx]
    pingmode = frame_meta[FrameHeaderFields.ping_mode]
    bin_count = int(frame_meta[FrameHeaderFields.samples_per_beam])
    beam_count = get_beamcount_from_pingmode(pingmode)
    
    if beam_count == 64:
        beam_angles = np.array(BeamWidthsAris3000_64)
    elif beam_count == 128:
        beam_angles = np.array(BeamWidthsAris3000_128)
    else:
        raise ValueError(f'Unexpected pingmode {pingmode}')
    
    window_start = frame_meta[FrameHeaderFields.window_start]
    window_length = frame_meta[FrameHeaderFields.window_length]
    bins_per_meter = bin_count / window_length
    #beam_widths = beam_angles[:, 2] - beam_angles[:, 1]
    
    # The sonar only takes measurements starting from a certain distance
    min_radius = bins_per_meter * window_start
    
    # The leftmost edge will be lower than the center of the closest profile
    distance_bottom_left = np.sin(np.deg2rad(beam_angles[-1, 1] + 90)) * min_radius
    
    # We need a few additional pixel to include the corners of the bottom profile
    bottom_profile_offset = int(abs(min_radius - distance_bottom_left))
    
    # The top profile is further away from the origin than the image bottom
    last_profile_distance = int(bin_count + bottom_profile_offset + min_radius)
    beam_range = beam_angles[-1, 2] - beam_angles[0, 1]
    frame_half_w = int(np.ceil(last_profile_distance * np.tan(np.deg2rad(beam_range / 2))) * scale)
    frame_h = int((bin_count + bottom_profile_offset) * scale)
    polar_frame = np.zeros((frame_h, frame_half_w * 2), dtype=np.uint8)
    
    if norm_intensity:
        int_min = np.min(frame)
        int_max = np.max(frame)
    
    for beam_idx in range(beam_count):
        _, start_angle, end_angle = beam_angles[beam_idx]
        
        for bin_idx in range(bin_count):
            intensity = frame[bin_idx, beam_idx]
            
            if norm_intensity:
                intensity = int((intensity - int_min) / (int_max - int_min) * 255)
            
            # The radius of each circle has to account for the offset of the center and the bottom
            # profile corners
            radius = (bin_idx + min_radius + bottom_profile_offset) * scale
            
            # Originally this used cv2.ellipse; however, this gives terrible results as the angles 
            # are internally rounded to integers so that a lookup table can be used. This uses a LOT
            # of information in the resulting image!
            
            # Find out how many pixels across we need to travel (usually only one)
            x_start = int(np.cos(np.deg2rad(start_angle + 90)) * radius + frame_half_w)
            x_end = int(np.cos(np.deg2rad(end_angle + 90)) * radius + frame_half_w)
            cross_distance = max(1, x_end - x_start + 1)
            angle_delta = abs(end_angle - start_angle) / cross_distance
            
            for i in range(cross_distance):
                angle = start_angle + i * angle_delta
                x = int(np.cos(np.deg2rad(angle + 90)) * radius + frame_half_w)
                y = int(frame_h - max(0, np.sin(np.deg2rad(angle + 90)) * radius - min_radius) - 1)
                polar_frame[y, x] = intensity
                
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
    