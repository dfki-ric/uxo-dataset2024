#!/usr/bin/env python
import sys
import os
import csv
import time
import numpy as np
import pandas as pd
import cv2
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# TODO
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


def usage():
    print(f'{sys.argv[0]} <aris-folder> <gantry-folger> <gopro-folder> <output_file.csv>')


class MatchingContext:
    def __init__(self, aris_dir, gantry_file, gopro_file):
        self.aris_basename = os.path.split(aris_dir)[-1]
        self.gantry_basename = os.path.split(gantry_file)[-1]
        self.gopro_basename = os.path.split(gopro_file)[-1]
        
        self.aris_meta = pd.read_csv(os.path.join(aris_dir, self.aris_basename + '_frames.csv'))
        self.aris_frames = sorted(os.path.join(aris_dir, f) for f in os.listdir(aris_dir) if f.lower().endswith('.pgm'))
        self.gantry_data = pd.read_csv(gantry_file)
        self.gopro_clip = cv2.VideoCapture(gopro_file)
        
        # Plot the gantry data - we will only adjust the offset of a marker
        self.gantry_t0_s = self.gantry_data.at[0, 'timestamp_s']
        self.gantry_t0_ns = self.gantry_data.at[0, 'timestamp_ns']
        self.gantry_data['timestamp_s'] -= self.gantry_t0_s
        self.gantry_data['timestamp_ns'] -= self.gantry_t0_ns
        self.gantry_data['t'] = self.gantry_data['timestamp_s'] + self.gantry_data['timestamp_ns'] / 10e9
        
        # Start at -1, this way the first call to tick() will move it to 0
        self.aris_frame_idx = -1
        self.aris_frame_count = len(self.aris_frames)
        self.aris_t0 = self.aris_meta.at[0, 'FrameTime']
        self.aris_plot_img = None
        
        self.gopro_frame_idx = 0
        self.gopro_offset = 0
        self.gopro_frame = None
        
        self.gantry_offset = 0.
        
        self.reload = True
        
    def tick(self):
        self.aris_frame_idx = (self.aris_frame_idx + 1) % self.aris_frame_count
        
    def get_aris_frame(self):
        # FrameTime = time of recording on PC (ms since 1970)
        # sonarTimeStamp = time of recording on sonar (ms since 1970), not sure if synchronized to PC time
        timestamp = self.aris_meta.at[self.aris_frame_idx, 'FrameTime'] - self.aris_t0
        frame = cv2.imread(self.aris_frames[self.aris_frame_idx])
        return frame, timestamp
    
    def get_gopro_frame(self, aris_frametime):
        fps = self.gopro_clip.get(cv2.CAP_PROP_FPS)
        new_timepos = aris_frametime + self.gopro_offset
        new_frame_idx = int(new_timepos / 1000 // fps)
        
        if new_frame_idx != self.gopro_frame_idx:
            self.gopro_frame_idx = new_frame_idx
            self.gopro_clip.set(cv2.CAP_PROP_POS_FRAMES, self.gopro_frame_idx)
            has_frame, self.gopro_frame = self.gopro_clip.read()
        
        return self.gopro_frame, self.gopro_frame_idx
        
    def get_gantry_position(self, aris_frametime):
        timepos = (aris_frametime + self.gantry_offset) / 10e3
        t = self.gantry_data['t']
        xi = np.interp(timepos, t, self.gantry_data['x'])
        yi = np.interp(timepos, t, self.gantry_data['y'])
        zi = np.interp(timepos, t, self.gantry_data['z'])
        return t, xi, yi, zi
        
        

class MainWindow(QtWidgets.QMainWindow):
    reload_plots = QtCore.pyqtSignal(str)
    
    def __init__(self, aris_data_dirs, gantry_files, gopro_files, out_file_path):
        super().__init__()
        
        # Keep track of the files we're using
        self.aris_data_dirs = aris_data_dirs
        self.gantry_files = gantry_files
        self.gopro_files = gopro_files
        self.out_file_path = out_file_path
        self.aris_file_idx = 0
        self.gantry_file_idx = 0
        self.gopro_file_idx = 0
        
        # Everything else will be stored inside the context
        self.context = None
        
        # QT things
        self._main_widget = QtWidgets.QWidget(self)
        
        self.fig = Figure()
        grid = GridSpec(2, 2, figure=self.fig)
        self.aris_plot = self.fig.add_subplot(grid[:, 0])
        self.gantry_plot = self.fig.add_subplot(grid[1, 1])
        self.gopro_plot = self.fig.add_subplot(grid[0, 1])
        self.gantry_offset_marker = self.gantry_plot.axvline(0, color='orange')
        
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding, 
                                  QtWidgets.QSizePolicy.Expanding)
        self.canvas.updateGeometry()
        
        # self.dropdown1 = QtWidgets.QComboBox()
        # self.dropdown1.addItems(["sex", "time", "smoker"])
        # self.dropdown2 = QtWidgets.QComboBox()
        # self.dropdown2.addItems(["sex", "time", "smoker", "day"])
        # self.dropdown2.setCurrentIndex(2)
        # self.dropdown1.currentIndexChanged.connect(self.update)
        # self.dropdown2.currentIndexChanged.connect(self.update)
        # self.label = QtWidgets.QLabel("A plot:")
        
        self.layout = QtWidgets.QGridLayout(self._main_widget)
        #self.layout.addWidget(QtWidgets.QLabel("Select category for subplots"))
        #self.layout.addWidget(self.dropdown1)
        #self.layout.addWidget(QtWidgets.QLabel("Select category for markers"))
        #self.layout.addWidget(self.dropdown2)
        self.layout.addWidget(self.canvas)

        self.setCentralWidget(self._main_widget)
        self.show()
        
        # Update in regular intervals
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.setInterval(1000 // 15)
        self.update_timer.start()
        
    def update(self):
        if not self.context or self.context.reload:
            self.context = MatchingContext(self.aris_data_dirs[self.aris_file_idx], self.gantry_files[self.gantry_file_idx], self.gopro_files[self.gopro_file_idx])
            
            # Prepare the gantry plot. As we update, we will only move the vertical line marker across.
            gantry_data = self.context.gantry_data
            self.gantry_plot.set_xlim([0, gantry_data['t'].iloc[-1]])
            self.gantry_plot.plot(gantry_data['t'], gantry_data['x'], 'r', label='x')
            self.gantry_plot.plot(gantry_data['t'], gantry_data['y'], 'g', label='y')
            self.gantry_plot.plot(gantry_data['t'], gantry_data['z'], 'b', label='z')
            
            self.context.reload = False
        
        # Update the context and plots
        self.context.tick()
        
        # ARIS
        aris_img, aris_frametime = self.context.get_aris_frame()
        self.aris_plot.set_title(f'{self.context.aris_basename} - {self.context.aris_frame_idx}')
        if self.context.aris_plot_img is None:
            self.context.aris_plot_img = self.aris_plot.imshow(aris_img, cmap='gray', vmin=0, vmax=255)
        else:
            self.context.aris_plot_img.set_data(aris_img)
        
        # GoPro
        gopro_frame, gopro_frame_idx = self.context.get_gopro_frame(aris_frametime)
        self.gopro_plot.set_title(f'{self.context.gopro_basename} - {gopro_frame_idx}')
        if gopro_frame is not None:
            self.gopro_plot.imshow(gopro_frame)
        else:
            self.gopro_plot.clear()

        # Gantry
        gantry_timepos = (aris_frametime + self.context.gantry_offset) / 10e3
        self.gantry_plot.set_title(f'{self.context.gantry_basename} - {gantry_timepos:+.3f}')
        self.gantry_offset_marker.set_xdata([gantry_timepos, gantry_timepos])

        self.fig.canvas.draw_idle()
        
        # TODO adjust offsets
        # TODO save to output file (numpy interp?)
    
    def write_match(self):
        # TODO check if file is empty, if so, write the header
        writer = csv.writer(out_file)
        writer.writerow([
            'aris_file',
            'gantry_file',
            'gopro_file',
            'gantry_timestamp_adjust',
            'gopro_frame_offset'
        ])
        
        # TODO write match from currentcontext



if __name__ == '__main__':
    # TODO
    sys.argv = [sys.argv[0], 'matched_data/data/aris/day1/', 'matched_data/data/gantry/day1/', 'matched_data/data/gopro/day1/clips_sd/', 'out.csv']
    
    if len(sys.argv) != 5:
        usage()
        raise RuntimeError('Wrong number of arguments')
    
    aris_dir_path = sys.argv[1]
    gantry_dir_path = sys.argv[2]
    gopro_dir_path = sys.argv[3]
    out_file_path = sys.argv[4]
    
    aris_data_dirs = sorted(os.path.join(aris_dir_path, f) for f in os.listdir(aris_dir_path))
    gantry_files = sorted(os.path.join(gantry_dir_path, f) for f in os.listdir(gantry_dir_path) if f.lower().endswith('.csv'))
    gopro_files = sorted(os.path.join(gopro_dir_path, f) for f in os.listdir(gopro_dir_path) if f.lower().endswith('.mp4'))
    
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(aris_data_dirs, gantry_files, gopro_files, out_file_path)
    sys.exit(app.exec_())
