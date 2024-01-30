# Recording Setup
The UXO targets were recorded with two sensors mounted on a pan tilt unit (PTU) attached to a gantry crane. In particular, the following hardware was used:
- SoundMetrics ARIS Explorer 3000 MBES (proprietary format)
- SoundMetrics ARIS Rotator AR3 (part of the ARIS recordings' metadata)
- GoPro Hero 8 (5.3k h264 MPEG-4 files including audio)
- Gantry crane (rosbags)

While the gantry crane could be controlled and recorded from ROS, we decided to use the ARIS' software in order to capture the 'most raw' data possible (including all the meta data). The GoPro was attached to the top right corner of the ARIS and recorded on its own. 


# What was recorded
The recordings cover 5 different objects of various sizes and state of degradation:
**TODO more info from Oli**
- 100lbs aircraft bomb
- heavily rusted and deformed incindiary grenade
- artillery shell in very good condition
- intact mortar shell
- test cylinder

Every time the object was exchanged, we followed the following procedure:
1. first the object was placed on a pedestal in the basin
2. using the crane and the center of the ARIS, we visually positioned the ARIS as close as possible in front of and above the object
3. we recorded this position *of the gantry crane*, i.e. the object's origin is still half its width and height off

Most of the recordings collected consist of the gantry crane following a pre-programmed half-orbit trajectory at different depths / elevations. The ARIS PTU was controlled manually to keep the object in frame. The GoPro recorded continuously.

In addition, between 150 and 300 pictures were taken for photogrammetry of every objects except the test cylinder.
**TODO camera type**


# How the dataset was prepared
To establish a groundtruth, we reconstructed a textured 3D model for every object except the test cylinder using Agisoft Metashape. The resulting models and textures can be found in *3d_objects*.

Reducing the dataset down to the (for us) relevant parts proved more challenging, largely due to some oversights during the recording. For one, the GoPro does not have a synchronized timestamp, so the only way to match the footage to the ARIS data was by matching the camera motion. In addition, the GoPro's recording and file naming scheme (combined with some dropouts due to low battery) made it difficult to find the corresponding clip for every recording. Calculating the optical flow has helped in these regards.

In the end, the data from each sensor was prepared separately and then finally matched together. For this reason, there are 3 versions of this dataset available:
- raw: contains the files as they were recorded
- intermediate: contains the output of all preprocessing steps, but before the final extraction
- processed: contains one datapoint for every ARIS frame, i.e. one ARIS frame, one GoPro frame, one gantry crane position and the corresponding metadata

The motion onset identified in the ARIS data was used to trim the other sensors after matching. In general, decisions were always made based on and in favor of the ARIS data.
**TODO gantry interpolation**


# Processing the data
To prepare the data from the raw recordings, simply execute the accompanying bash scripts in the indicated order.

**ARIS**
- *aris_1_extract_all.bash*: extracts the frames and metadata from the ARIS' proprietary format.
- *aris_2_to_polar.bash*: (optional) convert the raw frames to polar coordinates. Be aware that while this makes them easier to interpret, some data loss is incurred.
- *aris_3_calc_all_optical_flow.bash*: calculate the optical flow magnitudes for every recording.
- *aris_4_find_offsets.bash*: a graphical tool to manually find and mark the motion onset in every recording.

**Gantry Crane**
- *gantry_1_extract.bash*: exports each trajectory's timestamps and xyz position data.
- *gantry_2_find_offsets.bash*: automatically finds the motion onsets (first change in xyz).

**GoPro**
- *gopro_1_cut_day1.bash*: cuts the gopro footage from day 1 into individual clips. The cut points were manually extracted from the audio track.
- *gopro_1_cut_day2.bash*: cuts the gopro footage from day 2 into individual clips. The cut points were manually extracted from the audio track.
- *gopro_2_downsample_all.bash*: downsamples the unwieldy 5.3k footage to a more manageable size (check script for details).
- *gopro_3_calc_all_optical_flow.bash*: calculates the optical flow magnitudes for every clip.
- *gopro_4_extract_metadata_simple*: extracts the creation time from every GoPro recording. This proved to be unhelpful.

**Matching**
- *match_recordings.bash*: a GUI that allows synchronized playback of the different recordings and adjust the offsets between them. The result is a csv containing matching recordings and offsets.

**Export**
**TODO script**


# Lessons Learned
Unfortunately, this dataset was recorded with an ad-hoc setup, resulting in several difficulties down the line. In particular, having an independent recording setup for every sensor caused some major trouble and headaches down the line so that almost any amount of additional integration effort would have been warranted. Furthermore, the GoPro proved to be a suboptimal choice, as it was not possible to easily monitor it from outside the basin, resulting in several lost clips due to low battery and random recording stops. 


