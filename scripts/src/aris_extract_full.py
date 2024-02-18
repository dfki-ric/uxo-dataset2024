#!/usr/bin/env python
import sys
import os
import struct
import csv
import yaml
from enum import Enum
import numpy as np
import cv2
from tqdm import tqdm

import aris_definitions as aris_definitions
from aris_definitions import get_beamcount_from_pingmode, FileHeaderFields as ArisFile, FrameHeaderFields as ArisFrame


class _Struct:
    def __init__(self, definition, fieldnames) -> None:
        self.definition = definition
        self.fieldnames = fieldnames
        self.size = struct.calcsize(definition)
        
    def read(self, file) -> dict:
        chunk = file.read(self.size)
        
        if len(chunk) < self.size:
            return None
        
        values = struct.unpack(self.definition, chunk)
        # Access through strings instead of enums is uglier but more efficient for us
        keys = [k.value for k in self.fieldnames] if issubclass(self.fieldnames, Enum) else self.fieldnames
        file_header = {k:v for k,v in zip(keys, values)}
        
        return file_header

FileHeaderStruct = _Struct(aris_definitions.FileHeaderDefinition, ArisFile)
FrameHeaderStruct = _Struct(aris_definitions.FrameHeaderDefinition, ArisFrame)




def usage():
    print(f'{sys.argv[0]} <input-file> <output-folder>')


if __name__ == '__main__':
    if len(sys.argv) != 3:
       usage()
       raise RuntimeError('Wrong number of arguments')
    
    in_file = None
    out_file = None
    
    try:
        in_file_path = sys.argv[1]
        out_dir_path = sys.argv[2]
        #in_file_path = 'ARIS_2023_09_20/2023-09-20_145625.aris'
        #out_dir_path = 'matched_data/data/test/'
        
        in_file = open(in_file_path, 'rb')
        filename = os.path.splitext(os.path.basename(in_file_path))[0]
        
        # Basic sanity checks
        file_header = FileHeaderStruct.read(in_file)
        if file_header[ArisFile.version.value] != 0x05464444:
            raise RuntimeError(f'Corrupt file: 0x{file_header[ArisFile.version.value]:02x}')
        
        frame_header = FrameHeaderStruct.read(in_file)
        if frame_header[ArisFrame.version.value] != 0x05464444:
            raise RuntimeError(f'Corrupt frame: 0x{frame_header[ArisFrame.version.value]:02x}')
        
        os.makedirs(os.path.join(out_dir_path, filename), exist_ok=True)


        # Write the file meta data
        with open(os.path.join(out_dir_path, filename, filename + '_metadata.yaml'), 'w') as f:
            yaml.safe_dump(file_header, f)
        
        # Read first frame and prepare buffer for frame data
        frame_h = frame_header[ArisFrame.samples_per_beam.value]
        frame_w = get_beamcount_from_pingmode(frame_header[ArisFrame.ping_mode.value])
        frame_data = np.zeros([frame_h, frame_w], dtype=np.uint8)
        num_frames = file_header[ArisFile.frame_count.value]
        frame_number_padding = 4  #int(np.log10(num_frames)) + 1
        
        # Prepare the frame metadata file
        out_file = open(os.path.join(out_dir_path, filename, filename + '_frames.csv'), 'w')
        writer = csv.DictWriter(out_file, frame_header.keys())
        writer.writeheader()
        
        # Write frame metadata and frames
        with tqdm(total=num_frames) as t:
            while frame_header is not None:
                # Write header to csv
                writer.writerow(frame_header)
                
                # Write data to ppm
                frame_idx = frame_header[ArisFrame.frame_index.value]
                in_file.readinto(frame_data.data)
                cv2.imwrite(os.path.join(out_dir_path, filename, f'{frame_idx:0{frame_number_padding}}.pgm'), frame_data)
                t.update()
                
                # Read next header
                frame_header = FrameHeaderStruct.read(in_file)
    finally:
        if in_file:
            in_file.close()
        if out_file:
            out_file.close()