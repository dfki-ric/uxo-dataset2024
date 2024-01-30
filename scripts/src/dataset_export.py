#/usr/bin/env python3

import os
import argparse
import re
import shutil
import yaml
import pandas as pd
import cv2

from matching_context import MatchingContext, folder_basename


def export_recording(match: pd.Series, data_root: str, out_dir_root: str, gopro_resolution: str = '', overwrite=False):
    # Help to resolve the recording locations
    aris_dir = os.path.join(data_root, match['aris_file'])
    gantry_file = os.path.join(data_root, match['gantry_file'])
    gopro_file = os.path.join(data_root, match['gopro_file']) if match['gopro_file'] else ''
    
    # Switch to different GoPro resolution if desired
    if gopro_resolution and gopro_file:
        gopro_file = re.sub(r'/clips_../', '/' + gopro_resolution + '/', gopro_file)
        if gopro_file and not os.path.isfile(gopro_file):
            raise ValueError(f'{gopro_resolution}: missing GoPro file {gopro_file}')
    
    # Context makes it much easier to retrieve individual data points from the processed recordings
    ctx = MatchingContext(aris_dir, gantry_file, gopro_file)
    ctx.aris_start_frame = match['aris_onset']
    ctx.gopro_offset = match['gopro_offset']  # TODO not right yet!
    ctx.gantry_offset = match['gantry_offset']
    
    # Create export folders
    rec_root = os.path.join(out_dir_root, ctx.recording_label)
    os.makedirs(rec_root, exist_ok=overwrite)
    
    rec_aris_raw = os.path.join(rec_root, 'aris_raw')
    os.makedirs(rec_aris_raw, exist_ok=overwrite)
    
    rec_aris_polar = os.path.join(rec_root, 'aris_polar')
    os.makedirs(rec_aris_polar, exist_ok=overwrite)
    
    if ctx.has_gopro:
        rec_gopro = os.path.join(rec_root, 'gopro')
        os.makedirs(rec_gopro, exist_ok=overwrite)
    
    # Export data
    gantry_data = []
    for aris_frame_idx in range(ctx.aris_start_frame, ctx.aris_end_frame + 1):
        frametime = ctx.get_aris_frametime(aris_frame_idx)
        
        # ARIS frames
        shutil.copy(ctx.aris_frames_raw[aris_frame_idx], os.path.join(rec_aris_raw, f'{aris_frame_idx:04}.pgm'))
        shutil.copy(ctx.aris_frames_polar[aris_frame_idx], os.path.join(rec_aris_polar, f'{aris_frame_idx:04}.pgm'))
        
        # Collect gantry data (write later)
        (x, y, z), _ = ctx.get_gantry_odom(frametime)
        gantry_data.append((aris_frame_idx, x, y, z))
        
        # GoPro frames
        if ctx.has_gopro:
            gopro_frame, _ = ctx.get_gopro_frame(frametime)
            cv2.imwrite(os.path.join(rec_gopro, f'{aris_frame_idx:04}.ppm'), gopro_frame)
    
    # ARIS metadata
    ctx.aris_frames_meta.to_csv(os.path.join(rec_root, 'aris_frame_meta.csv'))
    with open(os.path.join(rec_root, 'aris_file_meta.yaml'), 'w') as f:
        yaml.safe_dump(ctx.aris_file_meta, f)
    
    # Write gantry data
    pd.DataFrame(gantry_data, columns=['aris_frame_idx', 'x', 'y', 'z']).to_csv(os.path.join(rec_root, 'gantry.csv'), header=True, index=False)
    
    # Additional notes
    with open(os.path.join(rec_root, 'notes.txt'), 'w') as f:
        f.write(match['notes'])
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('match_file')
    parser.add_argument('output_dir')
    parser.add_argument('-d', '--data-root', default='')
    parser.add_argument('-r', '--gopro-resolution', default='')
    parser.add_argument('-o', '--overwrite', action=argparse.BooleanOptionalAction, default=False)
    
    args = parser.parse_args()
    match_file_path = args.match_file
    out_dir_path = args.output_dir
    data_root = args.data_root if args.data_root else os.path.dirname(match_file_path)
    gopro_resolution = args.gopro_resolution
    overwrite_existing = args.overwrite
    
    os.makedirs(out_dir_path, exist_ok=True)
    matches = pd.read_csv(match_file_path, converters={
        'aris_file': str,
        'gantry_file': str,
        'gopro_file': str,
        'notes': str,
    })
    
    for _,match in matches.iterrows():
        try:
            print(folder_basename(match['aris_file']))
            export_recording(match, data_root, out_dir_path, gopro_resolution=gopro_resolution, overwrite=overwrite_existing)
        except OSError:
            print(' -> already exists, skipping')
            continue
