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


class MatchingContext:
    def __init__(self, aris_dir, gantry_file, gopro_file):
        self.aris_basename = basename(aris_dir)
        self.gantry_basename = basename(gantry_file)
        self.gopro_basename = basename(gopro_file)
        
        self.aris_meta = pd.read_csv(os.path.join(aris_dir, self.aris_basename + '_frames.csv'))
        self.aris_frames = sorted(os.path.join(aris_dir, f) for f in os.listdir(aris_dir) if f.lower().endswith('.pgm'))
        self.gantry_data = pd.read_csv(gantry_file)
        self.gopro_clip = cv2.VideoCapture(gopro_file)
        
        # Start at -1, this way the first call to tick() will move it to 0
        self._aris_frame_idx = 0
        self._aris_frames_start = 0
        self._aris_frames_end = len(self.aris_frames) - 1
        self.aris_motion_onset = 0
        self.aris_frames_total = len(self.aris_frames)
        self.aris_t0 = self.aris_meta.at[0, 'FrameTime']
        self.aris_duration = self.aris_meta.at[self.aris_frames_total - 1, 'FrameTime'] - self.aris_t0
        self.aris_img = None
        
        # Create microsecond timestamps 
        self.gantry_data['t'] = self.gantry_data['timestamp_s'] * 1e6 + self.gantry_data['timestamp_ns'] / 1e3

        # Load beginning of motion frame from save file
        marks_file_path = os.path.join(aris_dir, self.aris_basename + '_marks.yaml')
        if os.path.exists(marks_file_path):
            print(f'Found save file for {self.aris_basename}')
            with open (marks_file_path, 'r') as f:
                marks = yaml.safe_load(f)
                onset = max(0, marks.get('onset', 0))
                self._aris_frames_start = onset
                self.aris_motion_onset = onset
        
        self.gopro_frame_idx = -1
        self.gopro_frames_total = self.gopro_clip.get(cv2.CAP_PROP_FRAME_COUNT)
        self.gopro_fps = self.gopro_clip.get(cv2.CAP_PROP_FPS)
        self.gopro_offset = 0
        self.gopro_img = None
        
        self.gantry_offset = 0.
        self.gantry_t0 = self.gantry_data.at[0, 't']
        self.gantry_duration = self.gantry_data.at[self.gantry_data.shape[0] - 1, 't'] - self.gantry_t0
        
        self.reload = True
        
    @property
    def aris_frame_idx(self):
        return self._aris_frame_idx
    
    @aris_frame_idx.setter
    def aris_frame_idx(self, new_val):
        if self.aris_frames_start < new_val < self.aris_frames_end:
            self._aris_frame_idx = new_val
        else:
            self._aris_frame_idx = self.aris_frames_start
        self.aris_img = None
    
    @property
    def aris_frames_start(self):
        return self._aris_frames_start
    
    @aris_frames_start.setter
    def aris_frames_start(self, new_val):
        self._aris_frames_start = min(new_val, self.aris_frames_end - 1)
        self.aris_frame_idx = max(self.aris_frames_start, self.aris_frame_idx)
        
    @property
    def aris_frames_end(self):
        return self._aris_frames_end
    
    @aris_frames_end.setter
    def aris_frames_end(self, new_val):
        self._aris_frames_end = max(new_val, self.aris_frames_start + 1)
        self.aris_frame_idx = min(self.aris_frame_idx, self.aris_frames_end)
    
    @property
    def aris_active_frames(self):
        return self.aris_frames_end - self.aris_frames_start
    
    @property
    def aris_active_duration(self):
        return self.aris_meta.at[self.aris_frames_end, 'FrameTime'] - self.aris_meta.at[self.aris_frames_start, 'FrameTime']
    
    
    def tick(self):
        self.aris_img = None
        self.aris_frame_idx += 1
        
    def get_aris_frame(self):
        # FrameTime = time of recording on PC (µs since 1970)
        # sonarTimeStamp = time of recording on sonar (µs since 1970), not sure if synchronized to PC time
        frametime = self.aris_meta.at[self.aris_frame_idx, 'FrameTime']
        timeoffset = frametime - self.aris_t0
        if self.aris_img is None:
            self.aris_img = QtGui.QPixmap(self.aris_frames[self.aris_frame_idx])
        return self.aris_img, timeoffset
    
    def get_gopro_frame(self, aris_timeoffset):
        # TODO aris frametime is in microseconds, then why does 1e3 seem correct???
        new_frame_idx = int(aris_timeoffset / 1e3 // self.gopro_fps) + self.gopro_offset
        
        if new_frame_idx != self.gopro_frame_idx:
            self.gopro_frame_idx = new_frame_idx
            self.gopro_clip.set(cv2.CAP_PROP_POS_FRAMES, self.gopro_frame_idx)
            has_frame, gopro_frame = self.gopro_clip.read()
            if has_frame:
                img = cv2.cvtColor(gopro_frame, cv2.COLOR_BGR2RGB)
                q_img = QtGui.QImage(img, img.shape[1], img.shape[0], QtGui.QImage.Format_RGB888)
                self.gopro_img = QtGui.QPixmap(q_img)
        
        return self.gopro_img, self.gopro_frame_idx
        
    def get_gantry_odom(self, aris_timeoffset):
        # ARIS and gantry data use absolute timestamps
        timepos = ((self.aris_t0 + aris_timeoffset) + self.gantry_offset / 1000)
        t = self.gantry_data['t']   
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
    def __init__(self, aris_data_dirs, gantry_files, gopro_files, out_file_path, autoplay=False):
        super().__init__()
        
        self.aris_associated = set()
        self.gopro_associated = set()
        self.gantry_associated = set()
        self.association_details = {}
        
        # Keep track of the files we're using
        self.aris_data_dirs = aris_data_dirs
        self.gantry_files = gantry_files
        self.gopro_files = gopro_files
        self.out_file_path = out_file_path
        
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
        
        self.slider_aris_pos = MySlider()
        self.slider_aris_pos.valueChanged[int].connect(self._handle_aris_pos_slider)
        self.spinner_aris_pos = QtWidgets.QSpinBox()
        self.spinner_aris_pos.valueChanged[int].connect(self._handle_aris_pos_spinner)
        
        self.rangeslider_aris = QRangeSlider()
        self.rangeslider_aris.startValueChanged.connect(self._handle_aris_range_start_changed)
        self.rangeslider_aris.endValueChanged.connect(self._handle_aris_range_end_changed)
        
        # Gopro sliders and spinners
        self.slider_gopro_pos = MySlider()
        self.slider_gopro_pos.setEnabled(False)
        self.spinner_gopro_pos = QtWidgets.QSpinBox()
        self.spinner_gopro_pos.setEnabled(False)
        
        self.slider_gopro_offset = MySlider()
        self.slider_gopro_offset.setSingleStep(1)
        self.slider_gopro_offset.setPageStep(10)
        self.slider_gopro_offset.valueChanged[int].connect(self._handle_gopro_offset_slider)
        self.spinner_gopro_offset = QtWidgets.QSpinBox()
        self.spinner_gopro_offset.setSingleStep(1)
        self.spinner_gopro_offset.valueChanged.connect(self._handle_gopro_offset_spinner)
        
        # TODO Gantry sliders and spinners
        self.slider_gantry_pos = MySlider()
        self.slider_gantry_pos.setMaximum(1000)
        self.slider_gantry_pos.setEnabled(False)
        self.spinner_gantry_pos = QtWidgets.QSpinBox()
        self.spinner_gantry_pos.setMaximum(1000)
        self.spinner_gantry_pos.setEnabled(False)
        
        # Buttons and instructions
        # TODO instructions
        self.button_play_pause = QtWidgets.QPushButton('&Play / Pause')
        self.button_play_pause.clicked.connect(self._handle_play_pause_button)
        
        self.button_associate = QtWidgets.QPushButton('&Associate')
        self.button_associate.clicked.connect(self._handle_associate_button)
        
        self.button_save = QtWidgets.QPushButton('&Save')
        self.button_save.clicked.connect(self._handle_save_button)
        
        # Interactive elements layout
        ui_layout = QtWidgets.QVBoxLayout()
        ui_layout.addWidget(QtWidgets.QLabel("ARIS dataset"), )
        ui_layout.addWidget(self.dropdown_select_aris)
        ui_layout.addWidget(QtWidgets.QLabel("GoPro clip"))
        ui_layout.addWidget(self.dropdown_select_gopro)
        ui_layout.addWidget(QtWidgets.QLabel("Gantry dataset"))
        ui_layout.addWidget(self.dropdown_select_gantry)
        
        ui_layout.addWidget(QtWidgets.QLabel(""))
        
        ui_layout.addWidget(QtWidgets.QLabel("Aris Frame"))
        ui_layout.addWidget(self.slider_aris_pos)
        ui_layout.addWidget(self.spinner_aris_pos)
        ui_layout.addWidget(self.rangeslider_aris)
        
        ui_layout.addWidget(QtWidgets.QLabel(""))
        ui_layout.addWidget(QtWidgets.QLabel("GoPro Frame"))
        ui_layout.addWidget(self.slider_gopro_pos)
        ui_layout.addWidget(self.spinner_gopro_pos)
        ui_layout.addWidget(QtWidgets.QLabel("GoPro Offset"))
        ui_layout.addWidget(self.slider_gopro_offset)
        ui_layout.addWidget(self.spinner_gopro_offset)
        
        ui_layout.addWidget(QtWidgets.QLabel(""))
        ui_layout.addWidget(QtWidgets.QLabel("Gantry Progress"))
        ui_layout.addWidget(self.slider_gantry_pos)
        ui_layout.addWidget(self.spinner_gantry_pos)
        
        ui_layout.addWidget(QtWidgets.QLabel(""))
        
        ui_layout.addWidget(self.button_play_pause)
        ui_layout.addWidget(self.button_associate)
        ui_layout.addWidget(self.button_save)
        
        ui_layout.addStretch()

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
        self.update_timer.setInterval(1000 // 15)  # TODO make configurable
        self.update_timer.start()
        
        self.reset_context()
        self.show()
    
    @QtCore.pyqtSlot(int)
    def _handle_aris_pos_slider(self, val):
        self.context.aris_frame_idx = val
        self.spinner_aris_pos.setValue(val)
        self.ensure_update()

    @QtCore.pyqtSlot(int)
    def _handle_aris_pos_spinner(self, val):
        self.context.aris_frame_idx = val
        self.slider_aris_pos.setValue(val)
        self.ensure_update()

    @QtCore.pyqtSlot(int)
    def _handle_aris_range_start_changed(self, val):
        self.context.aris_frames_start = val
        self.ensure_update()
    
    @QtCore.pyqtSlot(int)
    def _handle_aris_range_end_changed(self, val):
        self.context.aris_frames_end = val
        self.ensure_update()

    @QtCore.pyqtSlot(int)
    def _handle_gopro_offset_slider(self, val):
        self.context.gopro_offset = val
        self.spinner_gopro_offset.setValue(val)
        self.ensure_update()
    
    @QtCore.pyqtSlot(int)
    def _handle_gopro_offset_spinner(self, val):
        self.context.gopro_offset = val
        self.slider_gopro_offset.setValue(val)
        self.ensure_update()

    def _handle_play_pause_button(self):
        self.playing = not self.playing

    def _handle_associate_button(self):
        association = Association(
            self.dropdown_select_aris.currentIndex(),
            self.dropdown_select_gopro.currentIndex(),
            self.dropdown_select_gantry.currentIndex(),
            self.context.aris_motion_onset,
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
        def mark_if_associated(name, idx, container):
            return f'* {name}' if idx in container else name
        
        def repopulate(dropdown, items, association_set):
            idx = max(0, dropdown.currentIndex())
            dropdown.currentIndexChanged.disconnect()
            dropdown.clear()
            dropdown.addItems([mark_if_associated(basename(f), i, association_set) for i,f in enumerate(items)])
            dropdown.setCurrentIndex(idx)
            dropdown.currentIndexChanged.connect(self.reload)
        
        # TODO mark ARIS files that have an onset in their metadata
        # TODO filter GANTRY files that overlap with the selected ARIS timerange
        # TODO use relative GANTRY playback
        # TODO read GANTRY offsets from metadata 
        # TODO regenerate GANTRY metadata
        
        repopulate(self.dropdown_select_aris, self.aris_data_dirs, self.aris_associated)
        repopulate(self.dropdown_select_gopro, self.gopro_files, self.gopro_associated)
        repopulate(self.dropdown_select_gantry, self.gantry_files, self.gantry_associated)
        
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

    def reset_context(self):
        aris_file = self.aris_data_dirs[self.dropdown_select_aris.currentIndex()]
        gantry_file = self.gantry_files[self.dropdown_select_gantry.currentIndex()]
        gopro_file = self.gopro_files[self.dropdown_select_gopro.currentIndex()]
        
        self.context = MatchingContext(aris_file, gantry_file, gopro_file)
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
        self.rangeslider_aris.setRange(self.context.aris_frames_start, self.context.aris_frames_end)
        self.rangeslider_aris.update()
        
        # Prepare the gantry plot. As we update, we will only move the vertical line marker across.
        gantry_data = self.context.gantry_data
        self.gantry_plot.set_xlim([0, self.context.gantry_duration])
        gantry_t_rel = gantry_data['t'] - self.context.gantry_t0
        self.gantry_plot.plot(gantry_t_rel, gantry_data['x'], 'r', label='x')
        self.gantry_plot.plot(gantry_t_rel, gantry_data['y'], 'g', label='y')
        self.gantry_plot.plot(gantry_t_rel, gantry_data['z'], 'b', label='z')
        self.gantry_offset_marker = self.gantry_plot.axvline(0, color='orange')
        self.plot_canvas.setStyleSheet('background-color:none;')  # TODO not working yet
        
        self.context.reload = False

    def reload(self):
        if self.context:
            self.context.reload = True
            self.ensure_update()

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
        aris_frame, aris_timeoffset = self.context.get_aris_frame()
        self.slider_aris_pos.setValue(self.context.aris_frame_idx)
        self.aris_canvas.setPixmap(aris_frame)
        
        # GoPro
        gopro_frame, gopro_frame_idx = self.context.get_gopro_frame(aris_timeoffset)
        if gopro_frame:
            self.gopro_canvas.setPixmap(gopro_frame)
            self.slider_gopro_pos.setValue(gopro_frame_idx)
            self.spinner_gopro_pos.setValue(gopro_frame_idx)
        else:
            print(f'no gopro frame for {aris_timeoffset}, this may be a bug')

        # Gantry
        gantry_odom, gantry_time = self.context.get_gantry_odom(aris_timeoffset)
        gantry_progress = int((gantry_time - self.context.gantry_t0) / self.context.gantry_duration * 1000)
        # TODO warn if outside range, i.e. timestamps don't match 
        print(gantry_progress)
        self.gantry_offset_marker.set_xdata([gantry_time, gantry_time])
        self.slider_gantry_pos.setValue(gantry_progress)
        self.spinner_gantry_pos.setValue(gantry_progress)

        self.fig.canvas.draw_idle()
        self.dirty = False
    


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
