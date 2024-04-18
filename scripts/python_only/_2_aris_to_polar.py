#!/usr/bin/env python
import sys
import os
import getpass
import numpy as np
import pandas as pd
import cv2
from tqdm import tqdm
from json import loads
from json import dumps

from aris_definitions import (
    get_beamcount_from_pingmode,
    BeamWidthsAris3000_64,
    BeamWidthsAris3000_128,
    FrameHeaderFields,
)


def usage():
    print(f"{sys.argv[0]} <input-folder> <output-folder> [frame-metadata-csv]")


def paint_pixel_antialiased(image: np.ndarray, x: float, y: float, value: int):
    int_x, frac_x = int(x), x - int(x)
    int_y, frac_y = int(y), y - int(y)

    # Calculate the contribution for each of the four surrounding pixels
    contributions = [
        ((1 - frac_x) * (1 - frac_y), (int_x, int_y)),
        ((frac_x) * (1 - frac_y), (int_x + 1, int_y)),
        ((1 - frac_x) * (frac_y), (int_x, int_y + 1)),
        ((frac_x) * (frac_y), (int_x + 1, int_y + 1)),
    ]

    for contribution, (px, py) in contributions:
        if 0 <= px < image.shape[1] and 0 <= py < image.shape[0]:
            image[py, px] += value * contribution


def aris_frame_to_polar(
    frame, frame_idx, metadata, norm_intensity=False, antialiasing=False, scale=2.0
):
    frame_meta = metadata.iloc[frame_idx]
    pingmode = frame_meta[FrameHeaderFields.ping_mode]
    bin_count = int(frame_meta[FrameHeaderFields.samples_per_beam])
    beam_count = get_beamcount_from_pingmode(pingmode)

    if beam_count == 64:
        beam_angles = np.array(BeamWidthsAris3000_64)
    elif beam_count == 128:
        beam_angles = np.array(BeamWidthsAris3000_128)
    else:
        raise ValueError(f"Unexpected pingmode {pingmode}")

    window_start = frame_meta[FrameHeaderFields.window_start]
    window_length = frame_meta[FrameHeaderFields.window_length]
    bins_per_meter = bin_count / window_length
    # beam_widths = beam_angles[:, 2] - beam_angles[:, 1]

    # The sonar only takes measurements starting from a certain distance
    min_radius = bins_per_meter * window_start

    # The leftmost edge will be lower than the center of the closest profile
    distance_bottom_left = np.sin(np.deg2rad(beam_angles[-1, 1] + 90)) * min_radius

    # We need a few additional pixel to include the corners of the bottom profile
    bottom_profile_offset = int(abs(min_radius - distance_bottom_left))

    # The top profile is further away from the origin than the image bottom
    last_profile_distance = int(bin_count + bottom_profile_offset + min_radius)
    beam_range = beam_angles[-1, 2] - beam_angles[0, 1]
    frame_half_w = int(
        np.ceil(last_profile_distance * np.tan(np.deg2rad(beam_range / 2))) * scale
    )
    frame_h = int((bin_count + bottom_profile_offset) * scale)
    polar_frame = np.zeros((frame_h, frame_half_w * 2), dtype=np.int32)

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
                x = np.cos(np.deg2rad(angle + 90)) * radius + frame_half_w
                y = (
                    frame_h
                    - max(0, np.sin(np.deg2rad(angle + 90)) * radius - min_radius)
                    - 1
                )

                if antialiasing:
                    paint_pixel_antialiased(polar_frame, x, y, intensity)
                else:
                    polar_frame[int(round(y)), int(round(x))] = intensity

    # Normalize the image to the 0-255 range (required from antialiased pixel painting)
    cv2.normalize(polar_frame, polar_frame, 0, 255, cv2.NORM_MINMAX)
    polar_frame = np.round(polar_frame).astype(np.uint8)
    return polar_frame
    # In ARIS frames, beams are ordered right to left
    # return cv2.flip(polar_frame, 1)

#yet another method to create polar images.
#In contrast to aris_frame_to_polar this method creates an image based on a given resolution. As a results a pixel in the original data corresponds to a polygon area in this image.
def aris_frame_to_polar2(frame, frame_idx, metadata,frame_res = 1000):
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
        
    speed_of_sound = frame_meta['SoundSpeed']
    sample_start_delay = frame_meta['SampleStartDelay']
    sample_period = frame_meta['SamplePeriod']
    
    window_start = sample_start_delay * 1e-6 * speed_of_sound / 2
    window_length = sample_period * (bin_count+1) * 1e-6 * speed_of_sound / 2
    range_start = window_start
    range_end = window_start + window_length
    bin_length = sample_period * 1e-6 * speed_of_sound / 2
    
    beam_range = beam_angles[-1][2] - beam_angles[0][1]
    frame_half_w = range_end * np.tan(np.deg2rad(beam_range / 2))
    
    0 #pixel/m
    frame_l_n = np.int(np.ceil(range_end * frame_res))
    frame_w_n = np.int(np.ceil(frame_half_w * 2 * frame_res))
    
    polar_frame = np.zeros((frame_l_n, frame_w_n), dtype=np.uint8)
    
    #subpixel precision
    center_img_ref_frame = np.array([frame_w_n/2,frame_l_n])
    for beam_idx in range(beam_count):
        start_angle = -beam_angles[beam_idx][1]
        center_angle = -beam_angles[beam_idx][0]
        end_angle = -beam_angles[beam_idx][2]
        
        for bin_idx in range(bin_count):
            intensity = frame[bin_idx, beam_idx]
            bin_start = window_start + sample_period * bin_idx * 1e-6 * speed_of_sound  / 2
            bin_end = window_start + sample_period * (bin_idx+1) * 1e-6 * speed_of_sound  / 2
            
            top_left_img_ref_frame      = np.array([bin_end * np.cos(np.deg2rad(start_angle+90)) * frame_res, -bin_end * np.sin(np.deg2rad(start_angle+90)) * frame_res]) + center_img_ref_frame
            top_center_img_ref_frame    = np.array([bin_end * np.cos(np.deg2rad(center_angle+90)) * frame_res, -bin_end * np.sin(np.deg2rad(center_angle+90)) * frame_res]) + center_img_ref_frame
            top_right_img_ref_frame     = np.array([bin_end * np.cos(np.deg2rad(end_angle+90)) * frame_res, -bin_end * np.sin(np.deg2rad(end_angle+90)) * frame_res]) + center_img_ref_frame
            bottom_right_img_ref_frame  = np.array([bin_start * np.cos(np.deg2rad(end_angle+90)) * frame_res, -bin_start * np.sin(np.deg2rad(end_angle+90)) * frame_res]) + center_img_ref_frame
            bottom_center_img_ref_frame = np.array([bin_start * np.cos(np.deg2rad(center_angle+90)) * frame_res, -bin_start * np.sin(np.deg2rad(center_angle+90)) * frame_res]) + center_img_ref_frame
            bottom_left_img_ref_frame   = np.array([bin_start * np.cos(np.deg2rad(start_angle+90)) * frame_res, -bin_start * np.sin(np.deg2rad(start_angle+90)) * frame_res]) + center_img_ref_frame
            
            top_left_img_ref_frame[0] = int(np.floor(top_left_img_ref_frame[0]))
            top_left_img_ref_frame[1] = int(np.ceil(top_left_img_ref_frame[1]))
            top_center_img_ref_frame[0] = int(np.round(top_center_img_ref_frame[0]))
            top_center_img_ref_frame[1] = int(np.ceil(top_center_img_ref_frame[1]))
            top_right_img_ref_frame[0] = int(np.ceil(top_right_img_ref_frame[0]))
            top_right_img_ref_frame[1] = int(np.ceil(top_right_img_ref_frame[1]))
            bottom_right_img_ref_frame[0] = int(np.ceil(bottom_right_img_ref_frame[0]))
            bottom_right_img_ref_frame[1] = int(np.floor(bottom_right_img_ref_frame[1]))
            bottom_center_img_ref_frame[0] = int(np.round(bottom_center_img_ref_frame[0]))
            bottom_center_img_ref_frame[1] = int(np.floor(bottom_center_img_ref_frame[1]))
            bottom_left_img_ref_frame[0] = int(np.floor(bottom_left_img_ref_frame[0]))
            bottom_left_img_ref_frame[1] = int(np.floor(bottom_left_img_ref_frame[1]))
            
            points=np.array([top_left_img_ref_frame,top_center_img_ref_frame,top_right_img_ref_frame,bottom_right_img_ref_frame,bottom_center_img_ref_frame,bottom_left_img_ref_frame])

            cv2.fillPoly(polar_frame, [points.astype(np.int32)], int(intensity))

    return cv2.flip(polar_frame, 1)

def aris_frame_to_polar_csv(frame, frame_idx, metadata):
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
        
    speed_of_sound = frame_meta['SoundSpeed']
    sample_start_delay = frame_meta['SampleStartDelay']
    sample_period = frame_meta['SamplePeriod']
    
    window_start = sample_start_delay * 1e-6 * speed_of_sound / 2
    window_length = sample_period * (bin_count+1) * 1e-6 * speed_of_sound / 2
    range_start = window_start
    range_end = window_start + window_length
    bin_length = sample_period * 1e-6 * speed_of_sound / 2
    
    beam_range = beam_angles[-1][2] - beam_angles[0][1]
    
    df = pd.DataFrame(columns=['beam_idx','sample_idx','sample_start (m)','sample_end (m)','center_angle (deg)','left_angle(deg)','right_angle(deg)','intensity (dB)'])

    #subpixel precision

    for beam_idx in range(beam_count):
        start_angle = beam_angles[beam_idx][1]
        center_angle = beam_angles[beam_idx][0]
        end_angle = beam_angles[beam_idx][2]
        
        for bin_idx in range(bin_count):
            intensity = frame[bin_idx, beam_idx]
            bin_start = window_start + sample_period * bin_idx * 1e-6 * speed_of_sound  / 2
            bin_end = window_start + sample_period * (bin_idx+1) * 1e-6 * speed_of_sound  / 2
            new_row = {'beam_idx' : beam_idx, 'sample_idx' : bin_idx, 'sample_start (m)' : bin_start, 'sample_end (m)' : bin_end, 'center_angle (deg)' : center_angle, 'left_angle(deg)' : start_angle, 'right_angle(deg)': end_angle,'intensity (dB)' : (float(intensity)*80.0/255.0) }
            df=df.append(new_row,ignore_index=True)
        
    # In ARIS frames, beams are ordered right to left
    return df

def read_json_dict():
    if os.path.isfile('.arisparameter'+getpass.getuser()) == True:
        with open('.arisparameter'+getpass.getuser(), 'r') as defaultlesen2:
            jsondict = loads(defaultlesen2.read())
        defaultlesen2.closed
        in_dir_path=jsondict["arisinput"]
        out_dir_path=jsondict["aris_to_polar_out"]
    else:
        in_dir_path=""
        out_dir_path=""
    return in_dir_path,out_dir_path

if __name__ == "__main__":
    # if not 3 <= len(sys.argv) < 4:
    #     usage()
    #     raise RuntimeError("Wrong number of arguments")
    
    how_polar=1
    #Kommando-Zeile für welches Verfhren
    print("Choose aris-to-polar method: (default=aris-to-polar")
    print("(1) aris-to-polar")
    print("(2) aris-to-polar2")
    print("(3) aris-to-polar-csv")
    try:
        how_polar = int(input('Input:'))
        if how_polar not in [1,2,3]:
            raise ValueError("invalid number, choosing 1 instead")
    except:
        raise ValueError("not a number, choosing 1 instead")

    in_dir_path,out_dir_path=read_json_dict()
    listoffiles=[file for file in os.listdir(in_dir_path) if file.split(".")[-1]=="aris"]
    
    for i,in_files in enumerate(listoffiles):

        if in_files.endswith("/"):
            in_files = in_files[:-1]
        basename = os.path.basename(in_files)[:-5]
    
        if os.path.exists(os.path.join(in_dir_path,"aris_extract_full",basename)):
            frames_meta_file = os.path.join(in_dir_path,"aris_extract_full",basename, f"{basename}_frames.csv")
        else:
            raise ValueError(f'corresponding meta-file to {basename} not found')
    
        os.makedirs(out_dir_path, exist_ok=True)
    
        with open(frames_meta_file, "r") as frames_meta_file:
            metadata = pd.read_csv(frames_meta_file)
    
            for f in tqdm(sorted(os.listdir(os.path.join(in_dir_path,"aris_extract_full",basename)))):
                if not f.lower().endswith(".pgm"):
                    continue
    
                frame_name = f
                if "_" in frame_name:
                    # Assume the actual frame identifier comes after an underscore (if present)
                    frame_name = f[f.index("_") + 1 :]
    
                frame_idx = int(os.path.splitext(frame_name)[0])
                frame = cv2.imread(os.path.join(in_dir_path,"aris_extract_full",basename, f), cv2.IMREAD_UNCHANGED)
                if how_polar==1:
                    polar = aris_frame_to_polar(frame, frame_idx, metadata)
                elif how_polar==2:
                    polar = aris_frame_to_polar2(frame, frame_idx, metadata)
                elif how_polar==3:
                    polar = aris_frame_to_polar_csv(frame, frame_idx, metadata)
                
                outfile_name = os.path.splitext(os.path.basename(f))[0]
                png_compression_level = 9
    
                cv2.imwrite(
                    os.path.join(out_dir_path, outfile_name + ".png"),
                    polar,
                    [cv2.IMWRITE_PNG_COMPRESSION, png_compression_level],
                )
