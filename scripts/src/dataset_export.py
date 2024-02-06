#/usr/bin/env python3

import os
import argparse
import re
import shutil
import yaml
import pandas as pd
import cv2

from aris_definitions import FrameHeaderFields
from matching_context import MatchingContext, folder_basename


def export_recording(match: pd.Series, data_root: str, out_dir_root: str, gopro_resolution: str = '', gopro_format: str = 'jpg', trim_from_gopro: bool = True):
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
    os.makedirs(rec_root, exist_ok=False)
    
    rec_aris_raw = os.path.join(rec_root, 'aris_raw')
    os.makedirs(rec_aris_raw, exist_ok=False)
    
    rec_aris_polar = os.path.join(rec_root, 'aris_polar')
    os.makedirs(rec_aris_polar, exist_ok=False)
    
    if ctx.has_gopro:
        rec_gopro = os.path.join(rec_root, 'gopro')
        os.makedirs(rec_gopro, exist_ok=False)
    
    # Export data
    indices = []
    gantry_data = []
    for aris_frame_idx in range(ctx.aris_start_frame, ctx.aris_end_frame + 1):
        frametime = ctx.get_aris_frametime(aris_frame_idx)
        
        # GoPro frames
        if ctx.has_gopro:
            gopro_file = os.path.join(rec_gopro, f'{aris_frame_idx:04}.{gopro_format}')
            gopro_frame, _ = ctx.get_gopro_frame(frametime)
            if gopro_frame is not None:
                cv2.imwrite(gopro_file, gopro_frame)
            
            # If gopro footage is available, only export data when a gopro frame is also available
            if trim_from_gopro and gopro_frame is None:
                continue
            
        # ARIS frames
        shutil.copy(ctx.aris_frames_raw[aris_frame_idx], os.path.join(rec_aris_raw, f'{aris_frame_idx:04}.pgm'))
        shutil.copy(ctx.aris_frames_polar[aris_frame_idx], os.path.join(rec_aris_polar, f'{aris_frame_idx:04}.pgm'))
        
        # Collect gantry data (write later)
        (x, y, z), _ = ctx.get_gantry_odom(frametime)
        gantry_data.append((aris_frame_idx, x, y, z))
        
        indices.append(aris_frame_idx)
    
    if trim_from_gopro and len(indices) != ctx.aris_active_frames:
        print(f' -> recording was trimmed to frames {indices[0]} to {indices[-1]}')
    
    # Relevant ARIS metadata
    frame_meta_sel = ctx.aris_frames_meta[ctx.aris_frames_meta[FrameHeaderFields.frame_index].isin(indices)]
    frame_meta_sel.to_csv(os.path.join(rec_root, 'aris_frame_meta.csv'), index=False)
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
    parser.add_argument('export_dir')
    parser.add_argument('-d', '--data-root', default='')
    parser.add_argument('-r', '--gopro-resolution', default='')
    parser.add_argument('-f', '--gopro-format', default='jpg')
    parser.add_argument('-t', '--trim-from-gopro', action=argparse.BooleanOptionalAction, default=True)
    
    args = parser.parse_args()
    match_file_path = args.match_file
    export_dir = args.export_dir
    data_root = args.data_root if args.data_root else os.path.dirname(match_file_path)
    gopro_resolution = args.gopro_resolution
    gopro_format = args.gopro_format
    trim_from_gopro = args.trim_from_gopro
    
    # Copy recording data
    print(f'Exporting recordings to {export_dir}')
    os.makedirs(export_dir, exist_ok=True)
    matches = pd.read_csv(match_file_path, converters={
        'aris_file': str,
        'gantry_file': str,
        'gopro_file': str,
        'notes': str,
    })
    
    recordings_dir = os.path.join(export_dir, 'recordings')
    for _,match in matches.iterrows():
        try:
            print(folder_basename(match['aris_file']))
            export_recording(match, 
                             data_root, 
                             recordings_dir, 
                             gopro_resolution=gopro_resolution, 
                             gopro_format=gopro_format, 
                             trim_from_gopro=trim_from_gopro)
        except OSError:
            print(' -> already exists, skipping')
            continue
    
    # Copy 3d models
    model_dir = os.path.join(export_dir, '3d_models/')
    shutil.copytree(os.path.join(data_root, '../3d_models'), 
                    model_dir, 
                    dirs_exist_ok=True, 
                    ignore=lambda src, names: [x for x in names if 'metashape' in x])

    # Copy scripts
    scripts_dir = os.path.join(export_dir, 'scripts/')
    shutil.copytree(os.path.join(os.path.dirname(__file__), '../'), 
                    scripts_dir, 
                    dirs_exist_ok=True, 
                    ignore=lambda src, names: [x for x in names if '__pycache__' in x])

    # Copy README and more
    other_files = [
        '../README.md',
        '../dataset.jpg',
    ]
    for file in other_files:
        shutil.copy(os.path.join(data_root, file), export_dir)
