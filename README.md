# Recording Setup
The UXO targets were recorded with two sensors mounted on a pan tilt unit (PTU) attached to a gantry crane. In particular, the following hardware was used:
- SoundMetrics ARIS Explorer 3000 MBES (proprietary format)
- SoundMetrics ARIS Rotator AR3 (part of the ARIS recordings' metadata)
- GoPro Hero 8 (5.3k h264 MPEG-4 files including audio)
- Gantry crane (rosbags)

While the gantry crane could be controlled and recorded from ROS, we decided to use the ARIS' software in order to capture the 'most raw' data possible (including all the meta data). The GoPro was attached to the top right corner of the ARIS and recorded on its own. 


# Dataset overview

## Directory structure
- *3d_models*: the photogrammetry 3d models of the target objects.
- *scripts*: contains the scripts used for processing and extracting the data.
- *recordings*: contains one folder per recordings. Each recording folder is named by date and local time.

## Recording contents
- *aris_polar*: directory containing sonar images rendered in polar coordinates.
- *aris_raw*: directory containing sonar images as recorded by the sonar.
- *gopro*: directory containing gopro frames matching the sonar images. May be missing for some recordings. Not every sonar frame will have a gopro frame.
- *aris_file_meta.yaml*: meta data recorded by the sonar for each recording, see [aris-file-sdk](https://github.com/SoundMetrics/aris-file-sdk).
- *aris_frame_meta.csv*: meta data recorded by the sonar for each frame, see [aris-file-sdk](https://github.com/SoundMetrics/aris-file-sdk).
- *gantry.csv*: positions of the gantry crane. The positions have been interpolated to the sonar frames' timestamps.
- *notes.txt*: additional notes taken for the recordings.

## Viewing recordings
The exported data uses simple, well-established formats, namely .pgm, .jpg, .csv, .yaml and .txt. For convenience, we also provide a script that loads an exported recording and allows to step through datapoints in a synchronized fashion using the arrow keys. To view a recording, use the following command:

```bash
bash scripts/view_recording.bash data_export/recordings/<recording-folder>
```


# What was recorded
The recordings cover 5 different objects of various sizes and state of degradation:

## Targets 

### 100lbs aircraft bomb
- "Standardbombe GP 100 lbs M 30"
- Heavily rusted
- Used since WW2
- Length 737 mm
- Diameter 208 mm
- Total weight 51 kg
- Filling weight 25 kg

### Incindiary grenade
- "Flüssigkeitsbrandbombe INC 30 lbs"
- Heavily rusted and deformed
- Used in WW2
- Length 442 mm
- Diameter 127 mm
- Total weight 11.3 kg
- Filling weight 3.9 kg

### Mortar shell
- "120 mm Mörserpatrone DM 81"
- Good condition
- Used after WW2
- Length 580 mm
- Diameter 120 mm
- Total weight 12.8 kg
- Filling weight 2.25 kg

### Artillery shell
- "10.5 cm Sprenggranate L/4,4"
- Good condition
- Used in WW2
- Length 365 mm
- Diameter 105 mm
- Total weight 15.1 kg
- Filling weight 1.27 kg

### Test cylinder
- Length 530 mm
- Diameter 220 mm
- Wall thickness


## Recording procedure

Every time the object was exchanged, we followed the following procedure:
1. first the object was placed in the basin, usually on a pedestal
2. using the crane and the center of the ARIS, we visually positioned the ARIS as close as possible in front of and above the object (see [[#Object Origins]] below)
3. from the pose of the gantry crane in these positions we could estimate the objects' positions

Most of the recordings collected consist of the gantry crane following a pre-programmed half-orbit trajectory at different depths / elevations. The ARIS PTU was controlled manually to keep the object in frame. The GoPro recorded continuously.

In addition, between 150 and 300 pictures were taken for photogrammetry of every objects except the test cylinder. The camera details are as follows:
- Model: Canon EOS 80D
- Exposure time: 1/160 s (manual)
- Aperture: F16
- ISO: 800
- Focal length: 18mm


# Object origins

## 100lbs aircraft bomb
- Front point (object tip)
    - x: 1.254022
    - y: 1.190926
    - z: -1.151828

- Top point 
    - x: 1.251079
    - y: 1.418704
    - z: -0.96597

**Object point:** (1.251079, 1.418704, -1.151828)

## Mortar shell
- Front point (object tip)
    - x: 1.6512390000000001
    - y: 1.2631050000000001
    - z: -1.1809090000000002
- Top point 
    - x: 1.263516
    - y: 1.252357
    - z: -1.0917249999999998

**Object point:** (1.2351, 1.25, -1.192784)

## Incindiary 
- Front point (object tip)
    - x: 1.6446880000000001
    - y: 1.235233
    - z: -1.192784
- Top point
    - x: 1.2350999999999999
    - y: 1.25
    - z: -1.019191

**Object point:** (1.2351, 1.25, -1.192784)

## Test cylinder
- Front point (object tip)
    - x: 1.674253
    - y: 1.122848
    - z: -1.123439

- Top point
    - x: 1.277832
    - y: 1.225541
    - z: -0.948813

**Object point:** (1.277832, 1.225541, -1.123439)

## 100lbs bomb (on ground)
- Top point
    - x: 1.174003
    - y: 1.053536
    - z: -1.497432

**Object point:** (1.174003, 1.053536, -1903.1)

> Note: the portal crane could not reach low enough to estimate the front point. The height was thus estimated from the object diameter, the known depth of the floor, and the PTU mounting dimensions.


# How the dataset was prepared
To establish a groundtruth, we reconstructed a textured 3D model for every object except the test cylinder using Agisoft Metashape. The resulting models and textures can be found in *3d_objects*.

Reducing the dataset down to the (for us) relevant parts proved more challenging, largely due to some oversights during the recording. For one, the GoPro does not have a synchronized timestamp, so the only way to match the footage to the ARIS data was by matching the camera motion. In addition, the GoPro's recording and file naming scheme (combined with some dropouts due to low battery) made it difficult to find the corresponding clip for every recording. Calculating the optical flow has helped in these regards.

In the end, the data from each sensor was prepared separately and then finally matched together. For this reason, there are 3 versions of this dataset available:
- raw: contains the files as they were recorded
- intermediate: contains the output of all preprocessing steps, but before the final extraction
- processed: contains one datapoint for every ARIS frame, i.e. one ARIS frame, one GoPro frame, one gantry crane position and the corresponding metadata

The motion onset identified in the ARIS data was used to trim the other sensors after matching. In general, decisions were always made based on and in favor of the ARIS data.


# Processing the raw data
To prepare the data from the raw recordings, simply execute the accompanying prepocessing and export scripts. Every script contains a short documentation and an example for how it was called to process the data. The called python scripts may have additional command line arguments that are not exposed by the bash scripts.

## Dependencies
The underlying scripts are python 3 files and use the following dependencies. Check the scripts to find out who needs what specifically.
- numpy
- pandas
- cv2
- yaml
- csv
- matplotlib
- rosbag
- ffmpeg
- pytz
- PyQt5


## Scripts

### Preprocessing
- *preprocess_aris_1_extract_all.bash*: extracts the frames and metadata from the ARIS' proprietary format.
- *preprocess_aris_2_to_polar.bash*: (optional) convert the raw frames to polar coordinates. Be aware that while this makes them easier to interpret, some data loss is incurred.
- *preprocess_aris_3_calc_all_optical_flow.bash*: calculate the optical flow magnitudes for every recording.
- *preprocess_aris_4_find_offsets.bash*: a graphical tool to manually find and mark the motion onset in every recording.

- *preprocess_gantry_1_extract.bash*: exports each trajectory's timestamps and xyz position data.
- *preprocess_gantry_2_find_offsets.bash*: automatically finds the motion onsets (first change in xyz).

- *preprocess_gopro_1_cut_day1.bash*: cuts the gopro footage from day 1 into individual clips. The cut points were manually extracted from the audio track.
- *preprocess_gopro_1_cut_day2.bash*: cuts the gopro footage from day 2 into individual clips. The cut points were manually extracted from the audio track.
- *preprocess_gopro_2_downsample_all.bash*: downsamples the unwieldy 5.3k footage to a more manageable size (check script for details).
- *preprocess_gopro_3_calc_all_optical_flow.bash*: calculates the optical flow magnitudes for every clip.

### Dataset assembly
- *dataset_match_recordings.bash*: a GUI that allows synchronized playback of the different recordings and adjust the offsets between them. The result is a csv containing matching recordings and offsets.
- *dataset_export.bash*: copies and extracts the processed data into the final dataset.

### Viewing
- *view_recording.bash*: simple viewer for stepping through an exported recording.



# Lessons Learned
Unfortunately, this dataset was recorded with an ad-hoc setup, resulting in several difficulties down the line. In particular, having an independent recording setup for every sensor caused some major trouble and headaches down the line so that almost any amount of additional integration effort would have been warranted. Furthermore, the GoPro proved to be a suboptimal choice, as it was not possible to easily monitor it from outside the basin, resulting in several lost clips due to low battery and random recording stops. 
