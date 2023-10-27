#!/usr/bin/env python
import sys
import os
import csv
import yaml
import numpy as np
import pandas as pd
import cv2
import datetime as dt
import pytz
from dataclasses import dataclass, asdict
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtGui, QtWidgets
from qrangeslider import QRangeSlider


def basename(s):
    if s.endswith('/'):
        s = s[:-1]
    return os.path.split(s)[-1]

def gopro_sorting_key(filename):
    base = os.path.splitext(basename(filename))[0]
    #prefix = base[:2]   # GX
    chapter = base[2:4]  # 01
    vid = base[4:8]      # 0010
    clip = base[9:11]    # _01
    return f'{vid}{chapter}{clip}'

def split_microseconds(timestamp_us):
    s = int(timestamp_us // 1e6)
    ms = int((timestamp_us - s * 1e6) // 1e3)
    us = int(timestamp_us - s * 1e6 - ms * 1e3)
    return s, ms, us

def parse_gopro_datetime(dt_string):
    return dt.datetime.fromisoformat(dt_string.replace('Z', '+00:00'))

def parse_gopro_timestamp(t_string):
    m, rest = t_string.split(':')
    s, ms = rest.split('.')
    return int(m) * 60 + int(s) + float(ms) / 1000


_aris_metadata_cache = {}
def get_aris_metadata(aris_data_dir):
    if aris_data_dir in _aris_metadata_cache:
        return _aris_metadata_cache[aris_data_dir]
    
    aris_basename = basename(aris_data_dir)
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


_optical_flow_cache = {}
def get_optical_flow(dataset_path):
    if dataset_path in _optical_flow_cache:
        return _optical_flow_cache[dataset_path]
    
    if os.path.isdir(dataset_path):
        data_folder = dataset_path
    else:
        data_folder = os.path.dirname(dataset_path)
    data_id = os.path.splitext(basename(dataset_path))[0]
    cache_file = os.path.join(data_folder, data_id + '_flow.csv')
    
    flow = np.squeeze(pd.read_csv(cache_file, header=None).to_numpy())
    norm_f = np.quantile(flow, 0.95) - np.min(flow)
    #norm_f = np.max(flow) - np.min(flow)
    if not np.isclose(norm_f, 0.):
        flow = (flow - np.min(flow)) / norm_f
    
    _optical_flow_cache[dataset_path] = flow
    return flow


class MatchingContext:
    def __init__(self, aris_dir, gopro_file, gantry_file):
        self.aris_basename = basename(aris_dir)
        self.gopro_basename = basename(gopro_file)
        self.gantry_basename = basename(gantry_file)
        
        # Load ARIS data
        self.aris_frames_path = os.path.join(aris_dir, 'polar')
        if not os.path.isdir(self.aris_frames_path):
            print(f'ARIS dataset {self.aris_basename} does not contain polar frames, using raw frames instead')
            self.aris_frames_path = aris_dir
        
        self.aris_file_meta, self.aris_frames_meta, self.aris_marks_meta = get_aris_metadata(aris_dir)
        self.aris_frames = sorted(os.path.join(self.aris_frames_path, f) for f in os.listdir(self.aris_frames_path) if f.lower().endswith('.pgm'))
        self.aris_optical_flow = get_optical_flow(aris_dir)
        self._aris_frame_idx = 0
        self._aris_start_frame = 0
        self._aris_end_frame = len(self.aris_frames) - 1
        self.aris_tick_step = 1
        self.aris_motion_onset = None
        self.aris_frames_total = len(self.aris_frames)
        self.aris_t0 = self.get_aris_frametime(0)
        self.aris_duration = self.get_aris_frametime(-1) - self.aris_t0
        self.aris_img = None

        # Load beginning of motion frame from save file
        if self.aris_marks_meta and 'onset' in self.aris_marks_meta:
            onset = max(0, self.aris_marks_meta['onset'])
            self._aris_start_frame = onset
            self.aris_motion_onset = onset
        
        # Load GoPro clip
        all_gopro_meta = get_gopro_metadata(os.path.dirname(gopro_file))
        self.gopro_meta = all_gopro_meta.loc[all_gopro_meta['file'] == self.gopro_basename].iloc[0]
        self.gopro_clip = cv2.VideoCapture(gopro_file)
        self.gopro_optical_flow = get_optical_flow(gopro_file)
        self.gopro_original_creation_time = parse_gopro_datetime(self.gopro_meta['creation_time'])
        self.gopro_original_creation_time_simple = self.gopro_original_creation_time.strftime('%Y-%m-%d_%H%M%S')
        self.gopro_frame_idx = -1
        self.gopro_frames_total = int(self.gopro_clip.get(cv2.CAP_PROP_FRAME_COUNT))
        self.gopro_fps = self.gopro_clip.get(cv2.CAP_PROP_FPS)
        self.gopro_offset = 0
        self.gopro_img = None
        
        # Load Gantry recording
        all_gantry_meta = get_gantry_metadata(os.path.dirname(gantry_file))
        self.gantry_meta = all_gantry_meta.loc[all_gantry_meta['file'] == self.gantry_basename].iloc[0]
        self.gantry_data = pd.read_csv(gantry_file)
        self.gantry_t0 = self.gantry_meta['start_us']
        self.gantry_duration = self.gantry_meta['end_us'] - self.gantry_t0
        self.gantry_offset = self.gantry_meta['onset_us'] - self.gantry_t0
        
        self.reload = True
    
    @property
    def aris_frame_idx(self):
        return self._aris_frame_idx
    
    @aris_frame_idx.setter
    def aris_frame_idx(self, new_val):
        if self.aris_start_frame < new_val < self.aris_end_frame:
            self._aris_frame_idx = new_val
        else:
            self._aris_frame_idx = self.aris_start_frame
        self.aris_img = None
    
    @property
    def aris_start_frame(self):
        return self._aris_start_frame
    
    @aris_start_frame.setter
    def aris_start_frame(self, new_val):
        self._aris_start_frame = min(new_val, self.aris_end_frame - 1)
        self.aris_frame_idx = max(self.aris_start_frame, self.aris_frame_idx)
        
    @property
    def aris_end_frame(self):
        return self._aris_end_frame
    
    @aris_end_frame.setter
    def aris_end_frame(self, new_val):
        self._aris_end_frame = max(new_val, self.aris_start_frame + 1)
        self.aris_frame_idx = min(self.aris_frame_idx, self.aris_end_frame)
    
    @property
    def aris_active_frames(self):
        return self.aris_end_frame - self.aris_start_frame
    
    @property
    def aris_active_duration(self):
        return self.get_aris_frametime(self.aris_end_frame) - self.get_aris_frametime(self.aris_start_frame)
    
    def tick(self):
        self.aris_img = None
        self.aris_frame_idx += self.aris_tick_step
        
    def get_aris_frame(self, colorize=True):
        frametime = self.get_aris_frametime(self.aris_frame_idx)
        if self.aris_img is None:
            if colorize:
                frame = cv2.imread(self.aris_frames[self.aris_frame_idx])
                frame_colorized = cv2.applyColorMap(frame, cv2.COLORMAP_TWILIGHT_SHIFTED)  # MAGMA, DEEPGREEN, OCEAN
                h, w, channels = frame_colorized.shape
                bytes_per_line = 3 * w
                qimg = QtGui.QImage(frame_colorized.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888).rgbSwapped()
                self.aris_img = QtGui.QPixmap(qimg)
            else:
                self.aris_img = QtGui.QPixmap(self.aris_frames[self.aris_frame_idx])
        return self.aris_img, frametime
    
    def get_aris_frametime(self, frame_idx):
        # FrameTime = time of recording on PC (µs since 1970)
        # sonarTimeStamp = time of recording on sonar (µs since 1970), not sure if synchronized to PC time
        return self.aris_frames_meta['FrameTime'].iloc[frame_idx]
    
    def get_aris_frametime_ext(self, frame_idx):
        if frame_idx < 0:
            return self.aris_t0 - abs(frame_idx) * np.mean(self.aris_frames_meta['SamplePeriod'])
        if frame_idx >= self.aris_frames_total:
            return self.aris_t0 + self.aris_duration + (frame_idx - self.aris_frames_total) * np.mean(self.aris_frames_meta['SamplePeriod'])
    
        return self.get_aris_frametime(frame_idx)
    
    def aristime_to_gopro_idx(self, aris_frametime):
        # TODO aris frametime is in microseconds, then why does 1e3 seem correct for frames per SECOND?
        time_from_start = aris_frametime - self.get_aris_frametime(self.aris_start_frame)
        return int(time_from_start / 1e3 // self.gopro_fps) + self.gopro_offset
    
    def get_gopro_frame(self, aris_frametime):
        new_frame_idx = self.aristime_to_gopro_idx(aris_frametime)
        
        if new_frame_idx != self.gopro_frame_idx:
            self.gopro_frame_idx = new_frame_idx
            self.gopro_clip.set(cv2.CAP_PROP_POS_FRAMES, self.gopro_frame_idx)
            has_frame, gopro_frame = self.gopro_clip.read()
            if has_frame:
                img = cv2.cvtColor(gopro_frame, cv2.COLOR_BGR2RGB)
                q_img = QtGui.QImage(img, img.shape[1], img.shape[0], QtGui.QImage.Format_RGB888)
                self.gopro_img = QtGui.QPixmap(q_img)
        
        return self.gopro_img, self.gopro_frame_idx
    
    def get_gantry_odom(self, aris_frametime):
        time_after_onset = aris_frametime - self.get_aris_frametime(self.aris_start_frame)
        timepos = self.gantry_t0 + self.gantry_offset + time_after_onset
        
        if timepos < self.gantry_t0:
            timepos = self.gantry_t0
        if timepos > self.gantry_t0 + self.gantry_duration:
            timepos = self.gantry_t0 + self.gantry_duration
        
        t = self.gantry_data['timestamp_us']   
        xi = np.interp(timepos, t, self.gantry_data['x'])
        yi = np.interp(timepos, t, self.gantry_data['y'])
        zi = np.interp(timepos, t, self.gantry_data['z'])
        return (xi, yi, zi), timepos



@dataclass
class Association:
    aris_idx: int
    gopro_idx: int
    gantry_idx: int
    aris_onset: int
    gopro_offset: int
    gantry_offset: float
    notes: str
    
    def has_gopro(self):
        return self.gopro_idx >= 0
    
    def has_gantry(self):
        return self.gantry_idx >= 0


class MainWidget(QtWidgets.QWidget):
    keyPressed = QtCore.pyqtSignal(int)
    
    def __init__(self, master):
        super().__init__(master)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.keyPressed.emit(event.key())


class MySlider(QtWidgets.QSlider):
    def __init__(self):
        super().__init__(QtCore.Qt.Horizontal)
        self.mousePressPos = None
        self.setMouseTracking(True)
        
    def wheelEvent(self, e):
        self.setValue(self.value() + np.sign(e.angleDelta().y()) * self.singleStep())
    
    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self.mousePressPos = e.pos()
        else:
            super().mousePressEvent(e)
    
    def mouseMoveEvent(self, e):
        if self.mousePressPos is not None and e.buttons() & QtCore.Qt.LeftButton:
            self.update_from_mouse_pos(e)
        else:
            super().mouseMoveEvent(e)
    
    def mouseReleaseEvent(self, e):
        if  self.mousePressPos is not None \
        and e.button() == QtCore.Qt.LeftButton \
        and e.pos() in self.rect():
            self.update_from_mouse_pos(e)
            self.mousePressPos = None
        else:
            return super().mouseReleaseEvent(e)

    def update_from_mouse_pos(self, e):
        e.accept()
        x = e.pos().x()
        value = (self.maximum() - self.minimum()) * x / self.width() + self.minimum()
        self.setValue(int(value))
        


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, aris_base_dir, gopro_base_dir, gantry_base_dir, autoplay=False):
        super().__init__()
        
        self.aris_associated = set()
        self.gopro_associated = set()
        self.gantry_associated = set()
        self.association_details = {}
        
        # Keep track of the files we're using
        self.aris_base_dir = aris_base_dir
        self.gopro_base_dir = gopro_base_dir
        self.gantry_base_dir = gantry_base_dir
        
        self.aris_data_dirs = sorted(os.path.join(aris_base_dir, f) for f in os.listdir(aris_base_dir))
        self.gopro_files = sorted([os.path.join(gopro_base_dir, f) for f in os.listdir(gopro_base_dir) if f.lower().endswith('.mp4')], key=gopro_sorting_key)
        self.gantry_files = sorted(os.path.join(gantry_base_dir, f) for f in os.listdir(gantry_base_dir) if f.lower().endswith('.csv') and not 'metadata' in f.lower())
        
        # Everything else will be stored inside the context
        self.context = None
        self.dirty = False
        self.playing = autoplay
        
        # QT things
        self._main_widget = MainWidget(self)
        self._main_widget.keyPressed.connect(self._handle_keypress)
        
        mono_font = QtGui.QFont('Monospace')
        mono_font.setStyleHint(QtGui.QFont.TypeWriter)
        
        # Plots
        self.canvas_aris = QtWidgets.QLabel()
        self.canvas_gopro = QtWidgets.QLabel()
        
        self.gantry_fig = Figure()
        self.gantry_plot = self.gantry_fig.add_subplot()
        self.gantry_plot.figure.tight_layout()
        
        self.canvas_gantry_plot = FigureCanvas(self.gantry_fig)
        self.canvas_gantry_plot.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.canvas_gantry_plot.updateGeometry()
        
        self.flow_fig = Figure(figsize=(6, 2))
        self.flow_plot = self.flow_fig.add_subplot()
        self.flow_plot.figure.tight_layout()
        self.flow_plot2 = self.flow_plot.twiny()
        self.flow_plot2.get_xaxis().set_visible(False)
        
        self.canvas_flow_plot = FigureCanvas(self.flow_fig)
        self.canvas_flow_plot.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.canvas_flow_plot.updateGeometry()
        
        # UI controls
        self.dropdown_select_aris = QtWidgets.QComboBox()
        self.dropdown_select_aris.setFont(mono_font)
        self.dropdown_select_aris.currentIndexChanged.connect(self.reload)
        self.dropdown_select_gopro = QtWidgets.QComboBox()
        self.dropdown_select_gopro.setFont(mono_font)
        self.dropdown_select_gopro.currentIndexChanged.connect(self.reload)
        self.dropdown_select_gantry = QtWidgets.QComboBox()
        self.dropdown_select_gantry.setFont(mono_font)
        self.dropdown_select_gantry.currentIndexChanged.connect(self.reload)
        self.refresh_dropdowns()
        
        # Sliders and spinners 
        def connect_slider_spinner(slider, spinner, on_value_update_func):
            @QtCore.pyqtSlot(int)
            def on_value_changed(val):
                spinner.setValue(val)
                slider.setValue(val)
                on_value_update_func(val)
                self.ensure_update()
            
            slider.valueChanged.connect(on_value_changed)
            spinner.valueChanged.connect(on_value_changed)
        
        # ARIS
        self.slider_aris_pos = MySlider()
        self.spinner_aris_pos = QtWidgets.QSpinBox()
        connect_slider_spinner(self.slider_aris_pos, self.spinner_aris_pos, self._on_aris_pos_changed)
        
        self.rangeslider_aris = QRangeSlider()
        self.rangeslider_aris.startValueChanged.connect(self._on_aris_range_start_changed)
        self.rangeslider_aris.endValueChanged.connect(self._on_aris_range_end_changed)
        
        # Gopro
        self.slider_gopro_pos = MySlider()
        self.slider_gopro_pos.setEnabled(False)
        self.spinner_gopro_pos = QtWidgets.QSpinBox()
        self.spinner_gopro_pos.setEnabled(False)
        # Driven by update()
        connect_slider_spinner(self.slider_gopro_pos, self.spinner_gopro_pos, lambda v: None)
        
        self.slider_gopro_offset = MySlider()
        self.slider_gopro_offset.setSingleStep(1)
        self.slider_gopro_offset.setPageStep(10)
        self.spinner_gopro_offset = QtWidgets.QSpinBox()
        self.spinner_gopro_offset.setSingleStep(1)
        connect_slider_spinner(self.slider_gopro_offset, self.spinner_gopro_offset, self._on_gopro_offset_changed)
        
        # Gantry
        self.slider_gantry_pos = MySlider()
        self.slider_gantry_pos.setMaximum(1000)  # percent based
        self.slider_gantry_pos.setEnabled(False)
        self.spinner_gantry_pos = QtWidgets.QSpinBox()
        self.spinner_gantry_pos.setMaximum(1000)
        self.spinner_gantry_pos.setEnabled(False)
        # Driven by update()
        connect_slider_spinner(self.slider_gantry_pos, self.spinner_gantry_pos, lambda v: None)
        
        self.slider_gantry_offset_s = MySlider()
        self.slider_gantry_offset_s.setRange(-1000, 1000)
        self.slider_gantry_offset_s.setSingleStep(1)
        self.slider_gantry_offset_s.setPageStep(5)
        self.spinner_gantry_offset_s = QtWidgets.QSpinBox()
        self.spinner_gantry_offset_s.setRange(-1000, 1000)
        connect_slider_spinner(self.slider_gantry_offset_s, self.spinner_gantry_offset_s, self._on_gantry_offset_changed)
        
        self.slider_gantry_offset_ms = MySlider()
        self.slider_gantry_offset_ms.setRange(-1000, 1000)
        self.slider_gantry_offset_ms.setSingleStep(5)
        self.slider_gantry_offset_ms.setPageStep(10)
        self.spinner_gantry_offset_ms = QtWidgets.QSpinBox()
        self.spinner_gantry_offset_ms.setRange(-1000, 1000)
        connect_slider_spinner(self.slider_gantry_offset_ms, self.spinner_gantry_offset_ms, self._on_gantry_offset_changed)
        
        self.slider_gantry_offset_us = MySlider()
        self.slider_gantry_offset_us.setRange(-1000, 1000)
        self.slider_gantry_offset_us.setSingleStep(10)
        self.slider_gantry_offset_us.setPageStep(50)
        self.spinner_gantry_offset_us = QtWidgets.QSpinBox()
        self.spinner_gantry_offset_us.setRange(-1000, 1000)
        connect_slider_spinner(self.slider_gantry_offset_us, self.spinner_gantry_offset_us, self._on_gantry_offset_changed)
        
        # Playback
        self.spinner_playback_fpu = QtWidgets.QSpinBox()
        self.spinner_playback_fpu.setRange(1, 10)
        self.spinner_playback_fpu.setValue(1)
        self.spinner_playback_fpu.valueChanged[int].connect(self._on_playback_fpu_changed)
        
        self.spinner_playback_ups = QtWidgets.QSpinBox()
        self.spinner_playback_ups.setRange(1, 60)
        self.spinner_playback_ups.setValue(15)
        self.spinner_playback_ups.valueChanged[int].connect(self._on_playback_ups_changed)
        
        self.button_play_pause = QtWidgets.QPushButton('&Play / Pause')
        self.button_play_pause.clicked.connect(self._handle_play_pause_button)
        
        # Export
        self.notes_widget = QtWidgets.QPlainTextEdit()
        
        self.check_associate_gopro = QtWidgets.QCheckBox('GoPro')
        self.check_associate_gopro.setChecked(True)
        self.check_associate_gantry = QtWidgets.QCheckBox('Gantry')
        self.check_associate_gantry.setChecked(True)
        
        self.button_associate = QtWidgets.QPushButton('&Associate')
        self.button_associate.clicked.connect(self._handle_associate_button)
        
        self.button_save = QtWidgets.QPushButton('&Save')
        self.button_save.clicked.connect(self._handle_save_button)
        
        # Interactive elements layout
        ctrl_layout = QtWidgets.QGridLayout()
        ctrl_layout.addWidget(QtWidgets.QLabel("ARIS dataset"), 0, 0, 1, -1)
        ctrl_layout.addWidget(self.dropdown_select_aris, 1, 0, 1, -1)
        ctrl_layout.addWidget(QtWidgets.QLabel("GoPro clip"), 2, 0, 1, -1)
        ctrl_layout.addWidget(self.dropdown_select_gopro, 3, 0, 1, -1)
        ctrl_layout.addWidget(QtWidgets.QLabel("Gantry dataset"), 4, 0, 1, -1)
        ctrl_layout.addWidget(self.dropdown_select_gantry, 5, 0, 1, -1)
        
        # Explain dropdown markings
        ctrl_layout.addWidget(QtWidgets.QLabel("(*) associated\n(m) has motion onset\n(x) has timestamp overlap"), 6, 0, 1, -1)
        
        ctrl_layout.addWidget(QtWidgets.QLabel(""), 7, 0, 1, -1)
        ctrl_layout.addWidget(QtWidgets.QLabel("Aris Playback"), 8, 0, 1, -1)
        ctrl_layout.addWidget(self.rangeslider_aris, 9, 0)
        ctrl_layout.addWidget(self.slider_aris_pos, 10, 0)
        ctrl_layout.addWidget(self.spinner_aris_pos, 10, 1)
        ctrl_layout.addWidget(QtWidgets.QLabel("f"), 10, 2)
        
        ctrl_layout.addWidget(QtWidgets.QLabel("GoPro Playback"), 12, 0, 1, -1)
        ctrl_layout.addWidget(self.slider_gopro_pos, 13, 0)
        ctrl_layout.addWidget(self.spinner_gopro_pos, 13, 1)
        ctrl_layout.addWidget(QtWidgets.QLabel("f"), 13, 2)
        
        ctrl_layout.addWidget(QtWidgets.QLabel("Gantry Playback"), 15, 0, 1, -1)
        ctrl_layout.addWidget(self.slider_gantry_pos, 16, 0)
        ctrl_layout.addWidget(self.spinner_gantry_pos, 16, 1)
        ctrl_layout.addWidget(QtWidgets.QLabel("‰"), 16, 2)
        
        ctrl_layout.addWidget(QtWidgets.QLabel(""), 17, 0, 1, -1)
        
        ctrl_layout.addWidget(QtWidgets.QLabel("GoPro Offset"), 18, 0, 1, -1)
        ctrl_layout.addWidget(self.slider_gopro_offset, 19, 0)
        ctrl_layout.addWidget(self.spinner_gopro_offset, 19, 1)
        ctrl_layout.addWidget(QtWidgets.QLabel("f"), 19, 2)
        
        ctrl_layout.addWidget(QtWidgets.QLabel("Gantry Offset"), 20, 0, 1, -1)
        ctrl_layout.addWidget(self.slider_gantry_offset_s, 21, 0)
        ctrl_layout.addWidget(self.spinner_gantry_offset_s, 21, 1)
        ctrl_layout.addWidget(QtWidgets.QLabel("s"), 21, 2)
        ctrl_layout.addWidget(self.slider_gantry_offset_ms, 22, 0)
        ctrl_layout.addWidget(self.spinner_gantry_offset_ms, 22, 1)
        ctrl_layout.addWidget(QtWidgets.QLabel("ms"), 22, 2)
        ctrl_layout.addWidget(self.slider_gantry_offset_us, 23, 0)
        ctrl_layout.addWidget(self.spinner_gantry_offset_us, 23, 1)
        ctrl_layout.addWidget(QtWidgets.QLabel("µs"), 23, 2)
        
        # Overall UI panel layout
        ui_layout = QtWidgets.QVBoxLayout()
        ui_layout.addLayout(ctrl_layout)
        
        fps_layout = QtWidgets.QGridLayout()
        fps_layout.addWidget(QtWidgets.QLabel("Max. Updates per Second"), 0, 0)
        fps_layout.addWidget(QtWidgets.QLabel("Frames per Update"), 0, 1)
        fps_layout.addWidget(self.spinner_playback_ups, 1, 0)
        fps_layout.addWidget(self.spinner_playback_fpu, 1, 1)
        
        ui_layout.addWidget(QtWidgets.QLabel(""))
        ui_layout.addLayout(fps_layout)
        ui_layout.addWidget(self.button_play_pause)
        
        ui_layout.addWidget(QtWidgets.QLabel(""))
        ui_layout.addWidget(QtWidgets.QLabel("Notes"))
        ui_layout.addWidget(self.notes_widget)
        ui_layout.setStretchFactor(self.notes_widget, 100)
        
        checkbox_layout = QtWidgets.QHBoxLayout()
        checkbox_layout.addWidget(QtWidgets.QLabel("Associate with"))
        checkbox_layout.addWidget(self.check_associate_gopro)
        checkbox_layout.addWidget(self.check_associate_gantry)
        ui_layout.addLayout(checkbox_layout)
        
        ui_layout.addWidget(self.button_associate)
        ui_layout.addWidget(self.button_save)
        
        # Table
        self.table_associations = QtWidgets.QTableWidget(len(self.aris_data_dirs), 3)
        self.table_associations.setHorizontalHeaderLabels(['ARIS', 'GoPro', 'Gantry'])
        for idx, aris_file in enumerate(self.aris_data_dirs):
            self.table_associations.setItem(idx, 0, QtWidgets.QTableWidgetItem(basename(aris_file)))
        self.table_associations.setItem(0, 1, QtWidgets.QTableWidgetItem(' ' * len(self.gopro_files[0])))
        self.table_associations.setItem(0, 2, QtWidgets.QTableWidgetItem(' ' * len(self.gantry_files[0])))
        self.table_associations.resizeColumnsToContents()
        table_columns_width = sum(self.table_associations.columnWidth(i) for i in range(self.table_associations.columnCount()))
        self.table_associations.setMinimumWidth(table_columns_width + 20)

        # Global UI Layout
        ui_layout_wrapper = QtWidgets.QWidget()
        ui_layout_wrapper.setLayout(ui_layout)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(ui_layout_wrapper)
        splitter.addWidget(self.table_associations)
        splitter.setStretchFactor(100, 50)
        
        self.layout = QtWidgets.QGridLayout(self._main_widget)
        self.layout.addWidget(self.canvas_aris, 0, 0, 3, 1, QtCore.Qt.AlignTop)
        self.layout.addWidget(self.canvas_gopro, 0, 1, 1, 1, QtCore.Qt.AlignTop)
        self.layout.addWidget(self.canvas_flow_plot, 1, 1, 1, 1, QtCore.Qt.AlignTop)
        self.layout.addWidget(self.canvas_gantry_plot, 2, 1, 1, 1, QtCore.Qt.AlignTop)
        self.layout.addWidget(splitter, 0, 2, 3, 1)
        self.layout.setColumnStretch(2, 50)
        
        self.setCentralWidget(self._main_widget)
        
        # Update in regular intervals
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.do_update)
        self.update_timer.setInterval(1000 // self.spinner_playback_ups.value())
        self.update_timer.start()
        
        self.reset_context()
        self.show()
    
    
    def _on_aris_pos_changed(self, val):
        self.context.aris_frame_idx = val
    
    def _on_aris_range_start_changed(self, val):
        self.context.aris_start_frame = val
        self.ensure_update()
    
    def _on_aris_range_end_changed(self, val):
        self.context.aris_end_frame = val
        self.ensure_update()

    def _on_gopro_offset_changed(self, val):
        self.context.gopro_offset = val
        
    def _on_gantry_offset_changed(self, val):
        self.context.gantry_offset = self.slider_gantry_offset_s.value() * 1e6 \
                                    + self.slider_gantry_offset_ms.value() * 1e3 \
                                    + self.slider_gantry_offset_us.value()
        
    @QtCore.pyqtSlot(int)
    def _on_playback_fpu_changed(self, val):
        #self.update_timer.setInterval(1000 // val)
        self.context.aris_tick_step = val
        
    @QtCore.pyqtSlot(int)
    def _on_playback_ups_changed(self, val):
        self.update_timer.setInterval(1000 // val)
        

    def _handle_play_pause_button(self):
        self.playing = not self.playing

    def _handle_associate_button(self):
        aris_idx = self.dropdown_select_aris.currentIndex()
        gopro_idx = self.dropdown_select_gopro.currentIndex() if self.check_associate_gopro.isChecked() else -1
        gantry_idx = self.dropdown_select_gantry.currentIndex() if self.check_associate_gantry.isChecked() else -1
        
        association = Association(
            aris_idx,
            gopro_idx,
            gantry_idx,
            self.context.aris_start_frame,
            self.context.gopro_offset,
            self.context.gantry_offset,
            self.notes_widget.toPlainText(),
        )
        
        # Check if there was a previous association with any of the files; if so, remove it
        to_remove = []
        for old_association in self.association_details.values():
            if not (aris_idx == old_association.aris_idx or (gopro_idx >= 0 and gopro_idx == old_association.gopro_idx) or (gantry_idx >= 0 and gantry_idx == old_association.gantry_idx)):
                continue
            
            # Steal the GoPro association if necessary
            if self.check_associate_gopro.isChecked():
                self.gopro_associated.discard(old_association.gopro_idx)
                old_association.gopro_idx = -1
                self.table_associations.setItem(old_association.aris_idx, 1, None)
                
            # Steal the Gantry association if necessary
            if self.check_associate_gantry.isChecked():
                self.gantry_associated.discard(old_association.gantry_idx)
                old_association.gantry_idx = -1
                self.table_associations.setItem(old_association.aris_idx, 2, None)
            
            # If nothing is left in the old association, delete it
            if not old_association.has_gopro() and not old_association.has_gantry():
                self.aris_associated.discard(old_association.aris_idx)
                to_remove.append(old_association.aris_idx)
        
        for key in to_remove:
            del self.association_details[key]
        
        
        # Store new association
        self.aris_associated.add(aris_idx)
        
        if gopro_idx >= 0:
            self.gopro_associated.add(gopro_idx)
            self.table_associations.setItem(aris_idx, 1, QtWidgets.QTableWidgetItem(self.context.gopro_basename))
            
        if gantry_idx >= 0:
            self.gantry_associated.add(gantry_idx)
            self.table_associations.setItem(aris_idx, 2, QtWidgets.QTableWidgetItem(self.context.gantry_basename))
        
        self.association_details[aris_idx] = association
        
        
        # XXX Automatically skipping to next entries seemd counter-intuitive
        # Mark files as associated in dropdowns
        # def next_unassociated(items, start = 0):
        #     for idx, f in enumerate(items[start:]):
        #         if basename(f) not in self.associated:
        #             return start + idx
        #     return start
        # 
        # self.dropdown_select_aris.setCurrentIndex(next_unassociated(self.aris_data_dirs))
        # self.dropdown_select_gopro.setCurrentIndex(next_unassociated(self.gopro_files))
        # self.dropdown_select_gantry.setCurrentIndex(next_unassociated(self.gantry_files))
        
        self.refresh_dropdowns()

    def refresh_dropdowns(self):
        # ARIS
        aris_items = []
        aris_frames_meta = None
        for idx,item in enumerate(self.aris_data_dirs):
            aris_metadata = get_aris_metadata(item)
            marks = aris_metadata[2]
            
            if idx == max(0, self.dropdown_select_aris.currentIndex()):
                aris_frames_meta = aris_metadata[1]
            
            associated = '*' if idx in self.aris_associated else ' '
            motion_onset = 'm' if 'onset' in marks else ' '
            aris_items.append(f'({associated}) ({motion_onset})  {basename(item)}')
        
        # Context may not be initialized yet, so don't use context.get_aris_frametime()
        current_aris_start = aris_frames_meta['FrameTime'][0]
        current_aris_end = aris_frames_meta['FrameTime'].iloc[-1]
        
        # GoPro
        gopro_items = []
        gopro_meta = get_gopro_metadata(self.gopro_base_dir)
        for idx,item in enumerate(self.gopro_files):
            # GoPro clips are already cut to where the motion starts
            # Can't match metadata based on index since we have custom sorting
            gopro_file_meta = gopro_meta[gopro_meta['file'] == basename(item)].iloc[0]
            gopro_creation_time = parse_gopro_datetime(gopro_file_meta['creation_time'])
            # TODO so far we showed everything in localtime, but hardcoding the offset is ugly...
            gopro_creation_time = gopro_creation_time.replace(hour=gopro_creation_time.hour + 2)
            gopro_datetime_simple = gopro_creation_time.strftime('%Y-%m-%d_%H%M%S')
            
            # Check original timestamps to see if footage has overlap with ARIS
            gopro_t0 = (gopro_creation_time - dt.datetime.utcfromtimestamp(0).replace(tzinfo=pytz.UTC)).total_seconds()
            gopro_clip_start = (gopro_t0 + parse_gopro_timestamp(gopro_file_meta['original_start'])) * 1e6
            gopro_clip_end = (gopro_t0 + parse_gopro_timestamp(gopro_file_meta['original_end'])) * 1e6
            
            associated = '*' if idx in self.gopro_associated else ' '
            overlapping = 'x' if gopro_clip_start < current_aris_end and gopro_clip_end > current_aris_start else ' '
            # TODO overlapping is not useful because for some reason all footage from day1 has the same creation date
            gopro_items.append(f'({associated}) ( )  {gopro_datetime_simple}  {basename(item)}')
        
        # Gantry
        gantry_items = []
        gantry_metadata = get_gantry_metadata(self.gantry_base_dir)
        for idx,item in enumerate(self.gantry_files):
            gantry_file_meta = gantry_metadata.iloc[idx]
            gantry_file_start = gantry_file_meta['start_us']
            gantry_file_end = gantry_file_meta['end_us']
            
            # Mark gantry files which have timestamps overlapping with selected ARIS file
            associated = '*' if idx in self.gantry_associated else ' '
            overlapping = 'x' if gantry_file_start < current_aris_end and gantry_file_end > current_aris_start else ' '
            gantry_items.append(f'({associated}) ({overlapping})  {basename(item)}')
        
        def repopulate(dropdown, items):
            idx = max(0, dropdown.currentIndex())
            dropdown.currentIndexChanged.disconnect()
            dropdown.clear()
            dropdown.addItems(items)
            dropdown.setCurrentIndex(idx)
            dropdown.currentIndexChanged.connect(self.reload)
        
        repopulate(self.dropdown_select_aris, aris_items)
        repopulate(self.dropdown_select_gopro, gopro_items)
        repopulate(self.dropdown_select_gantry, gantry_items)
        
    def _handle_keypress(self, key):
        if key in [QtCore.Qt.Key.Key_Space, QtCore.Qt.Key.Key_P]:
            self.button_play_pause.animateClick()
        elif key == QtCore.Qt.Key.Key_A:
            self.button_associate.animateClick()
        elif key == QtCore.Qt.Key.Key_S:
            self.button_save.animateClick()
        else:
            return

    def _handle_save_button(self):
        self.update_timer.stop()
        
        out_file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Associations', '', 'Csv Files(*.csv)')
        if not out_file_path:
            return
        
        with open(out_file_path, 'w') as out_file:
            writer = csv.DictWriter(out_file, Association.__dataclass_fields__.keys())
            writer.writeheader()
            writer.writerows(asdict(a) for a in self.association_details)


    def ensure_update(self):
        self.dirty = True
        
    def needs_update(self):
        return self.playing or self.context is None or self.dirty

    def do_update(self):
        if not self.needs_update():
            return
        
        if not self.context or self.context.reload:
            self.reset_context()
        
        if self.playing:
            self.context.tick()
        
        # ARIS
        aris_frame, aris_frametime = self.context.get_aris_frame()
        self.slider_aris_pos.setValue(self.context.aris_frame_idx)
        self.canvas_aris.setPixmap(aris_frame)
        
        # GoPro
        gopro_frame, gopro_frame_idx = self.context.get_gopro_frame(aris_frametime)
        if gopro_frame:
            self.canvas_gopro.setPixmap(gopro_frame)
            self.slider_gopro_pos.setValue(gopro_frame_idx)
            self.spinner_gopro_pos.setValue(gopro_frame_idx)
        else:
            print(f'no gopro frame for {aris_frametime - self.context.aris_t0}, this may be a bug')

        # Flow plot
        idx_half_range = 75 * self.spinner_playback_fpu.value()
        aris_start_idx = self.context.aris_frame_idx - idx_half_range
        aris_end_idx = self.context.aris_frame_idx + idx_half_range
        self.flow_plot.set_xticks(np.arange(aris_start_idx, aris_end_idx, (aris_end_idx - aris_start_idx) / 20))
        self.flow_plot.set_xlim([aris_start_idx, aris_end_idx])
        
        gopro_start_idx = self.context.aristime_to_gopro_idx(self.context.get_aris_frametime_ext(aris_start_idx))
        gopro_end_idx = self.context.aristime_to_gopro_idx(self.context.get_aris_frametime_ext(aris_end_idx))
        self.flow_plot2.set_xlim([gopro_start_idx, gopro_end_idx])
        self.flow_playback_marker.set_xdata([self.context.aris_frame_idx, self.context.aris_frame_idx])
        self.flow_fig.canvas.draw_idle()

        # Gantry
        gantry_odom, gantry_time = self.context.get_gantry_odom(aris_frametime)
        gantry_progress = int((gantry_time - self.context.gantry_t0) / self.context.gantry_duration * 1000)
        self.gantry_offset_marker.set_xdata([gantry_time - self.context.gantry_t0, gantry_time - self.context.gantry_t0])
        self.slider_gantry_pos.setValue(gantry_progress)
        self.spinner_gantry_pos.setValue(gantry_progress)
        self.gantry_fig.canvas.draw_idle()
        
        self.dirty = False
    
    def reset_context(self):
        self.refresh_dropdowns()
        
        aris_idx = self.dropdown_select_aris.currentIndex()
        gopro_idx = self.dropdown_select_gopro.currentIndex()
        gantry_idx = self.dropdown_select_gantry.currentIndex()
        
        aris_file = self.aris_data_dirs[aris_idx]
        gopro_file = self.gopro_files[gopro_idx]
        gantry_file = self.gantry_files[gantry_idx]
        
        self.context = MatchingContext(aris_file, gopro_file, gantry_file)
        
        self.context.aris_tick_step = self.spinner_playback_fpu.value()
        
        # We can skip so much of the gopro clip that it barely starts playing
        range_min = -int(self.context.aris_duration / 10e3 // self.context.gopro_fps)
        # But we can also delay playback so much that it barely starts playing
        range_max = int(self.context.gopro_frames_total)
        
        self.slider_aris_pos.setMaximum(int(self.context.aris_frames_total - 1))
        self.spinner_aris_pos.setMaximum(int(self.context.aris_frames_total - 1))
        self.slider_gopro_pos.setMaximum(int(self.context.gopro_frames_total - 1))
        self.spinner_gopro_pos.setMaximum(int(self.context.gopro_frames_total - 1))
        self.slider_gantry_pos.setMaximum(1000)
        self.spinner_gantry_pos.setMaximum(1000)
        
        self.slider_gopro_offset.setRange(range_min, range_max)
        self.spinner_gopro_offset.setRange(range_min, range_max)
        
        self.rangeslider_aris.setMin(0)
        self.rangeslider_aris.setMax(self.context.aris_frames_total - 1)
        self.rangeslider_aris.setRange(self.context.aris_start_frame, self.context.aris_end_frame)
        self.rangeslider_aris.update()
        
        gantry_offset_s, gantry_offset_ms, gantry_offset_us = split_microseconds(self.context.gantry_offset)
        self.slider_gantry_offset_s.setValue(gantry_offset_s)
        self.slider_gantry_offset_ms.setValue(gantry_offset_ms)
        self.slider_gantry_offset_us.setValue(gantry_offset_us)
        
        # Prepare the optical flow plot. Only the gopro's flow plot will change as the offset is updated.
        self.flow_plot.cla()
        self.flow_plot.set_xticks(np.arange(0, self.context.aris_frames_total, self.context.aris_frames_total // 20))
        self.flow_plot.set_xticklabels([])
        self.flow_plot.get_xaxis().grid(which='both')
        aris_flow_x = np.arange(self.context.aris_frames_total)
        aris_flow_y = self.context.aris_optical_flow
        self.flow_plot.plot(aris_flow_x, aris_flow_y, 'b', label='aris')
        self.flow_playback_marker = self.flow_plot.axvline(0, color='orange')
        
        self.flow_plot2.cla()
        self.flow_plot2.set_ylim([0, 1])
        gopro_flow_x = np.arange(self.context.gopro_frames_total)
        gopro_flow_y = self.context.gopro_optical_flow
        self.flow_plot2.plot(gopro_flow_x, gopro_flow_y, 'r', label='gopro')
        
        # Prepare the gantry plot. As we update, we will only move the vertical line marker across.
        self.gantry_plot.cla()
        gantry_data = self.context.gantry_data
        self.gantry_plot.set_xlim([0, self.context.gantry_duration])
        gantry_t = gantry_data['timestamp_us'] - self.context.gantry_t0
        self.gantry_plot.plot(gantry_t, gantry_data['x'], 'r', label='x')
        self.gantry_plot.plot(gantry_t, gantry_data['y'], 'g', label='y')
        self.gantry_plot.plot(gantry_t, gantry_data['z'], 'b', label='z')
        self.gantry_offset_marker = self.gantry_plot.axvline(self.context.gantry_offset, color='orange')
        self.canvas_gantry_plot.setStyleSheet('background-color:none;')  # TODO not working yet
        
        association: Association = self.association_details.get(aris_idx)
        if association and (not association.has_gopro() or association.gopro_idx == gopro_idx) and (not association.has_gantry() or association.gantry_idx == gantry_idx):
                self.notes_widget.setPlainText(association.notes)
                self.check_associate_gopro.setChecked(association.has_gopro())
                self.check_associate_gantry.setChecked(association.has_gantry())
        else:
            self.notes_widget.setPlainText('')
            #self.check_associate_gopro.setChecked(True)
            #self.check_associate_gantry.setChecked(True)
        
        self.context.reload = False

    def reload(self):
        if self.context:
            self.context.reload = True
            self.ensure_update()



if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--day', choices=['1', '2'], help="Load datasets from 'data/[aris|gopro|gantry]/day<X>/")
    group.add_argument('--dirs', nargs=3, metavar=('ARIS_DIR', 'GOPRO_DIR', 'GANTRY_DIR'), help="Load datasets from the provided directories")
    args = parser.parse_args()
    
    if args.day in ['1', '2']:
        aris_dir_path = f'data/aris/day{args.day}/'
        gopro_dir_path = f'data/gopro/day{args.day}/clips_sd/'
        gantry_dir_path = f'data/gantry/day{args.day}/'
    else:
        aris_dir_path, gopro_dir_path, gantry_dir_path = args.dirs
    
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(aris_dir_path, gopro_dir_path, gantry_dir_path)
    sys.exit(app.exec_())
