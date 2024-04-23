import os
import yaml
import numpy as np
import pandas as pd
import cv2


def folder_basename(s):
    if s.endswith('/'):
        s = s[:-1]
    return os.path.split(s)[-1]


_aris_metadata_cache = {}
def get_aris_metadata(aris_data_dir):
    if aris_data_dir in _aris_metadata_cache:
        return _aris_metadata_cache[aris_data_dir]
    
    aris_basename = folder_basename(aris_data_dir)
    with open(os.path.join(aris_data_dir, aris_basename + '_metadata.yaml'), 'r') as f:
        file_meta = yaml.safe_load(f)
    
    frame_meta = pd.read_csv(os.path.join(aris_data_dir, aris_basename + '_frames.csv'))
    
    try:
        with open(os.path.join(aris_data_dir, aris_basename + '_marks.yaml'), 'r') as f:
            marks_meta = yaml.safe_load(f)
    except IOError:
        marks_meta = None
    
    _aris_metadata_cache[aris_data_dir] = (file_meta, frame_meta, marks_meta)
    return file_meta, frame_meta, marks_meta


_gopro_metadata_cache = {}
def get_gopro_metadata(gopro_files_dir):
    if gopro_files_dir in _gopro_metadata_cache:
        return _gopro_metadata_cache[gopro_files_dir]
    
    metadata = pd.read_csv(os.path.join(gopro_files_dir, 'gopro_metadata.csv'))
    _gopro_metadata_cache[gopro_files_dir] = metadata
    return metadata


_gantry_metadata_cache = {}
def get_gantry_metadata(gantry_files_dir):
    if gantry_files_dir in _gantry_metadata_cache:
        return _gantry_metadata_cache[gantry_files_dir]
    
    metadata = pd.read_csv(os.path.join(gantry_files_dir, 'gantry_metadata.csv'))
    _gantry_metadata_cache[gantry_files_dir] = metadata
    return metadata


class MatchingContext:
    def __init__(self, aris_dir, gantry_file, gopro_file, polar_img_format='png'):
        self.aris_basename = folder_basename(aris_dir)
        self.gantry_basename = folder_basename(gantry_file)
        self.gopro_basename = folder_basename(gopro_file)
        
        self.recording_label = self.aris_basename
        
        # Load ARIS data
        aris_dir_polar = os.path.join(aris_dir, 'polar')
        
        self.aris_frames_raw = sorted(
            os.path.join(aris_dir, f) 
            for f in os.listdir(aris_dir) 
            if f.lower().endswith('.pgm')
        )
        try:
            self.aris_frames_polar = sorted(
                os.path.join(aris_dir_polar, f) 
                for f in os.listdir(aris_dir_polar) 
                if f.lower().endswith(polar_img_format)
            )
        except FileNotFoundError:
            print(f'ARIS dataset {self.aris_basename} does not contain polar frames, using raw frames instead')
            self.aris_frames_polar = None
        
        self.aris_file_meta, self.aris_frames_meta, self.aris_marks_meta = get_aris_metadata(aris_dir)
        self._aris_frame_idx = 0
        self._aris_start_frame = 0
        self._aris_end_frame = len(self.aris_frames_raw) - 1
        self.aris_tick_step = 1
        self.aris_motion_onset = None
        self.aris_frames_total = len(self.aris_frames_raw)
        self.aris_t0 = self.get_aris_frametime(0)
        self.aris_duration = self.get_aris_frametime(-1) - self.aris_t0

        # Load beginning of motion frame from save file
        if self.aris_marks_meta and 'onset' in self.aris_marks_meta:
            onset = max(0, self.aris_marks_meta['onset'])
            self._aris_start_frame = onset
            self.aris_motion_onset = onset
        
        # Load Gantry recording
        all_gantry_meta = get_gantry_metadata(os.path.dirname(gantry_file))
        self.gantry_meta = all_gantry_meta.loc[all_gantry_meta['file'] == self.gantry_basename].iloc[0]
        self.gantry_data = pd.read_csv(gantry_file)
        self.gantry_t0 = self.gantry_meta['start_us']
        self.gantry_onset = self.gantry_meta['onset_us']
        self.gantry_duration = self.gantry_meta['end_us'] - self.gantry_t0
        self.gantry_offset = self.gantry_onset - self.gantry_t0
        
        # Load GoPro clip
        self.has_gopro = bool(gopro_file)
        if gopro_file:
            # GoPro metadata is no longer required (and was never useful)
            #all_gopro_meta = get_gopro_metadata(os.path.dirname(gopro_file))
            #self.gopro_meta = all_gopro_meta.loc[all_gopro_meta['file'] == self.gopro_basename].iloc[0]
            self.gopro_clip = cv2.VideoCapture(gopro_file)
            self.gopro_frame_idx = -1
            self.gopro_frames_total = int(self.gopro_clip.get(cv2.CAP_PROP_FRAME_COUNT))
            self.gopro_fps = self.gopro_clip.get(cv2.CAP_PROP_FPS)
            self.gopro_offset = 0
            self._gopro_frame = None


    @property
    def aris_start_frame(self):
        return self._aris_start_frame
    
    @aris_start_frame.setter
    def aris_start_frame(self, new_val):
        self._aris_start_frame = min(new_val, self.aris_end_frame - 1)
    
    @property
    def aris_end_frame(self):
        return self._aris_end_frame
    
    @aris_end_frame.setter
    def aris_end_frame(self, new_val):
        self._aris_end_frame = max(new_val, self.aris_start_frame + 1)
    
    @property
    def aris_active_frames(self):
        return self.aris_end_frame - self.aris_start_frame + 1
    
    @property
    def aris_active_duration(self):
        return self.get_aris_frametime(self.aris_end_frame) - self.get_aris_frametime(self.aris_start_frame)
    
    def get_aris_frametime(self, frame_idx):
        # FrameTime = time of recording on PC (µs since 1970)
        # sonarTimeStamp = time of recording on sonar (µs since 1970), not sure if synchronized to PC time
        return self.aris_frames_meta['FrameTime'].iloc[frame_idx]
    
    def get_aris_frametime_ext(self, frame_idx):
        if frame_idx < 0:
            # Note: in contrast to what the header definitions claim, FrameRate is in frames per SECOND!
            return self.aris_t0 - abs(frame_idx) / np.mean(self.aris_frames_meta['FrameRate']) * 1e6
        if frame_idx >= self.aris_frames_total:
            return self.aris_t0 + self.aris_duration + (frame_idx - self.aris_frames_total) / np.mean(self.aris_frames_meta['FrameRate']) * 1e6
    
        return self.get_aris_frametime(frame_idx)
    
    def aristime_to_gopro_idx(self, aris_frametime):
        time_from_start = aris_frametime - self.get_aris_frametime(self.aris_start_frame)
        return int(time_from_start / 1e6 * self.gopro_fps) + self.gopro_offset
    
    def get_gopro_frame(self, aris_frametime, exact: bool = True):
        new_frame_idx = self.aristime_to_gopro_idx(aris_frametime)
        
        if new_frame_idx != self.gopro_frame_idx:
            self.gopro_clip.set(cv2.CAP_PROP_POS_FRAMES, new_frame_idx)
            clip_pos = self.gopro_clip.get(cv2.CAP_PROP_POS_FRAMES)
            
            if exact and clip_pos != new_frame_idx:
                return None, clip_pos
            
            self.gopro_frame_idx = new_frame_idx
            has_frame, gopro_frame = self.gopro_clip.read()
            if has_frame:
                self._gopro_frame = gopro_frame
        
        return self._gopro_frame, self.gopro_frame_idx
    
    def get_usable_gopro_range(self):
        # We can skip so much of the gopro clip that it barely starts playing
        range_min = -int(self.aris_duration / 10e3 // self.gopro_fps)
        # But we can also delay playback so much that it barely starts playing
        range_max = int(self.gopro_frames_total)
        
        return range_min, range_max
    
    def get_gantry_odom(self, aris_frametime):
        time_after_onset = aris_frametime - self.get_aris_frametime(self.aris_start_frame)
        timepos = self.gantry_t0 + self.gantry_offset + time_after_onset
        
        timepos = max(timepos, self.gantry_t0)
        timepos = min(timepos, self.gantry_t0 + self.gantry_duration)
        
        t = self.gantry_data['timestamp_us']   
        xi = np.interp(timepos, t, self.gantry_data['x'])
        yi = np.interp(timepos, t, self.gantry_data['y'])
        zi = np.interp(timepos, t, self.gantry_data['z'])
        return (xi, yi, zi), timepos
