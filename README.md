# About
We present a dataset for acoustic and optical sensing of unexploded ordnance (UXO) underwater.

UXO in the sea pose an environmental problem and a challenge for the growing offshore economy. It is best practice to perform the recovery of ammunition without explosions to protect anthropogenic structures and marine mammals. During explosive ordnance disposal (EOD), experts often rely on optical images. However, visibility underwater may be limited in harbor areas, after storm events or in waters with very mobile sediments. Thus, visual inspection is not always possible. EOD experts therefore use high-frequency sonars with large vertical apertures like the ARIS Explorer 3000 for acoustic imaging. While efforts have been made to use the available information for 3D reconstruction, existing solutions can be limited to predefined motion patterns. 

The topic is inherently sensitive, and most of the data is acquired by and for private companies and not made available to the public, which impedes research in this area. Additionally, in-situ data often lacks sufficient pose information. To facilitate further research, we created a validation dataset that was recorded in a controlled experimental environment. It has the following properties:

- Over 100 recordings of 3 different UXO.
- More than 92000 matched and annotated imaging sonar and camera frames.
- UXO ground truths in the form of photogrammetric 3D models.
- Precise position and attitude sensor data with respect to the targets.
- Realistic motion trajectories achievable in non-experimental environments.

This dataset allows quantitative analysis with different algorithms. 3D models and trajectories can be compared against each other to evaluate different solutions.


# Viewing the data
The exported data uses simple, well-established formats, namely .pgm, .jpg, .csv, .yaml and .txt. For convenience, we provide a script that loads an exported recording and allows to step through datapoints in a synchronized fashion using the arrow keys. To view a recording, use the following command:

```bash
bash scripts/view_recording.bash data_export/recordings/<target_type>/<recording-folder>
```


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
- *recordings*: contains one folder per target type, and then one folder per recording named by date and local time.

## Recording contents
- *aris_polar*: directory containing sonar images rendered in polar coordinates.
- *aris_raw*: directory containing sonar images as recorded by the sonar.
- *gopro*: directory containing gopro frames matching the sonar images. May be missing for some recordings. Not every sonar frame will have a gopro frame.
- *aris_file_meta.yaml*: meta data recorded by the sonar for each recording, see [aris-file-sdk](https://github.com/SoundMetrics/aris-file-sdk).
- *aris_frame_meta.csv*: meta data recorded by the sonar for each frame, see [aris-file-sdk](https://github.com/SoundMetrics/aris-file-sdk).
- *gantry.csv*: positions of the gantry crane. The positions have been interpolated to the sonar frames' timestamps.
- *notes.txt*: additional notes taken for the recording, e.g. PTU tilt, target or trajectory type.


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


# Transforms
The acoustic origin of the ARIS lies 2.5cm forward from the rearmost surface. The beam forming center, i.e. the point where all beams cross in the azimuth direction, has about 5cm travel depending on the focus, but can be estimated as the center of the lens housing. For our transforms below we assume that the sonar's acoustic origin coincides with the center of rotation. 

## Crane -> ARIS
- Offsets in gantry crane frame, i.e. the wall behind the UXO is in the Y direction and Z is pointing upwards.
- dx = 0
- dy = 174
- dz = -338

## GoPro
- All offsets in ARIS acoustic frame (analog conventional optical frame of cameras)
- x = right
- y = down
- z = forward (optical axis)

### ARIS -> GoPro Lens Front
- (assuming no pitch between GoPro and ARIS, see below)
- dx = +3.5
- dy = -154.5
- dz = +167

### ARIS -> GoPro Mounting Hole
- Threaded hole on top of ARIS on its right "ear" (-x in ARIS frame)
- dx = +23
- dy = -105.5
- dz = +126.5

### GoPro Mounting Hole -> GoPro Lens Front
- Center of the glass surface protecting the GoPro lens
- GoPro was mounted with a slight angle of 3-4° around a point at +0/-7.5/+21.25 from the mounting hole
- dx = -19.5
- dy = -49
- dz = +40.5

## UXO
- *Measured*: point recorded by visually aligning crane with center of UXO
- *Corrected*: measured point with Crane->ARIS offset applied, i.e. what the crane would have measured if we aligned it without the ARIS
- Units in m

### 100lbs
- Measured: (1.251079, 1.190926, -1.151828)
- Corrected: (1.251079,  1.592704, -1.489828)

### Mortar Shell
- Measured: (1.263516, 1.2631, -1.18091)
- Corrected: (1.263516, 1.4371, -1.51891)

### Incendiary
- Measured: (1.2351, 1.235233, -1.192784)
- Corrected: (1.2351, 1.409233, -1.530784)

### Test Cylinder
- Measured: (1.277832, 1.225541, -1.123439)
- Corrected: (1.277832, 1.399541, -1.461439)

### 100lbs (floor)
- Measured: (1.174003, 1.053536, *?*)
- Corrected: (1.174003, 1.227536, -2.236)
- Note: the portal crane could not reach low enough to estimate the Z offset; the Z offset was thus estimated from the known depth of the floor (-2.34m) and the object diameter (208mm).


# How the dataset was prepared
To establish a groundtruth, we reconstructed a textured 3D model for every object except the test cylinder using Agisoft Metashape. The resulting models and textures can be found in *3d_objects*.

Reducing the dataset down to the (for us) relevant parts proved more challenging, largely due to some oversights during the recording. For one, the GoPro does not have a synchronized timestamp, so the only way to match the footage to the ARIS data was by matching the camera motion. In addition, the GoPro's recording and file naming scheme (combined with some dropouts due to low battery) made it difficult to find the corresponding clip for every recording. Calculating the optical flow has helped in these regards.

In the end, the data from each sensor was prepared separately and then finally matched together. For this reason, there are 3 versions of this dataset available:
- raw: contains the files as they were recorded
- intermediate: contains the output of all preprocessing steps, but before the final extraction
- processed: contains one datapoint for every ARIS frame, i.e. one ARIS frame, one GoPro frame, one gantry crane position and the corresponding metadata

The motion onset identified in the ARIS data was used to trim the other sensors after matching. In general, decisions were always made based on and in favor of the ARIS data.


# Processing the raw data
To prepare the data from the raw recordings, simply execute the accompanying prepocessing and export scripts. To make things easier, all options are documented in and read from the accompanying `config.yaml` file. 

## Dependencies
The underlying scripts are python 3 files and use the following dependencies. Check the scripts to find out who needs what specifically. Since development has moved away from ROS1, we recommend using the excellent [robostack](https://robostack.github.io/) to setup ROS1 environment. Beyond the packages this will install, you should do the following:

```bash
mamba install numpy pandas opencv pyyaml matplotlib ffmpeg pytz pyqt tqdm
pip install rosbag
```

## Scripts

### Preprocessing
- *prep_1_aris_extract.py*: extracts the frames and metadata from the ARIS' proprietary format.
- *prep_2_aris_to_polar.py*: (optional) convert the raw frames to polar coordinates. Be aware that while this makes them easier to interpret, some data loss is incurred.
- *prep_3_aris_calc_optical_flow.py*: calculate the optical flow magnitudes for the sonar recordings.
- *prep_4_aris_find_offsets.py*: a graphical tool to manually find and mark the motion onset in every recording.

- *prep_5_gantry_extract.py*: exports each trajectory's timestamps and xyz position data.
- *prep_6_gantry_find_offsets.py*: automatically finds the motion onsets (first change in xyz).

- *prep_7_gopro_cut.bash*: cuts the gopro footage into individual clips. The cut points were manually extracted from the audio track.
- *prep_8_gopro_downsample.bash*: downsamples the unwieldy 5.3k footage to a more manageable size (check script for details).
- *prep_9_gopro_calc_optical_flow.py*: calculates the optical flow magnitudes for every clip.

- *prep_x_match_recordings.py*: a GUI that allows synchronized playback of the different recordings and adjust the offsets between them. The result is a csv containing matching recordings and offsets.

### Dataset assembly
- *release_1_export.py*: copies and extracts the processed data into the final dataset.
- *release_2_archive.bash*: packs the dataset into several archives.

### Viewing
- *view_recording.py*: simple viewer for synchronously stepping through an exported recording.



# Camera Calibrations

## GoPro Hero 8 (recordings)
```python
# Wide mode -> fisheye calibration
camera_matrix = np.array([[397.77105952, 0.0, 323.01645778],
                          [0.0, 393.9965825, 181.94773453],
                          [0.0, 0.0, 1.0]])
distortion = np.array([[0.22602159], [0.34004099],
                       [-0.39509882], [0.66812696]])
```

## Canon EOS 80D (photogrammetry)
```python
camera_matrix = np.array ([[604.90542407, 0.0, 289.34879658]
                           [0.0, 495.82900424, 241.46109218]
                           [0.0, 0.0, 1.0]])
distortion = np.array([[-0.32364768, 0.51904464, -0.01417983, -0.00342211, -0.53602811]])
```



# Lessons Learned
Unfortunately, this dataset was recorded with an ad-hoc setup, resulting in several difficulties down the line. In particular, having an independent recording setup for every sensor caused some major trouble and headaches down the line so that almost any amount of additional integration effort would have been warranted. Furthermore, the GoPro proved to be a suboptimal choice, as it was not possible to easily monitor it from outside the basin, resulting in several lost clips due to low battery and random recording stops. 
