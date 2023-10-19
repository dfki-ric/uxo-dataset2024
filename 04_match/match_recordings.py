#!/usr/bin/env python
import sys
import os
import csv
import yaml
import numpy as np
import pandas as pd
import cv2
from dataclasses import dataclass, asdict
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtGui, QtWidgets
from qrangeslider import QRangeSlider


def usage():
    print(f'{sys.argv[0]} <aris-folder> <gantry-folger> <gopro-folder> <output_file.csv>')


def basename(s):
    return os.path.split(s)[-1]

def split_microseconds(timestamp_us):
    s = int(timestamp_us // 1e6)
    ms = int((timestamp_us - s * 1e6) // 1e3)
    us = int(timestamp_us - s * 1e6 - ms * 1e3)
    return s, ms, us

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


_gantry_metadata_cache = {}
def get_gantry_metadata(gantry_files_dir):
    if gantry_files_dir in _gantry_metadata_cache:
        return _gantry_metadata_cache[gantry_files_dir]
    
    metadata = pd.read_csv(os.path.join(gantry_files_dir, 'gantry_metadata.csv'))
    _gantry_metadata_cache[gantry_files_dir] = metadata
    return metadata


class MatchingContext:
    def __init__(self, aris_dir, gopro_file, gantry_file):
        self.aris_basename = basename(aris_dir)
        self.gopro_basename = basename(gopro_file)
        self.gantry_basename = basename(gantry_file)
        
        self.aris_file_meta, self.aris_frames_meta, self.aris_marks_meta = get_aris_metadata(aris_dir)
        self.aris_frames = sorted(os.path.join(aris_dir, f) for f in os.listdir(aris_dir) if f.lower().endswith('.pgm'))
        self.gopro_clip = cv2.VideoCapture(gopro_file)
        self.gantry_data = pd.read_csv(gantry_file)
        
        # Start at -1, this way the first call to tick() will move it to 0
        self._aris_frame_idx = 0
        self._aris_start_frame = 0
        self._aris_end_frame = len(self.aris_frames) - 1
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
        
        self.gopro_frame_idx = -1
        self.gopro_frames_total = self.gopro_clip.get(cv2.CAP_PROP_FRAME_COUNT)
        self.gopro_fps = self.gopro_clip.get(cv2.CAP_PROP_FPS)
        self.gopro_offset = 0
        self.gopro_img = None
        
        all_gantry_meta = get_gantry_metadata(os.path.dirname(gantry_file))
        self.gantry_meta = all_gantry_meta.loc[all_gantry_meta['file'] == self.gantry_basename].iloc[0]
        self.gantry_t0 = self.gantry_meta['start_us']
        self.gantry_duration = self.gantry_meta['end_us'] - self.gantry_t0
        self.gantry_offset = self.gantry_meta['onset_us'] - self.gantry_t0
        
        self.reload = True
    
    def get_aris_frametime(self, frame_idx):
        # FrameTime = time of recording on PC (µs since 1970)
        # sonarTimeStamp = time of recording on sonar (µs since 1970), not sure if synchronized to PC time
        return self.aris_frames_meta['FrameTime'].iloc[frame_idx]
    
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
        self.aris_frame_idx += 1
        
    def get_aris_frame(self):
        frametime = self.get_aris_frametime(self.aris_frame_idx)
        if self.aris_img is None:
            self.aris_img = QtGui.QPixmap(self.aris_frames[self.aris_frame_idx])
        return self.aris_img, frametime
    
    def get_gopro_frame(self, aris_frametime):
        # TODO aris frametime is in microseconds, then why does 1e3 seem correct for frames per SECOND?
        time_from_start = aris_frametime - self.aris_t0
        new_frame_idx = int(time_from_start / 1e3 // self.gopro_fps) + self.gopro_offset
        
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
    def __init__(self, aris_base_dir, gopro_base_dir, gantry_base_dir, out_file_path, autoplay=False):
        super().__init__()
        
        self.aris_associated = set()
        self.gopro_associated = set()
        self.gantry_associated = set()
        self.association_details = {}
        
        # Keep track of the files we're using
        self.aris_base_dir = aris_base_dir
        self.gopro_base_dir = gopro_base_dir
        self.gantry_base_dir = gantry_base_dir
        self.out_file_path = out_file_path
        
        self.aris_data_dirs = sorted(os.path.join(aris_base_dir, f) for f in os.listdir(aris_base_dir))
        self.gopro_files = sorted(os.path.join(gopro_base_dir, f) for f in os.listdir(gopro_base_dir) if f.lower().endswith('.mp4'))
        self.gantry_files = sorted(os.path.join(gantry_base_dir, f) for f in os.listdir(gantry_base_dir) if f.lower().endswith('.csv') and not 'metadata' in f.lower())
        
        # Everything else will be stored inside the context
        self.context = None
        self.dirty = False
        self.playing = autoplay
        
        # QT things
        self._main_widget = MainWidget(self)
        self._main_widget.keyPressed.connect(self._handle_keypress)
        
        # Plots
        self.aris_canvas = QtWidgets.QLabel()
        self.gopro_canvas = QtWidgets.QLabel()
        
        self.fig = Figure()
        self.gantry_plot = self.fig.add_subplot()
        self.gantry_plot.figure.tight_layout()
        
        self.plot_canvas = FigureCanvas(self.fig)
        self.plot_canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.plot_canvas.updateGeometry()
        
        # UI controls
        self.dropdown_select_aris = QtWidgets.QComboBox()
        self.dropdown_select_aris.currentIndexChanged.connect(self.reload)
        self.dropdown_select_gopro = QtWidgets.QComboBox()
        self.dropdown_select_gopro.currentIndexChanged.connect(self.reload)
        self.dropdown_select_gantry = QtWidgets.QComboBox()
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
        
        # Buttons and playback
        self.spinner_playback_fps = QtWidgets.QSpinBox()
        self.spinner_playback_fps.setRange(1, 60)
        self.spinner_playback_fps.setValue(15)
        self.spinner_playback_fps.valueChanged[int].connect(self._on_playback_fps_changed)
        
        self.button_play_pause = QtWidgets.QPushButton('&Play / Pause')
        self.button_play_pause.clicked.connect(self._handle_play_pause_button)
        
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
        ctrl_layout.addWidget(QtWidgets.QLabel("Aris Frame"), 8, 0, 1, -1)
        ctrl_layout.addWidget(self.slider_aris_pos, 9, 0)
        ctrl_layout.addWidget(self.spinner_aris_pos, 9, 1)
        ctrl_layout.addWidget(QtWidgets.QLabel("f"), 9, 2)
        ctrl_layout.addWidget(self.rangeslider_aris, 10, 0, 1, -1)
        
        ctrl_layout.addWidget(QtWidgets.QLabel(""), 11, 0, 1, -1)
        ctrl_layout.addWidget(QtWidgets.QLabel("GoPro Frame"), 12, 0, 1, -1)
        ctrl_layout.addWidget(self.slider_gopro_pos, 13, 0)
        ctrl_layout.addWidget(self.spinner_gopro_pos, 13, 1)
        ctrl_layout.addWidget(QtWidgets.QLabel("f"), 13, 2)
        ctrl_layout.addWidget(QtWidgets.QLabel("GoPro Offset"), 14, 0, 1, -1)
        ctrl_layout.addWidget(self.slider_gopro_offset, 15, 0)
        ctrl_layout.addWidget(self.spinner_gopro_offset, 15, 1)
        ctrl_layout.addWidget(QtWidgets.QLabel("f"), 15, 2)
        
        ctrl_layout.addWidget(QtWidgets.QLabel(""), 16, 0, 1, -1)
        ctrl_layout.addWidget(QtWidgets.QLabel("Gantry Progress"), 17, 0, 1, -1)
        ctrl_layout.addWidget(self.slider_gantry_pos, 18, 0)
        ctrl_layout.addWidget(self.spinner_gantry_pos, 18, 1)
        ctrl_layout.addWidget(QtWidgets.QLabel("%"), 18, 2)
        
        ctrl_layout.addWidget(QtWidgets.QLabel(""), 19, 0, 1, -1)
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
        
        ui_layout.addStretch()

        ui_layout.addWidget(QtWidgets.QLabel("Max. Playback FPS"))
        ui_layout.addWidget(self.spinner_playback_fps)
        
        ui_layout.addWidget(QtWidgets.QLabel(""))
        ui_layout.addWidget(self.button_play_pause)
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

        # UI Layout
        ui_layout_wrapper = QtWidgets.QWidget()
        ui_layout_wrapper.setLayout(ui_layout)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(ui_layout_wrapper)
        splitter.addWidget(self.table_associations)
        splitter.setStretchFactor(100, 50)
        
        self.layout = QtWidgets.QGridLayout(self._main_widget)
        self.layout.addWidget(self.aris_canvas, 0, 0, 2, 1)
        self.layout.addWidget(self.gopro_canvas, 0, 1)
        self.layout.addWidget(self.plot_canvas, 1, 1)
        self.layout.addWidget(splitter, 0, 2, 2, 1)
        #self.layout.addLayout(ui_layout, 0, 2, 2, 1)
        #self.layout.addWidget(self.table_associations, 0, 3, 2, 1)
        self.layout.setColumnStretch(2, 50)
        #self.layout.setColumnStretch(4, 100)

        self.setCentralWidget(self._main_widget)
        
        # Update in regular intervals
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.do_update)
        self.update_timer.setInterval(1000 // self.spinner_playback_fps.value())
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
    def _on_playback_fps_changed(self, val):
        self.update_timer.setInterval(1000 // val)


    def _handle_play_pause_button(self):
        self.playing = not self.playing

    def _handle_associate_button(self):
        association = Association(
            self.dropdown_select_aris.currentIndex(),
            self.dropdown_select_gopro.currentIndex(),
            self.dropdown_select_gantry.currentIndex(),
            self.context.aris_start_frame,
            self.context.gopro_offset,
            self.context.gantry_offset
        )
        
        # Check if there was a previous association with any of the files; if so, remove it
        old_association = None
        if association.aris_idx in self.aris_associated:
            old_association = self.association_details[association.aris_idx]
        elif association.gopro_idx in self.gopro_associated:
            for a in self.association_details.values():
                if a.gopro_idx == association.gopro_idx:
                    old_association = a
                    break
        elif association.gantry_idx in self.gantry_associated:
            for a in self.association_details.values():
                if a.gantry_idx == association.gantry_idx:
                    old_association = a
                    break
        
        if old_association is not None:
            self.aris_associated.discard(old_association.aris_idx)
            self.gopro_associated.discard(old_association.gopro_idx)
            self.gantry_associated.discard(old_association.gantry_idx)
            del self.association_details[old_association.aris_idx]
            
            self.table_associations.setItem(old_association.aris_idx, 1, None)
            self.table_associations.setItem(old_association.aris_idx, 2, None)
        
        # Store new association
        self.aris_associated.add(association.aris_idx)
        self.gopro_associated.add(association.gopro_idx)
        self.gantry_associated.add(association.gantry_idx)
        self.association_details[association.aris_idx] = association
        
        # Update table
        self.table_associations.setItem(association.aris_idx, 1, QtWidgets.QTableWidgetItem(self.context.gopro_basename))
        self.table_associations.setItem(association.aris_idx, 2, QtWidgets.QTableWidgetItem(self.context.gantry_basename))
        
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
        aris_items = []
        aris_frames_meta = None
        for idx,item in enumerate(self.aris_data_dirs):
            aris_metadata = get_aris_metadata(item)
            marks = aris_metadata[2]
            if idx == max(0, self.dropdown_select_aris.currentIndex()):
                aris_frames_meta = aris_metadata[1]
            associated = '*' if idx in self.aris_associated else ' '
            motion_onset = 'm' if 'onset' in marks else ' '
            aris_items.append(f'({associated}) ({motion_onset}) {item}')
        
        gopro_items = []
        for idx,item in enumerate(self.gopro_files):
            associated = '*' if idx in self.gopro_associated else ' '
            # GoPro clips are already cut to where the motion starts
            gopro_items.append(f'({associated}) {item}')
        
        gantry_items = []
        gantry_metadata = get_gantry_metadata(self.gantry_base_dir)
        # Context may not be initialized yet, so don't use context.get_aris_frametime()
        current_aris_start = aris_frames_meta['FrameTime'][0]
        current_aris_end = aris_frames_meta['FrameTime'].iloc[-1]
        for idx,item in enumerate(self.gantry_files):
            gantry_file_meta = gantry_metadata.iloc[idx]
            gantry_file_start = gantry_file_meta['start_us']
            gantry_file_end = gantry_file_meta['end_us']
            associated = '*' if idx in self.gantry_associated else ' '
            # mark gantry files which have timestamps overlapping with selected ARIS file
            overlapping = 'x' if gantry_file_start < current_aris_end and gantry_file_end > current_aris_start else ' '
            gantry_items.append(f'({associated}) ({overlapping}) {item}')
        
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
        self.aris_canvas.setPixmap(aris_frame)
        
        # GoPro
        gopro_frame, gopro_frame_idx = self.context.get_gopro_frame(aris_frametime)
        if gopro_frame:
            self.gopro_canvas.setPixmap(gopro_frame)
            self.slider_gopro_pos.setValue(gopro_frame_idx)
            self.spinner_gopro_pos.setValue(gopro_frame_idx)
        else:
            print(f'no gopro frame for {aris_frametime - self.context.aris_t0}, this may be a bug')

        # Gantry
        gantry_odom, gantry_time = self.context.get_gantry_odom(aris_frametime)
        gantry_progress = int((gantry_time - self.context.gantry_t0) / self.context.gantry_duration * 1000)
        self.gantry_offset_marker.set_xdata([gantry_time - self.context.gantry_t0, gantry_time - self.context.gantry_t0])
        self.slider_gantry_pos.setValue(gantry_progress)
        self.spinner_gantry_pos.setValue(gantry_progress)
        
        self.fig.canvas.draw_idle()
        self.dirty = False
    
    def reset_context(self):
        self.refresh_dropdowns()
        
        aris_file = self.aris_data_dirs[self.dropdown_select_aris.currentIndex()]
        gopro_file = self.gopro_files[self.dropdown_select_gopro.currentIndex()]
        gantry_file = self.gantry_files[self.dropdown_select_gantry.currentIndex()]
        
        self.context = MatchingContext(aris_file, gopro_file, gantry_file)
        self.gantry_plot.cla()
        
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
        
        # Prepare the gantry plot. As we update, we will only move the vertical line marker across.
        gantry_data = self.context.gantry_data
        self.gantry_plot.set_xlim([0, self.context.gantry_duration])
        gantry_t = gantry_data['timestamp_us'] - self.context.gantry_t0
        self.gantry_plot.plot(gantry_t, gantry_data['x'], 'r', label='x')
        self.gantry_plot.plot(gantry_t, gantry_data['y'], 'g', label='y')
        self.gantry_plot.plot(gantry_t, gantry_data['z'], 'b', label='z')
        self.gantry_offset_marker = self.gantry_plot.axvline(self.context.gantry_offset, color='orange')
        self.plot_canvas.setStyleSheet('background-color:none;')  # TODO not working yet
        
        self.context.reload = False

    def reload(self):
        if self.context:
            self.context.reload = True
            self.ensure_update()



if __name__ == '__main__':
    # TODO
    sys.argv = [sys.argv[0], 'data/aris/day1/', 'data/gantry/day1/', 'data/gopro/day1/clips_sd/', 'out.csv']
    
    if len(sys.argv) != 5:
        usage()
        raise RuntimeError('Wrong number of arguments')
    
    aris_dir_path = sys.argv[1]
    gopro_dir_path = sys.argv[3]
    gantry_dir_path = sys.argv[2]
    out_file_path = sys.argv[4]
    
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(aris_dir_path, gopro_dir_path, gantry_dir_path, out_file_path)
    sys.exit(app.exec_())
