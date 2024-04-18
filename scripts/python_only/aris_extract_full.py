#!/usr/bin/env python
import sys
import os
import struct
import csv
import yaml
import getpass
from enum import Enum
import numpy as np
import cv2
from tqdm import tqdm
from json import loads
from json import dumps

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




def generate_json_dictionary(in_file_path,out_dir_path,in_bag_path,out_bag_path,gopro_downsample_path):
    jsondict={}
    jsondict["arisinput"]=in_file_path
    jsondict["aris_extract_full_out"]=out_dir_path
    jsondict["aris_to_polar_in"]=out_dir_path
    jsondict["aris_to_polar_out"]=os.path.join(out_dir_path,"polar")
    jsondict["aris_calc_optical_flow_in"]=os.path.join(out_dir_path,"polar")
    jsondict["aris_calc_optical_flow_out"]=out_dir_path
    jsondict["gantryinput"]=in_bag_path
    jsondict["gantry_extract"]=out_bag_path
    jsondict["gopro_downsample"]=gopro_downsample_path
    
    
    with open('.arisparameter'+getpass.getuser(), 'w') as defaultspeichern2:
        defaultspeichern2.write(dumps(jsondict))
    

def usage():
    print(f'{sys.argv[0]} <input-file> <output-folder>')


if __name__ == '__main__':
    # if len(sys.argv) != 3:
    #    usage()
    #    raise RuntimeError('Wrong number of arguments')
    
    in_file = None
    out_file = None
    
    #directory for aris files
    in_file_path="C:/Users/kevinmarquardt/Desktop/data_raw_sample/aris/day1"#(1)
    in_file_path="C:/Users/kevinmarquardt/Desktop/data_raw_sample"#(2)
 
    
    """
    for every run a user-specific json file is created and stored in the python-script directory: "arisparameterusername"
    the json file contains the source- and outpot-folders for aris, gantry and gopro data
    the json file is automatically imported for all following preprocessing-steps, so you need to define the source- and output-directory only in this script.
    this only works if you dont change the username, but allows simultaneous user-specific precprocessing-flows

    Note for file-storage-system
    you can use the automatic generation of gantry and gopro source folders, if the structur looks as follows:
    //in_file_path:
        ->/aris
            ->/*.aris
            ->...
        ->/gantry
            ->/*.bag
            ->...
        ->gopro
            ->/*.mp4
            ->...
    you need to define the main directory with the aris, gantry and gopro folder as in_file_path
    
    you need to use the lines marked with a (1) for this mode
    
    
    if you use other data structures (e.g. seperate date-folders inside the aris-, gantry- or gopro-folder), you need to define the 3 input paths manually.
    for the given example you need to run the entire preprocessing-procedure day by day
    
    you need to use the lines marked with a (2) for this mode
    
    """
    
    
    
    
    #directory for aris .aris-files
    path=in_file_path#(2)
    #in_file_path=os.path.join(path,"aris")#(1)
    
    #directory for gantry .bag-files
    in_bag_path="K:/EKB/GEO Service/Aktuell/TMP/Kevin/Unlowdet/gantry"#(2)
    #in_bag_path=os.path.join(path,"gantry")#(1)
    
    #directory for gopro .mp4-files
    gopro_downsample_path="K:/EKB/GEO Service/Aktuell/TMP/Kevin/Unlowdet/clips_sd"#(2)
    #gopro_downsample_path=os.path.join(path,"clips_sd")#(1)
    
    #directory for aris output
    #out_dir_path="K:/EKB/GEO Service/Aktuell/TMP/Kevin/Unlowdet/aris_extract_full"
    out_dir_path=os.path.join(path,"aris_extract_full")
    
    #directory for gantry output
    #out_bag_path="K:/EKB/GEO Service/Aktuell/TMP/Kevin/Unlowdet/gantry_extract_full"
    out_bag_path=os.path.join(path,"gantry_extract_full")
    

    
    generate_json_dictionary(in_file_path,out_dir_path,in_bag_path,out_bag_path,gopro_downsample_path)
    
    
    #listoffiles=os.listdir(in_file_path)
    #searches Input-directory for *.aris files and generates filelist for loop
    listoffiles=[file for file in os.listdir(in_file_path) if file.split(".")[-1]=="aris"]
    
    for i,in_files in enumerate(listoffiles):
            
        
        try:
            #in_file=
            #in_file_path = sys.argv[1]
            #out_dir_path = sys.argv[2]
            #in_file_path = 'ARIS_2023_09_20/2023-09-20_145625.aris'
            #out_dir_path = 'matched_data/data/test/'
            
            in_file = open(os.path.join(in_file_path, in_files), 'rb')
            filename = os.path.splitext(os.path.basename(in_files))[0]
            
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
            print(f'{filename} ({i+1}/{len(listoffiles)})')
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
                