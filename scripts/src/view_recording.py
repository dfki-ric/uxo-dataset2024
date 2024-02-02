#!/usr/bin/env python3

import sys
import os
from functools import lru_cache
import yaml
import pandas as pd
import cv2
from PyQt5 import QtCore, QtGui, QtWidgets

from q_custom_widgets import MainWidget, MySlider


class DatasetViewer(QtWidgets.QMainWindow):
    def __init__(self, recording_dir: str, aris_polar: bool = True, aris_colorize: bool = True, use_cache: bool = False):
        super().__init__()
        
        self._recording_dir = recording_dir
        self._aris_polar = aris_polar
        self._aris_colorize = aris_colorize
        self._pos = 0
        self._load_recording(recording_dir, aris_polar=aris_polar)
        
        if use_cache:
            self.get_data = lru_cache(None)(self.get_data)
        
        # QT things
        self._main_widget = MainWidget(self)
        self._main_widget.keyPressed.connect(self._handle_keypress)
        
        # Plots
        self._canvas_aris = QtWidgets.QLabel()
        self._canvas_aris.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self._canvas_gopro = QtWidgets.QLabel()
        self._canvas_gopro.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        
        # Info boxes
        self._gantry_info = QtWidgets.QLabel()
        self._gantry_info.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self._notes_info = QtWidgets.QPlainTextEdit()
        self._notes_info.setReadOnly(True)
        self._notes_info.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self._frame_info = QtWidgets.QPlainTextEdit()
        self._frame_info.setReadOnly(True)
        self._frame_info.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        
        # Controls
        self._slider = MySlider()
        self._slider.setMaximum(len(self.aris_frames))
        self._slider.setSingleStep(1)
        self._slider.setPageStep(10)
        self._slider.valueChanged.connect(self._pos_set)
        
        info_boxes = QtWidgets.QHBoxLayout()
        info_boxes.addWidget(self._notes_info)
        info_boxes.addWidget(self._frame_info)
        
        right_side = QtWidgets.QVBoxLayout()
        right_side.addWidget(self._canvas_gopro)
        right_side.addWidget(self._gantry_info)
        right_side.addLayout(info_boxes)
        right_side_wrapper = QtWidgets.QWidget()
        right_side_wrapper.setLayout(right_side)
        
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(self._canvas_aris)
        splitter.addWidget(right_side_wrapper)
        
        self._layout = QtWidgets.QVBoxLayout(self._main_widget)
        self._layout.addWidget(splitter)
        self.setCentralWidget(self._main_widget)
        
        self.update()
        self.show()
    
    def _load_recording(self, recording_dir: str, aris_polar: bool = True):
        aris_dir = os.path.join(recording_dir, 'aris_' + 'polar' if aris_polar else 'raw')
        self.aris_frames = sorted([os.path.join(aris_dir, f) for f in os.listdir(aris_dir)])
        
        gopro_dir = os.path.join(recording_dir, 'gopro')
        self.gopro_frames = sorted([os.path.join(gopro_dir, f) for f in os.listdir(gopro_dir)])
        
        gantry_file = os.path.join(recording_dir, 'gantry.csv')
        self.gantry_data = pd.read_csv(gantry_file)
      
        self.aris_file_meta = yaml.safe_load(open(os.path.join(recording_dir, 'aris_file_meta.yaml')))
        self.aris_frame_meta = pd.read_csv(os.path.join(recording_dir, 'aris_frame_meta.csv'))
        
        self.notes = []
        notes_file = os.path.join(recording_dir, 'notes.txt')
        if os.path.isfile(notes_file):
            self.notes = [s.strip() for s in open(notes_file).readlines()]
        
    def _handle_keypress(self, key):
        if key == QtCore.Qt.Key.Key_Left:
            self._pos_adjust(-1)
        elif key == QtCore.Qt.Key.Key_Right:
            self._pos_adjust(1)
        elif key == QtCore.Qt.Key.Key_Down:
            self._pos_adjust(-10)
        elif key == QtCore.Qt.Key.Key_Up:
            self._pos_adjust(10)
        elif key == QtCore.Qt.Key.Key_Q:
            self.close()
        
    def _pos_adjust(self, steps):
        self._pos_set(self._pos + steps)
        
    def _pos_set(self, pos):
        self._pos = pos % len(self.aris_frames)
        self.update()
    
    def get_data(self, pos):
        if self._aris_colorize:
            aris_frame = cv2.imread(self.aris_frames[pos])
            aris_frame = cv2.applyColorMap(aris_frame, cv2.COLORMAP_TWILIGHT_SHIFTED)  # MAGMA, DEEPGREEN, OCEAN
            h, w, channels = aris_frame.shape
            aris = QtGui.QImage(aris_frame.data, w, h, channels * w, QtGui.QImage.Format_RGB888).rgbSwapped()
            aris = QtGui.QPixmap(aris)
        else:
            aris = QtGui.QPixmap(self.aris_frames[pos])
        
        if pos < len(self.gopro_frames):
            gopro = QtGui.QPixmap(self.gopro_frames[pos])
        else:
            gopro = None
        gantry = self.gantry_data.iloc[pos]
        frame_meta = self.aris_frame_meta.iloc[pos]
        
        return aris, gopro, gantry, frame_meta
    
    def update(self):
        aris, gopro, gantry, frame_meta = self.get_data(self._pos)
        
        self._canvas_aris.setPixmap(aris)
        self._canvas_gopro.setPixmap(gopro)
        self._gantry_info.setText('\n'.join(f'{k}: {v}' for k,v in gantry.to_dict().items()))
        self._frame_info.setPlainText('\n'.join(f'{k}: {v}' for k,v in frame_meta.to_dict().items()))
        self._notes_info.setPlainText('\n'.join(self.notes))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = DatasetViewer(sys.argv[1])
    sys.exit(app.exec_())
