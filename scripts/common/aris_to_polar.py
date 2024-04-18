#!/usr/bin/env python
import sys
import os
import numpy as np
import pandas as pd
import cv2
from tqdm import tqdm

from dataset.scripts.src.config import get_config
from .aris_definitions import (
    get_beamcount_from_pingmode,
    BeamWidthsAris3000_64,
    BeamWidthsAris3000_128,
    FrameHeaderFields,
)


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
    frame_l_n = int(np.ceil(range_end * frame_res))
    frame_w_n = int(np.ceil(frame_half_w * 2 * frame_res))
    
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
    
    df = pd.DataFrame(columns=['beam_idx',
        'sample_idx',
        'sample_start (m)',
        'sample_end (m)',
        'center_angle (deg)',
        'left_angle(deg)',
        'right_angle(deg)',
        'intensity (dB)'
    ])

    for beam_idx in range(beam_count):
        start_angle = beam_angles[beam_idx][1]
        center_angle = beam_angles[beam_idx][0]
        end_angle = beam_angles[beam_idx][2]
        
        for bin_idx in range(bin_count):
            intensity = frame[bin_idx, beam_idx]
            bin_start = window_start + sample_period * bin_idx * 1e-6 * speed_of_sound  / 2
            bin_end = window_start + sample_period * (bin_idx+1) * 1e-6 * speed_of_sound  / 2
            
            new_row = {
                'beam_idx' : beam_idx,
                'sample_idx' : bin_idx,
                'sample_start (m)' : bin_start,
                'sample_end (m)' : bin_end,
                'center_angle (deg)' : center_angle,
                'left_angle(deg)' : start_angle,
                'right_angle(deg)': end_angle,
                'intensity (dB)' : float(intensity) * 80.0/255.0
            }

            df=df.append(new_row,ignore_index=True)
    
    return df


if __name__ == "__main__":
    config = get_config()

    input_path = config["aris_extract"]
    methods = config.get("aris_to_polar_method", "polar2+csv").split('+')
    png_compression_level = config.get("aris_to_polar_png_compression", 9)

    both_polars = "polar" in methods and "polar2" in methods
    recordings = sorted([x for x in os.listdir(input_path) if os.path.isdir(x)])

    for rec_name in tqdm(recordings):
        if rec_name.endswith("/"):
            rec_name = rec_name[:-1]
        
        recording_path = os.path.join(input_path, rec_name)
        frames_meta_file = os.path.join(recording_path, f"{rec_name}_frames.csv")
        out_path = os.path.join(recording_path, "polar")
        os.makedirs(out_path, exist_ok=True)

        with open(frames_meta_file, "r") as frames_meta_file:
            metadata = pd.read_csv(frames_meta_file)

            for f in tqdm(sorted(os.listdir(recording_path))):
                if not f.lower().endswith(".pgm"):
                    continue

                frame_name = f
                if "_" in frame_name:
                    # Assume the actual frame identifier comes after an underscore (if present)
                    frame_name = f[f.index("_") + 1 :]

                frame_idx = int(os.path.splitext(frame_name)[0])
                frame = cv2.imread(os.path.join(recording_path, f), cv2.IMREAD_UNCHANGED)
                polar = aris_frame_to_polar(frame, frame_idx, metadata)
                
                basename = os.path.splitext(os.path.basename(f))[0]
                frame_out_path = os.path.join(out_path, basename)
                
                if both_polars:
                    polar2_out_path = os.path.join(out_path + '2', basename)
                else:
                    polar2_out_path = frame_out_path

                # Run the conversions
                for conversion in methods:
                    if conversion == "polar1":
                        polar_img = aris_frame_to_polar(frame, frame_idx, metadata)
                        cv2.imwrite(
                            frame_out_path + '.png', 
                            polar_img, 
                            [cv2.IMWRITE_PNG_COMPRESSION, png_compression_level]
                        )
                    elif conversion == "polar2":
                        polar_img = aris_frame_to_polar2(frame, frame_idx, metadata)
                        cv2.imwrite(
                            polar2_out_path + '.png', 
                            polar_img, 
                            [cv2.IMWRITE_PNG_COMPRESSION, png_compression_level]
                        )
                    elif conversion == "csv":
                        polar_df = aris_frame_to_polar_csv(frame, frame_idx, metadata)
                        polar_df.to_csv(frame_out_path + '.csv', header=True, index=False)
                    else:
                        raise ValueError(f"Invalid method {conversion}")