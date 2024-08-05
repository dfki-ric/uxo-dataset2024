#!/usr/bin/env python3
import os
import re
import shutil
import yaml
import pandas as pd
import numpy as np
from scipy.spatial.transform import Rotation as R
import cv2
from tqdm import tqdm, trange

from common.config import get_config
from common.aris_definitions import FrameHeaderFields
from common.matching_context import MatchingContext, folder_basename
from dataset.calibration.tf_demo.transforms import get_tf_manager


def _create_ar3_df(df_aris_metadata, df_portal_crane):
    tm = get_tf_manager()

    poss = []
    for index, row in df_portal_crane.iterrows():
        A2B = np.eye(4) 
        A2B[:3,3] = np.array(row[['x','y','z']])
        tm.add_transform("setup/portal_crane", "world", A2B=A2B)
        poss.append(tm.get_transform("setup/ar3", "world")[:3, 3])

    rots = [(R.from_matrix(tm.get_transform("setup/ar3", "world")[:3,:3]) * 
             R.from_euler('xyz', row[['SonarRoll', 'SonarTilt', 'SonarPan']], degrees=True)).as_quat() for index, row in df_aris_metadata.iterrows()]

    df_ar3 = pd.DataFrame()
    df_ar3['aris_frame_idx'] = df_portal_crane['aris_frame_idx']
    df_ar3[['pos.x','pos.y', 'pos.z']] = poss.round(6)
    df_ar3[['rot.x','rot.y', 'rot.z', 'rot.w']] = rots.round(6)

    return df_ar3

def get_target_type(notes: str) -> str:
    for line in notes.splitlines():
        if 'target:' in line.lower():
            return line.split(':', maxsplit=1)[-1].strip().lower().replace(' ', '_')
        
    return 'other'


def export_recording(match: pd.Series, 
                     data_root: str, 
                     out_dir_root: str, 
                     aris_polar_img_format: str = 'png',
                     gopro_resolution: str = 'fhd', 
                     gopro_format: str = 'jpg', 
                     trim_from_gopro: bool = True
) -> None:
    # Help to resolve the recording locations
    aris_dir = os.path.join(data_root, match['aris_file'])
    gantry_file = os.path.join(data_root, match['gantry_file'])
    gopro_file = os.path.join(data_root, match['gopro_file']) if match['gopro_file'] else ''
    
    # Switch to different GoPro resolution if desired
    if gopro_resolution and gopro_file:
        gopro_file = re.sub(r'/clips_.+?/', '/clips_' + gopro_resolution + '/', gopro_file)
        if gopro_file and not os.path.isfile(gopro_file):
            raise ValueError(f'{gopro_resolution}: missing GoPro file {gopro_file}')
    
    # Context makes it much easier to retrieve individual data points from the processed recordings
    ctx = MatchingContext(aris_dir, 
                          gantry_file, 
                          gopro_file, 
                          polar_img_format=aris_polar_img_format)
    ctx.aris_start_frame = match['aris_onset']
    ctx.gopro_offset = match['gopro_offset']
    ctx.gantry_offset = match['gantry_offset']
    
    # Create export folders
    rec_root = os.path.join(out_dir_root, get_target_type(match['notes']), ctx.recording_label)
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
    name = folder_basename(match['aris_file'])
    for aris_frame_idx in trange(ctx.aris_start_frame, ctx.aris_end_frame + 1, desc=name):
        frametime = ctx.get_aris_frametime(aris_frame_idx)
        
        # GoPro frames
        if ctx.has_gopro:
            gopro_file = os.path.join(rec_gopro, f'{aris_frame_idx:04}.{gopro_format}')

            if os.path.isfile(gopro_file):
                print(f' -> frame {aris_frame_idx} already exists in export, skipping rest of this recording')
                break

            gopro_frame, _ = ctx.get_gopro_frame(frametime)
            if gopro_frame is not None:
                cv2.imwrite(gopro_file, gopro_frame)
            
            # If gopro footage is available, only export data when a gopro frame is also available
            if trim_from_gopro and gopro_frame is None:
                continue
            
        # ARIS frames
        shutil.copy(ctx.aris_frames_raw[aris_frame_idx], os.path.join(rec_aris_raw, f'{aris_frame_idx:04}.pgm'))
        shutil.copy(ctx.aris_frames_polar[aris_frame_idx], os.path.join(rec_aris_polar, f'{aris_frame_idx:04}.{aris_polar_img_format}'))
        
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
    
    # Write ar3 data
    _create_ar3_df(frame_meta_sel, gantry_data).to_csv(os.path.join(rec_root, 'ar3.csv'), header=True, index=False)

    # Additional notes
    with open(os.path.join(rec_root, 'notes.txt'), 'w') as f:
        f.write(match['notes'])
        

if __name__ == '__main__':
    config = get_config()

    match_file = config["match_file"]
    export_dir = config["export_dir"]
    polar_img_format = config["aris_to_polar_image_format"]
    gopro_resolution = config.get("export_gopro_resolution", "fhd")
    gopro_format = config.get("export_gopro_format", "jpg")
    trim_from_gopro = config.get("export_only_with_gopro", True)

    data_root = os.path.dirname(match_file)
    
    # Copy recording data
    print(f'Exporting recordings to {export_dir}')
    os.makedirs(export_dir, exist_ok=True)
    matches = pd.read_csv(match_file, converters={
        'aris_file': str,
        'gantry_file': str,
        'gopro_file': str,
        'notes': str,
    })
    
    recordings_dir = os.path.join(export_dir, 'recordings')
    for _,match in tqdm(matches.itertuples(), total=len(matches), desc='overall'):
        export_recording(match, 
                         data_root, 
                         recordings_dir, 
                         aris_polar_img_format=polar_img_format,
                         gopro_resolution=gopro_resolution, 
                         gopro_format=gopro_format, 
                         trim_from_gopro=trim_from_gopro)
    
    # NOTE labels have been generated after export, so this script can't know about them

    # Copy 3d models
    print('Copying 3d models...')
    model_dir = os.path.join(export_dir, '3d_models/')
    shutil.copytree(os.path.join(data_root, '../3d_models'), 
                    model_dir, 
                    dirs_exist_ok=True, 
                    ignore=lambda src, names: [x for x in names if 'metashape' in x])

    # Copy scripts
    print('Copying scripts...')
    scripts_dir = os.path.join(export_dir, 'scripts/')
    shutil.copytree(os.path.dirname(__file__), 
                    scripts_dir, 
                    dirs_exist_ok=True, 
                    ignore=lambda src, names: [x for x in names if '__pycache__' in x])

    # Copy calibration data
    print('Copying calibrations...')
    calib_dir = os.path.join(export_dir, 'calibration')
    shutil.copytree(os.path.join(data_root, '../calibration'),
                    calib_dir,
                    dirs_exist_ok=True)

    # Copy README and more
    print('Tidying up...')
    other_files = [
        '../README.md',
        '../preview.jpg',
    ]
    for file in other_files:
        shutil.copy(os.path.join(data_root, file), export_dir)

    print(f'Done! Find your dataset at: {export_dir}')
