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


def basename(s):
    return os.path.split(s)[-1]


class MatchingContext:
    def __init__(self, aris_dir, gantry_file, gopro_file):
        self.aris_basename = basename(aris_dir)
        self.gantry_basename = basename(gantry_file)
        self.gopro_basename = basename(gopro_file)
        
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
        self.aris_img = None
        
        self.gopro_frame_idx = -1
        self.gopro_offset = 0
        self.gopro_img = None
        
        self.gantry_offset = 0.
        
        self.reload = True
        
    def tick(self):
        self.aris_img = None
        self.aris_frame_idx = (self.aris_frame_idx + 1) % self.aris_frame_count
        
    def get_aris_frame(self):
        # FrameTime = time of recording on PC (ms since 1970)
        # sonarTimeStamp = time of recording on sonar (ms since 1970), not sure if synchronized to PC time
        frametime = self.aris_meta.at[self.aris_frame_idx, 'FrameTime'] - self.aris_t0
        if self.aris_img is None:
            self.aris_img = QtGui.QPixmap(self.aris_frames[self.aris_frame_idx])
        return self.aris_img, frametime
    
    def get_gopro_frame(self, aris_frametime):
        fps = self.gopro_clip.get(cv2.CAP_PROP_FPS)
        new_timepos = aris_frametime + self.gopro_offset
        new_frame_idx = int(new_timepos / 1000 // fps)
        
        if new_frame_idx != self.gopro_frame_idx:
            self.gopro_frame_idx = new_frame_idx
            self.gopro_clip.set(cv2.CAP_PROP_POS_FRAMES, self.gopro_frame_idx)
            has_frame, gopro_frame = self.gopro_clip.read()
            if has_frame:
                img = cv2.cvtColor(gopro_frame, cv2.COLOR_BGR2RGB)
                q_img = QtGui.QImage(img, img.shape[1], img.shape[0], QtGui.QImage.Format_RGB888)
                self.gopro_img = QtGui.QPixmap(q_img)
        
        return self.gopro_img, self.gopro_frame_idx
        
    def get_gantry_position(self, aris_frametime):
        timepos = (aris_frametime + self.gantry_offset) / 10e3
        t = self.gantry_data['t']
        xi = np.interp(timepos, t, self.gantry_data['x'])
        yi = np.interp(timepos, t, self.gantry_data['y'])
        zi = np.interp(timepos, t, self.gantry_data['z'])
        return t, xi, yi, zi
        

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, aris_data_dirs, gantry_files, gopro_files, out_file_path):
        super().__init__()
        
        # Keep track of the files we're using
        self.aris_data_dirs = aris_data_dirs
        self.gantry_files = gantry_files
        self.gopro_files = gopro_files
        self.out_file_path = out_file_path
        
        # Everything else will be stored inside the context
        self.context = None
        
        # QT things
        self._main_widget = QtWidgets.QWidget(self)
        
        # Plots
        self.aris_canvas = QtWidgets.QLabel()
        self.gopro_canvas = QtWidgets.QLabel()
        
        self.fig = Figure()
        self.gantry_plot = self.fig.add_subplot()
        self.gantry_offset_marker = self.gantry_plot.axvline(0, color='orange')
        
        self.plot_canvas = FigureCanvas(self.fig)
        self.plot_canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.plot_canvas.updateGeometry()
        
        # UI controls
        self.dropdown_select_aris = QtWidgets.QComboBox()
        self.dropdown_select_aris.addItems([basename(f) for f in self.aris_data_dirs])
        self.dropdown_select_aris.currentIndexChanged.connect(self.reload)
        self.dropdown_select_gantry = QtWidgets.QComboBox()
        self.dropdown_select_gantry.addItems([basename(f) for f in self.gantry_files])
        self.dropdown_select_gantry.currentIndexChanged.connect(self.reload)
        self.dropdown_select_gopro = QtWidgets.QComboBox()
        self.dropdown_select_gopro.addItems([basename(f) for f in self.gopro_files])
        self.dropdown_select_gopro.currentIndexChanged.connect(self.reload)
        
        ui_layout = QtWidgets.QVBoxLayout()
        ui_layout.addWidget(QtWidgets.QLabel("ARIS dataset"), )
        ui_layout.addWidget(self.dropdown_select_aris)
        ui_layout.addWidget(QtWidgets.QLabel("Gantry dataset"))
        ui_layout.addWidget(self.dropdown_select_gantry)
        ui_layout.addWidget(QtWidgets.QLabel("GoPro clip"))
        ui_layout.addWidget(self.dropdown_select_gopro)
        ui_layout.addStretch()

        self.layout = QtWidgets.QGridLayout(self._main_widget)
        self.layout.addWidget(self.aris_canvas, 0, 0, 2, 1)
        self.layout.addWidget(self.gopro_canvas, 0, 1)
        self.layout.addWidget(self.plot_canvas, 1, 1)
        self.layout.addLayout(ui_layout, 0, 2, 2, 1)

        self.setCentralWidget(self._main_widget)
        self.show()
        
        # Update in regular intervals
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.setInterval(1000 // 15)
        self.update_timer.start()

    def reload(self):
        self.context.reload = True
    
    def update(self):
        if not self.context or self.context.reload:
            aris_file = self.aris_data_dirs[self.dropdown_select_aris.currentIndex()]
            gantry_file = self.gantry_files[self.dropdown_select_gantry.currentIndex()]
            gopro_file = self.gopro_files[self.dropdown_select_gopro.currentIndex()]
            
            self.context = MatchingContext(aris_file, gantry_file, gopro_file)
            self.gantry_plot.cla()
            
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
        aris_frame, aris_frametime = self.context.get_aris_frame()
        self.aris_canvas.setPixmap(aris_frame)
        
        # GoPro
        gopro_frame, gopro_frame_idx = self.context.get_gopro_frame(aris_frametime)
        self.gopro_canvas.setPixmap(gopro_frame)

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
