import os
import re
import yaml
import numpy as np
import pandas as pd
import h5py as h5
import cv2


# TODO contact Christian Backe regarding dataset management and organization


def write_aris(hdf: h5.File, match: dict, root: str = '/') -> None:
    aris_dataset_path = match['aris_file']
    aris_basename = os.path.dirname(aris_dataset_path + '/')
    
    def get_metafile(appendix: str) -> str:
        return aris_dataset_path + '/' + aris_basename + '_' + appendix
    
    aris_group = hdf.create_group(root + 'aris/' + aris_basename)
    meta_group = aris_group.create_group('frame_metadata')
    
    # General recording metadata
    aris_group.attrs['Datetime'] = aris_basename
    with open(get_metafile('metadata.yaml')) as aris_meta_file:
        aris_meta = yaml.safe_load(aris_meta_file)
        
        num_frames = aris_meta['FrameCount']
        beam_count = aris_meta['NumRawBeams']
        bin_count = aris_meta['SamplesPerChannel']
        
        for key,value in aris_meta:
            aris_group.attrs[key] = value
    
    # Frame metadata
    frame_meta: pd.DataFrame = pd.read_csv(get_metafile('frames.csv'))
    for fm in frame_meta.columns:
        # Skip non-unique columns
        if len(pd.unique(frame_meta[fm])) > 1:
            meta_group.create_dataset(fm, data=frame_meta[fm])
            
    # Create links to some important datasets
    aris_group['timestamps'] = meta_group['FrameTime']
    aris_group['pan'] = meta_group['SonarPan']
    aris_group['tilt'] = meta_group['SonarTilt']
    aris_group['roll'] = meta_group['SonarRoll']
    
    # Add marks if present
    # with open(get_metafile('marks.yaml')) as marks_file:
    #     marks = yaml.safe_load(marks_file)
        
    # Add raw frames
    frames_raw = aris_group.create_dataset('frames_raw', (num_frames, beam_count, bin_count, 1), dtype=np.uint8)
    idx = 0
    for frame_file in os.listdir(aris_dataset_path):
        if not frame_file.endswith('.pgm'):
            continue
        
        frame = cv2.imread(frame_file, cv2.IMREAD_UNCHANGED)
        frames_raw[idx] = frame
        idx += 1
        
    # Add polar frames
    frames_polar = None
    idx = 0
    for frame_file in os.listdir(aris_dataset_path + '/polar'):
        if not frame_file.endswith('.pgm'):
            continue
        
        frame = cv2.imread(frame_file, cv2.IMREAD_UNCHANGED)
        if frames_polar is None:
            frames_polar = aris_group.create_dataset(frames_polar, (num_frames, frames_polar.shape[0], frames_polar.shape[1]), dtype=np.uint8)
        
        frames_polar[idx] = frame
        idx += 1
    

def write_gantry(hdf: h5.File, match: dict, root: str = '/') -> None:
    gantry_file = match['gantry_file']
    filename = os.path.splitext(os.path.basename(gantry_file))[0]
    gantry_group = hdf.create_group(root + 'gantry/' + filename)
    
    # Copy all metadata
    gantry_meta_file = os.path.dirname(gantry_file) + '/gantry_metadata.csv'
    gantry_all_meta = pd.read_csv(gantry_meta_file)
    gantry_meta = gantry_all_meta.iloc[os.path.basename(gantry_file)]
    
    for gm in gantry_meta.columns:
        gantry_group.attrs[gm] = gantry_meta[gm]
        
    # Copy the actual data
    gantry_data = pd.read_csv(gantry_file)
    for seq in gantry_data.columns:
        gantry_group.create_dataset(seq, data=gantry_data[seq])


def write_gopro(hdf: h5.File, match: dict, root: str = '/') -> None:
    gopro_file = match['gopro_file']
    filename = os.path.splitext(os.path.basename(gopro_file))[0]
    gopro_group = hdf.create_group(root + 'gopro/' + filename)
    
    # Copy all metadata
    gopro_meta_file = os.path.dirname(gopro_file) + '/gopro_metadata.csv'
    gopro_all_meta = pd.read_csv(gopro_meta_file)
    gopro_meta = gopro_all_meta.iloc[os.path.basename(gopro_file)]
    
    for gm in gopro_meta.columns:
        gopro_group.attrs[gm] = gopro_meta[gm]
    
    # Copy the frames
    clip = cv2.VideoCapture(gopro_file)
    width = int(clip.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
    height = int(clip.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
    frames_total = int(clip.get(cv2.CAP_PROP_FRAME_COUNT))
    
    frames = gopro_group.create_dataset('frames', (frames_total, width, height, 3), dtype=np.uint8)
    for frame_idx in range(frames_total):
        clip.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        has_frame, gopro_frame = clip.read()
        if has_frame:
            frames[frame_idx] = cv2.cvtColor(gopro_frame, cv2.COLOR_BGR2RGB)


def write_notes(hdf: h5.File, match: dict) -> None:
    notes: str = match['notes']
    lines = notes.split('\n')
    additional = []
    
    for line in lines:
        if not line.startswith('- '):
            additional.append(line)
            continue
        
        line = line[2:]
        line_low = line.lower()
        
        if line_low.startswith(('target:', 'trajectory:', 'pan:', 'tilt:', 'roll:')):
            key, value = line.split(': ', 1)
            hdf.attrs[key.lower()] = value
            
        elif 'transmit' in line.lower():
            hdf.attrs['transmit'] = line_low.replace('transmit', '').strip()
            
        elif re.match(r'[0-9]+db', line_low):
            hdf.attrs['gain'] = line
            
        else:
            additional.append(line)
            
    hdf.attrs['notes'] = '\n'.join(additional)


def write_distributed_dataset(match_file: str) -> None:
    matches = pd.read_csv(match_file)
    datasets = {}
    
    for idx,match in matches.iterrows():
        basename = os.path.dirname(match['aris_file'] + '/')
        hdf = 'datasets/' + basename + '.hdf'
        datasets[basename] = hdf
        
        with h5.File(hdf, 'w') as dataset:
            # Write metadata for this dataset
            dataset.attrs['date'] = basename
            dataset.attrs['aris_onset_frame_idx'] = match['aris_onset']
            dataset.attrs['gantry_offset_us'] = match['gantry_offset']
            dataset.attrs['gopro_frame_offset'] = match['gopro_offset']
            
            write_notes(dataset, match)
            
            write_aris(dataset, match)
            write_gantry(dataset, match)
            write_gopro(dataset, match)
        
    meta_hdf = 'metaset.hdf'
    with h5.File(meta_hdf, 'w') as meta:
        for key,dataset in datasets.items():
            meta[key] = h5.ExternalLink(dataset, '/')
    
    # TODO 
    # - region references
    # - target origins
    # - dimension scales
    # - add matching data as required (timezone offsets?)
    # - add meta hdf linking to other hdfs
    