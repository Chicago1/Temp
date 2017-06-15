from __future__ import print_function

__author__ = 'kylehenry' #testing
# Project: ptycho_gui

import os
import sys
import time
#import multiprocessing as mp
import matplotlib
from PyQt4 import (QtCore, QtGui)
from PyQt4.QtGui import QInputDialog
from PyQt4.QtCore import Qt
import numpy as np
import matplotlib as mpl
import h5py #-D
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

import scipy.misc as sm
import scipy.stats as st
import math
from scipy import interpolate
from scipy import ndimage
import matplotlib.pyplot as plt

#import align_class #kcode
#import ptycho_trans_parallel as ptycho #kcode

#from PIL import Image
import copy

import xml.etree.cElementTree as ET

CMAP_PREVIEW_PATH = os.path.join(os.path.dirname(__file__), '.cmap_previews')

get_save_filename = QtGui.QFileDialog.getSaveFileName
get_open_filename = QtGui.QFileDialog.getOpenFileName

class PtychoDialog(QtGui.QDialog):

    CM_DEFAULT = 'jet'

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        PtychoDialog.instance = self

        self._thread = None
        self.ion_data = None
        self.img_type = None
        self.crop_x0 = None
        self.crop_x1 = None
        self.crop_y0 = None
        self.crop_y1 = None
        self.image = None
        self.im = None
        self.colorbar = None
        self.set_roi_enabled = False
        self.bad_flag = 0
        self.orient_view = True #Changing this to True to fix issue with image being initialy bad -D
        self.thresh = False
        self.flippedud = False
        self.flippedlr = False #Changing this to True to fix issue with image being initialy bad -D
        self.transposed = False

        self.h5 = None


        def __del__(self):
            # Restore sys.stdout
            sys.stdout = sys.__stdout__

        self.vbox = QtGui.QVBoxLayout()
        self.tab_widget = QtGui.QTabWidget()
        self.tab_widget.setMinimumWidth(680)
        self.f = QtGui.QFrame()
        self.f_vbox = QtGui.QVBoxLayout()
        self.f.setLayout(self.f_vbox)
        self.tab1 = QtGui.QWidget()
        self.tab2 = QtGui.QWidget()
        self.tab3 = QtGui.QWidget()
        self.tab4 = QtGui.QWidget()
        self.tab1_vbox = QtGui.QVBoxLayout()
        self.tab2_vbox = QtGui.QVBoxLayout()
        self.tab3_vbox = QtGui.QVBoxLayout()
        self.tab4_vbox = QtGui.QVBoxLayout()
        self.advanced = False

        self.diffraction_data_options = ["Load from array", "Load from TIFF", "Read from metadata"]
        self.scan_pattern_options = ["Load from file", "Generate"]
        self.object_options = ["Load from file", "Random guess"]
        self.probe_options = ["Load from file", "Random guess"]

        self.setWindowTitle("Ptycho GUI")

        self.set_widgets()

        self.set_defaults()

        self.set_main_tab()

        self.set_canvas()

        self.rect = Rectangle((0, 0), 0, 0, alpha=0.3, facecolor='gray',
                              edgecolor='red', linewidth=2) #this changes the apperacne of the box -D
        #self.canvas.axes.add_patch(self.rect)
        self.show_rect = False
        self.rect_xy=0
        self.rect_height=0
        self.rect_width=0

        self.start_button.clicked.connect(self.start)
        self.start_button.setDefault(False)
        self.start_button.setAutoDefault(False)
        self.stop_button.clicked.connect(self.stop)
        self.stop_button.setDefault(False)
        self.stop_button.setAutoDefault(False)
        self.advanced_button.clicked.connect(self.toggle_advanced)
        self.advanced_button.setDefault(False)
        self.advanced_button.setAutoDefault(False)

        self._settings.append('last_path')

        self.tab1.setLayout(self.tab1_vbox)
        self.tab2.setLayout(self.tab2_vbox)
        self.tab3.setLayout(self.tab3_vbox)
        self.tab4.setLayout(self.tab4_vbox)

        self.tab_widget.addTab(self.tab1, "") #sets tabs -D #I removed tabs
        #self.tab_widget.addTab(self.tab2, "Experimental")
        #self.tab_widget.addTab(self.tab3, "Partial coherence")
        #self.tab_widget.addTab(self.tab4, "Position correction")

        self.splitter = QtGui.QSplitter()
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setLineWidth(1)

        self.splitter.addWidget(self.tab_widget)
        self.splitter.addWidget(self.canvas_gbox)

        self.vbox.addWidget(self.splitter)
        self.setLayout(self.vbox)

    def set_canvas(self):
        self.canvas = MplCanvas(width=20, height=0.25, dpi=50) #not this canvas#  -D
        self.canvas_gbox = QtGui.QGroupBox()
        self.canvas_vbox = QtGui.QVBoxLayout()
        self.canvas_gbox.setLayout(self.canvas_vbox)
        self.canvas_gbox.setMinimumWidth(500)
        self.canvas_gbox.setObjectName('canvasGbox')
        self.canvas_gbox.setStyleSheet("QGroupBox#canvasGbox { border:0; }")

        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event',
                                        self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

        self.scale_hbox = QtGui.QHBoxLayout()
        self.scale_label = QtGui.QLabel("Scale:")
        self.button_group1 = QtGui.QButtonGroup()
        self.lin_rbutton = QtGui.QRadioButton("Linear")
        self.log_rbutton = QtGui.QRadioButton("Logarithmic")
        self.button_group1.addButton(self.lin_rbutton)
        self.button_group1.addButton(self.log_rbutton)
        self.lin_rbutton.toggled.connect(self.canvas_linear)
        self.log_rbutton.toggled.connect(self.canvas_log)
        self.lin_rbutton.setChecked(True)
        #self.bar_label = QtGui.QLabel('|')
        self.button_group2 = QtGui.QButtonGroup()
        self.amp_rbutton = QtGui.QRadioButton("Amplitude")
        self.phase_rbutton = QtGui.QRadioButton("Phase")
        self.button_group2.addButton(self.amp_rbutton)
        self.button_group2.addButton(self.phase_rbutton)
        self.amp_rbutton.toggled.connect(self.canvas_amp)
        self.phase_rbutton.toggled.connect(self.canvas_phase)
        self.amp_rbutton.setEnabled(False)
        self.phase_rbutton.setEnabled(False)
        self.amp_rbutton.setChecked(True)

        self.slider_hbox = QtGui.QHBoxLayout()
        self.image_slider_label = QtGui.QLabel("Image slice:")
        self.image_slider = QtGui.QSlider(Qt.Horizontal)
        self.image_slider.valueChanged.connect(self.slide)
        self.image_slider.setMinimum(0)
        self.image_slider.setValue(0)
        self.image_slider.setEnabled(False)
        self.image_slice_qle = QtGui.QLineEdit()
        self.image_slice_qle.setEnabled(False)
        self.image_slice_qle.setMaximumWidth(50)
        self.image_slice_qle.returnPressed.connect(self.slide_from_qle)

        self.canvas_south1_hbox = QtGui.QHBoxLayout()
        self.color_map = QtGui.QComboBox()
        self.update_color_maps()
        self.color_map.currentIndexChanged.connect(self._set_color_map)
        self._color_map = mpl.cm.get_cmap(self.CM_DEFAULT)
        self.flip_ud_button = QtGui.QPushButton("Flip UD")
        self.flip_ud_button.setDefault(False)
        self.flip_ud_button.setAutoDefault(False)
        self.flip_lr_button = QtGui.QPushButton("Flip LR")
        self.flip_lr_button.setDefault(False)
        self.flip_lr_button.setAutoDefault(False)
        self.transpose_button = QtGui.QPushButton("Transpose")
        self.transpose_button.setDefault(False)
        self.transpose_button.setAutoDefault(False)
        self.flip_ud_button.clicked.connect(self.flip_ud)
        self.flip_lr_button.clicked.connect(self.flip_lr)
        self.transpose_button.clicked.connect(self.transpose_im)

        self.canvas_south2_hbox = QtGui.QHBoxLayout()
        #self.canvas_south2_grid = QtGui.QGridLayout()
        self.roi_gbox = QtGui.QGroupBox("ROI")
        self.roi_grid = QtGui.QGridLayout()
        #self.roi_grid.setVerticalSpacing(1)
        self.set_roi_button = QtGui.QPushButton("ROI")
        self.set_roi_button.setDefault(False)
        self.set_roi_button.setAutoDefault(False)
        self.set_roi_button.setCheckable(True)
        self.set_roi_button.clicked[bool].connect(self.set_roi_enable)

        self.normalize_button = QtGui.QPushButton("Norm")
        self.normalize_button.setDefault(False)
        self.normalize_button.setAutoDefault(False)
        self.normalize_button.setEnabled(False)

        self.subtract_button = QtGui.QPushButton("Sub")
        self.subtract_button.setDefault(False)
        self.subtract_button.setAutoDefault(False)
        self.subtract_button.setEnabled(False)

        self.save_pix_button = QtGui.QPushButton("Save h5")  # save function on right -D
        self.save_pix_button.setDefault(False)
        self.save_pix_button.setAutoDefault(False)


        # self.normalize_button.clicked.connect(self.apply_roi)

        self.normalize_button.clicked.connect(self.norm) #-D
        self.subtract_button.clicked.connect(self.sub)  # -D
        self.save_pix_button.clicked.connect(self.saveh5)  # -D



        self.bin_cb = QtGui.QCheckBox("Binning")
        self.bin_hbox = QtGui.QHBoxLayout()
        self.bin_qle1 = QtGui.QLineEdit("2")
        self.bin_qle1.setAlignment(QtCore.Qt.AlignHCenter)
        self.x_label = QtGui.QLabel("x")  #not tool bar coordinates -D
        self.bin_qle2 = QtGui.QLineEdit("2")
        self.bin_qle2.setAlignment(QtCore.Qt.AlignHCenter)
        self.bin_hbox.addWidget(self.bin_qle1)
        self.bin_hbox.addWidget(self.x_label)
        self.bin_hbox.addWidget(self.bin_qle2)
        self.square_cb = QtGui.QCheckBox("Square")
        self.bin_cb.stateChanged.connect(self.bin_action)
        self.roi_gbox.setLayout(self.roi_grid)
        self.roi_grid.addWidget(self.set_roi_button, 0, 0)
        self.roi_grid.addWidget(self.normalize_button, 0, 1)
        self.roi_grid.addWidget(self.subtract_button, 0, 2)
        self.roi_grid.addLayout(self.bin_hbox, 1, 0)
        self.roi_grid.addWidget(self.bin_cb, 1, 1)
        self.roi_grid.addWidget(self.square_cb, 2, 0)

        self.bad_pix_grid = QtGui.QGridLayout()
        #self.bad_pix_grid.setVerticalSpacing(1)
        self.bad_pix_gbox = QtGui.QGroupBox("Bad pixels")
        self.bad_pix_gbox.setLayout(self.bad_pix_grid)
        self.bad_pix_button = QtGui.QPushButton("Pick")
        self.bad_pix_button.setDefault(False)
        self.bad_pix_button.setAutoDefault(False)
        self.bad_pix_button.setCheckable(True)
        self.bad_pix_button.clicked[bool].connect(self.bad_enable)
        bpw = self.bad_pixels_widget = QtGui.QListWidget()
        #bpw.setMinimumHeight(1)
        bpw.setMaximumHeight(50)
        bpw.setContextMenuPolicy(Qt.CustomContextMenu)
        bpw.customContextMenuRequested.connect(self._bad_pixels_menu)
        #self.thresh_label = QtGui.QLabel("Threshold")
        self.thresh_cb = QtGui.QCheckBox("Threshold")
        self.thresh_cb.stateChanged.connect(self.apply_thresh)
        self.thresh_sb = QtGui.QDoubleSpinBox()
        self.thresh_sb.setMaximum(1e10)
        '''self.apply_thresh_button = QtGui.QPushButton("Apply")
        self.apply_thresh_button.setDefault(False)
        self.apply_thresh_button.setAutoDefault(False)
        self.apply_thresh_button.setCheckable(True)
        self.apply_thresh_button.clicked[bool].connect(self.apply_thresh)'''
        self.bad_pix_grid.addWidget(self.bad_pix_button, 0, 0)
        self.bad_pix_grid.addWidget(self.bad_pixels_widget, 0, 1, 2, 1)
        #self.bad_pix_grid.addWidget(self.save_pix_button, 0, 2)
        #self.bad_pix_grid.addWidget(self.load_pix_button, 1, 2)
        #self.bad_pix_grid.addWidget(self.thresh_label, 3, 0)
        self.bad_pix_grid.addWidget(self.thresh_cb, 3, 0)
        self.bad_pix_grid.addWidget(self.thresh_sb, 3, 1)
        #self.bad_pix_grid.addWidget(self.apply_thresh_button, 3, 2)

        self.save_and_load_grid = QtGui.QGridLayout()
        #self.save_and_load_grid.setVerticalSpacing(1)

        self.load_pix_button = QtGui.QPushButton("Load")
        self.load_pix_button.setDefault(False)
        self.load_pix_button.setAutoDefault(False)
        self.load_pix_button.clicked.connect(self.load_img_setup)
        spacer_label = QtGui.QLabel("")
        self.save_and_load_grid.addWidget(self.save_pix_button, 0, 0)
        self.save_and_load_grid.addWidget(self.load_pix_button, 1, 0)
        self.save_and_load_grid.addWidget(spacer_label, 2, 0)

        self.scale_hbox.addWidget(self.scale_label)
        self.scale_hbox.addWidget(self.lin_rbutton)
        self.scale_hbox.addWidget(self.log_rbutton)
        #self.scale_hbox.addWidget(self.bar_label)
        self.scale_hbox.addStretch(0)
        self.scale_hbox.addWidget(self.amp_rbutton)
        self.scale_hbox.addWidget(self.phase_rbutton)
        self.scale_hbox.addStretch(0)

        self.slider_hbox.addWidget(self.image_slider_label)
        self.slider_hbox.addWidget(self.image_slider)
        self.slider_hbox.addWidget(self.image_slice_qle)

        #self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        self.mpl_toolbar = MplToolbar(self.canvas, self)

        self.canvas_south1_hbox.addWidget(self.color_map)
        self.canvas_south1_hbox.addWidget(self.flip_ud_button)
        self.canvas_south1_hbox.addWidget(self.flip_lr_button)
        self.canvas_south1_hbox.addWidget(self.transpose_button)
        self.canvas_south1_hbox.addStretch(0)

        self.canvas_south2_hbox.addWidget(self.roi_gbox)
        self.canvas_south2_hbox.addWidget(self.bad_pix_gbox)
        self.canvas_south2_hbox.addLayout(self.save_and_load_grid)

        '''self.canvas_south2_grid.addWidget(self.roi_gbox, 0, 0)
        self.canvas_south2_grid.addWidget(self.bad_pix_gbox, 0, 1)
        self.canvas_south2_grid.addLayout(self.save_and_load_vbox, 0, 2)'''

        self.canvas_vbox.addLayout(self.scale_hbox)
        self.canvas_vbox.addLayout(self.slider_hbox)
        self.canvas_vbox.addWidget(self.canvas)
        self.canvas_vbox.addWidget(self.mpl_toolbar) #definitely the toolbar with the slice pixel values -D
        self.canvas_vbox.addLayout(self.canvas_south1_hbox)
        self.canvas_vbox.addLayout(self.canvas_south2_hbox)
        #self.canvas_vbox.addLayout(self.canvas_south2_grid)

        self.disable_mods()

    # refresh image with bin_cb checked/unchecked
    def bin_action(self):
        self.mod_image('cmap', reset_zoom=True)

    def bad_enable(self, pressed):
        """
        Enable or disable bad pixels selection by changing the bad_flag value
        """
        self.bad_flag = 1 if pressed else 0

    def _bad_pixels_menu(self, pos):
        def add():
            msg = 'Position in the format: x, y'
            s, ok = QInputDialog.getText(self, 'Position?', msg)
            if ok:
                s = str(s)
                x, y = s.split(',')
                x = int(x)
                y = int(y)
                self.bad_pixels_widget.addItem('%d, %d' % (x, y))
                self.mod_image('cmap')

        def remove():
            rows = [index.row() for index in
                    self.bad_pixels_widget.selectedIndexes()]
            for row in reversed(sorted(rows)):
                self.bad_pixels_widget.takeItem(row)

            self.mod_image('cmap')

        def clear():
            self.bad_pixels_widget.clear()
            self.mod_image('cmap')

        self.menu = menu = QtGui.QMenu()
        menu.addAction('&Add', add)
        menu.addAction('&Remove', remove)
        menu.addAction('&Clear', clear)

        menu.popup(self.bad_pixels_widget.mapToGlobal(pos))

    def on_press(self, event):
        if event.inaxes:
            self.crop_x0 = round(event.xdata)
            self.crop_y0 = round(event.ydata)

    def on_release(self, event):
        self.crop_x1 = round(event.xdata)#on release data
        self.crop_y1 = round(event.ydata)
        if event.inaxes:
            if (self.crop_x0, self.crop_y0) == (self.crop_x1, self.crop_y1):
                if self.bad_flag:
                    duplicate = False
                    for i in xrange(self.bad_pixels_widget.count()):
                        y, x = self.bad_pixels_widget.item(i).text().split(',')
                        y = int(y)
                        x = int(x)
                        if int(round(self.crop_x1)) == y and int(round(self.crop_y1)) == x:
                            duplicate = True

                    if not duplicate:
                        self.bad_pixels_widget.addItem('%d, %d' %
                                                       (int(round(self.crop_x1)),
                                                        int(round(self.crop_y1))))
                        self.mod_image('cmap')
            '''elif self.set_roi_enabled:
                roi_crop = self.roi_img[int(round(self.crop_y0)):
                                        int(round(self.crop_y1)),
                                        int(round(self.crop_x0)):
                                        int(round(self.crop_x1))]'''

    def on_motion(self, event):
        if self.set_roi_enabled and event.button == 1 and event.inaxes:
            self.rect.set_width(event.xdata - self.crop_x0) #crop_x0 is lower, crop_x1 is higher -D
            self.rect.set_height(event.ydata - self.crop_y0)
            self.rect.set_xy((self.crop_x0, self.crop_y0))

            self.rect_xy=self.rect.get_xy()
            self.rect_height = self.rect.get_height()
            self.rect_width = self.rect.get_width()

            self.canvas.draw()

    def initrect(self):
        rect=Rectangle((0, 0), 0, 0, alpha=0.3, facecolor='gray',
                              edgecolor='red', linewidth=2)
        rect.set_xy(self.rect_xy)
        rect.set_height(self.rect_height)
        rect.set_width(self.rect_width)
        return rect


    def set_roi_enable(self, pressed):
        if pressed == True:
            #self.rect.set_visible(True)
            #self.canvas.axes.add_patch(self.rect)
            self.canvas.fig.axes[0].add_patch(self.rect)
            self.show_rect = True
            self.canvas.draw()
            self.set_roi_enabled = True
            self.normalize_button.setEnabled(True)
            self.subtract_button.setEnabled(True)

        else:
            #self.rect.set_visible(False)
            self.rect.remove()
            self.show_rect = False
            self.canvas.draw()
            self.set_roi_enabled = False
            self.normalize_button.setEnabled(False)
            self.subtract_button.setEnabled(False)

    def apply_roi(self):

        # self.normalize_button.setEnabled(False)
        # self.show_rect = False
        # self.rect.remove()
        x = int(round(self.crop_x1)) - int(round(self.crop_x0))
        y = int(round(self.crop_y1)) - int(round(self.crop_y0))

        def pad_crop(x, y):
            x_dim = 0
            y_dim = 0
            while x > x_dim:
                x_dim += 32

            while y > y_dim:
                y_dim += 32

            if self.square_cb.isChecked():
                x_dim = max(x_dim, y_dim)
                y_dim = x_dim

            for i in xrange(self.bad_pixels_widget.count()):
                item = self.bad_pixels_widget.item(i)
                x_, y_ = item.text().split(',')
                x_ = int(x_)
                y_ = int(y_)
                new_x = x_ - int(round(self.crop_x0))
                new_y = y_ - int(round(self.crop_y0))
                '''print(x_dim)
                ratio = x_ / self.image.shape[0]
                #ratio = 1 - ratio
                new_x = str(int(ratio * x_dim) - 1)
                ratio = y_ / self.image.shape[1]
                #ratio = 1 - ratio
                new_y = str(int(ratio * y_dim) - 1)'''
                item.setText("%s, %s" % (new_x, new_y))

            if self.img_type == '3':
                # center the crop around the center of mass
                initial_crop = self.image[int(round(self.crop_y0)):
                                          int(round(self.crop_y0 + y_dim)),
                                          int(round(self.crop_x0)):
                                          int(round(self.crop_x0 + x_dim)),
                                          :]
                com_x, com_y, com_z = ndimage.measurements.center_of_mass(initial_crop)
                self.crop_x0 = int(round(com_x + self.crop_x0)) - (x_dim / 2)
                self.crop_y0 = int(round(com_y + self.crop_y0)) - (y_dim / 2)

                # do a second crop calculation to more accurately center
                second_crop = self.image[int(round(self.crop_y0)):
                                         int(round(self.crop_y0 + y_dim)),
                                         int(round(self.crop_x0)):
                                         int(round(self.crop_x0 + x_dim)),
                                         :]

                com_x, com_y, com_z = ndimage.measurements.center_of_mass(second_crop)
                self.crop_x0 = int(round(com_x + self.crop_x0)) - (x_dim / 2)
                self.crop_y0 = int(round(com_y + self.crop_y0)) - (y_dim / 2)

                cropped_image = self.image[int(round(self.crop_y0)):
                                           int(round(self.crop_y0 + y_dim)),
                                           int(round(self.crop_x0)):
                                           int(round(self.crop_x0 + x_dim)),
                                           :]

                self.rect.set_xy((self.crop_x0, self.crop_y0))
                self.rect.set_width(x_dim)
                self.rect.set_height(y_dim)


                # zero-pad image if smaller than desired dimensions
            #     if cropped_image.shape[1] < x_dim or cropped_image.shape[0] < y_dim:
            #         npad_x = x_dim - cropped_image.shape[1]
            #         npad_y = y_dim - cropped_image.shape[0]
            #         npad = ((0, npad_x), (0, npad_y), (0, 0))
            #         cropped_image = np.pad(cropped_image, npad, mode='constant', constant_values=0)
            #     return cropped_image
            # elif self.img_type == 'complex':
            #     return self.image[int(round(self.crop_y0)):
            #                       int(round(self.crop_y0 + y_dim)),
            #                       int(round(self.crop_x0)):
            #                       int(round(self.crop_x0 + x_dim))]
            # else:
            #     return self.image[int(round(self.crop_y0)):
            #                       int(round(self.crop_y0 + y_dim)),
            #                       int(round(self.crop_x0)):
            #                       int(round(self.crop_x0 + x_dim))]

        if self.img_type == '3':
            crop_image = pad_crop(x, y)
            self.something(crop_image)#trying now to exploit crop commmand such that it can be used to store data
            # self.show_image(crop_image, dim='3', new_file=True) #Testing croping the image
            #
            # self.open_file.file_ = self.image
            # self._clear_views()
        # elif self.img_type == 'complex':
        #     crop_image = pad_crop(x, y)
        #     self.show_image(crop_image, dim='complex', new_file=True)
        #     self._clear_views()
        # else:
        #     crop_image = pad_crop(x, y)
        #     self.show_image(crop_image, new_file=True)
        #     self._clear_views()
    def saveh5(self):
        nameh5 = str(QtGui.QFileDialog.getSaveFileName(self, "File name"))
        if "." not in nameh5:
            nameh5 = nameh5 + ".h5"
        with h5py.File(nameh5, 'w') as hf:
            hf.create_dataset("proj", data=np.fliplr(np.swapaxes(self.h5,0,2)))#test-D

    def norm(self): #now will take a slice value in the range from -D
        xy=self.rect.get_xy()
        height=(self.rect.get_height())# can be negative -D
        width=(self.rect.get_width())
        x2 = xy[0] + width
        y2 = xy[1] + height
        length = self.image.shape[2]
        kingBG=0
        normimage=self.image.copy()
        for i in range(length): #range command works -D
            #self.image_slider.setValue(i)
            if i == 0:
                kingBG = np.sum((np.fliplr(self.image))[min((xy[0], x2)):max((xy[0], x2)), min((xy[1], y2)):max((xy[1], y2)),i])
                #kingBG = np.sum((np.fliplr(self.image))[min((xy[0], x2)):max((xy[0], x2)), min((xy[1], y2)):max((xy[1], y2)), self.image_slider.getValue(i)])
            else:
                currentBG = np.sum((np.fliplr(self.image))[min((xy[0], x2)):max((xy[0], x2)), min((xy[1], y2)):max((xy[1], y2)),i])
                #currentBG = np.sum((np.fliplr(self.image))[min((xy[0], x2)):max((xy[0], x2)), min((xy[1], y2)):max((xy[1], y2)), self.image_slider.getValue(i)])
                factor=kingBG/currentBG #normalizing factor
                normimage[:, :, i] *=factor
                #print("loop",i)
        #print(np.shape(self.image))
        #print(np.shape(normimage))
        #self.show_image(normimage, dim='3', new_file=True) #SHOW IMAGE DOESNT WORK -D
        # self.image=normimage
        # ax=self.canvas.fig.add_subplot(111)
        # ax.imshow(normimage[:,:,self.image_slider.value()])
        #self.image_slider.setValue(0)
        #self.show_file(type='npy')
        # with h5py.File('out_norm.h5', 'w') as hf:
        #     hf.create_dataset("proj", data=np.fliplr(np.swapaxes(normimage,0,2)))#test-D
        self.set_roi_enable(False)
        self.set_roi_button.setChecked(False)
        self.h5 = normimage.copy()
        self.show_image(normimage,dim='3',new_file=True)


    def sub(self):  # now average will take a slice value in the range from -D
        xy = self.rect.get_xy()
        height = (self.rect.get_height())  # can be negative -D
        width = (self.rect.get_width())
        x2 = xy[0] + width
        y2 = xy[1] + height
        length = self.image.shape[2]
        subimage = self.image.copy()
        for i in range(length):  # range command works -D
            #self.image_slider.setValue(i)
            currentBG = np.mean((np.fliplr(self.image))[min((xy[0], x2)):max((xy[0], x2)), min((xy[1], y2)):max((xy[1], y2)),self.image_slider.value()])
            currentBG = np.mean((np.fliplr(self.image))[min((xy[0], x2)):max((xy[0], x2)), min((xy[1], y2)):max((xy[1], y2)),i])
            tempslice = self.image[:,:,i]
            tempslice -= currentBG
            tempslice[tempslice<0.] = 0.
            subimage[:,:,i] = tempslice
            #print("toop",i)
        #self.im.set_data(subimage) #SET IMAGE DOESNT WORK -D
        #self.show_file(type='npy')
        # with h5py.File('out_sub.h5', 'w') as hf:
        #     hf.create_dataset("proj", data=np.fliplr(np.swapaxes(subimage, 0, 2)))  # test-D
        self.set_roi_enable(False)
        self.set_roi_button.setChecked(False)
        self.h5 = subimage.copy()
        self.show_image(subimage, dim='3', new_file=True)

    def apply_thresh(self, pressed):
        if pressed:
            self.thresh = True
            self.mod_image('cmap')
        else:
            self.thresh = False
            self.mod_image('cmap')

    # save roi, bad pixels, and threshold to xml file
    def save_img_setup(self):
        root = ET.Element("root")
        roi = ET.SubElement(root, "roi")
        ET.SubElement(roi, "xy").text = str(self.rect.get_xy())
        ET.SubElement(roi, 'width').text = str(self.rect.get_width())
        ET.SubElement(roi, 'height').text = str(self.rect.get_height())
        bad_pix = ET.SubElement(root, "bad_pix")
        for i in xrange(self.bad_pixels_widget.count()):
            item = str(self.bad_pixels_widget.item(i).text())
            ET.SubElement(bad_pix, "pixel").text = item
        ET.SubElement(root, "threshold").text = str(self.thresh_sb.value())
        ET.SubElement(root, "flippedud").text = str(self.flippedud)
        ET.SubElement(root, "flippedlr").text = str(self.flippedlr)
        ET.SubElement(root, "transposed").text = str(self.transposed)

        tree = ET.ElementTree(root)
        filename = QtGui.QFileDialog.getSaveFileName(self, "File name")
        tree.write(filename)

    # load roi, bad pixels, and threshold from xml file and populate gui
    def load_img_setup(self):
        # load data into local variables
        filename = QtGui.QFileDialog.getOpenFileName(self, "Select file", filter='*.xml')
        tree = ET.parse(filename)
        root = tree.getroot()
        xy = root.find("roi/xy").text
        xy_floats = eval(xy)
        #xy_ints = [int(val) for val in xy]
        width = root.find("roi/width").text
        height = root.find("roi/height").text
        bad_pix_list = []
        for value in root.findall("bad_pix/pixel"):
            bad_pix_list.append(value.text)
        threshold = root.find("threshold").text
        flippedud = root.find("flippedud").text
        flippedlr = root.find("flippedlr").text
        transposed = root.find("transposed").text

        # populate gui elements with loaded data
        self.rect.set_xy(xy_floats)
        self.rect.set_width(float(width))
        self.rect.set_height(float(height))
        for pix in bad_pix_list:
            self.bad_pixels_widget.addItem(pix)
        self.thresh_sb.setValue(float(threshold))
        '''if self.flippedud != self.str_to_bool(flippedud):
            self.image = np.flipud(self.image)
            self.flippedud == flippedud
        if self.flippedlr != self.str_to_bool(flippedlr):
            self.image = np.fliplr(self.image)
            self.flippedlr == flippedlr
        if self.transposed == self.str_to_bool(transposed):
            self.image = self.image.T
            self.transposed = transposed'''

        # refresh the image to add bad pixels to display
        self.mod_image('cmap')

    def str_to_bool(self, s):
        if s == 'True':
            return True
        elif s == 'False':
            return False
        else:
            raise ValueError

    def canvas_linear(self):
        #if enabled:
        if self.lin_rbutton.isChecked():
            '''self.canvas.axes.set_xscale("linear")
            self.canvas.axes.set_yscale("linear")
            self.canvas.axes.invert_yaxis()
            self.canvas.draw()'''
            if self.img_type is not None:
                self.mod_image('lin')

    def canvas_log(self):
        #if enabled:
        if self.log_rbutton.isChecked():
            '''self.canvas.axes.set_xscale("log")
            self.canvas.axes.set_yscale("log")
            self.canvas.draw()'''
            if self.img_type is not None:
                self.mod_image('log')

    def canvas_amp(self):
        if self.amp_rbutton.isChecked() and self.amp_rbutton.isEnabled():
            self.show_image(self.image, dim='complex')

    def canvas_phase(self):
        if self.phase_rbutton.isChecked() and self.phase_rbutton.isEnabled():
            self.show_image(self.image, dim='complex')

    def set_defaults(self):

        self.diffraction_file = ''                        # diffraction data
        self.points_file = ''                             # scan pattern
        self.object_file = ''                             # object file
        self.probe_file = ''                              # probe file

        self.outer_loops = 1

        self.x_roi = 128                                  # x ROI
        self.y_roi = 128                                  # y ROI

        self.nx_obj = 856                                 # object x dimension
        self.ny_obj = 856                                 # object y dimension
        self.save_name = 'test'                           # saving file name
        self.scan_num = 'scan'                            # scan number
        self.update_product_flag = False                  # update product flag
        self.beta = 0.9                                   # general feedback parameter
        self.alpha = 1e-8                                 # espresso threshold coefficient
        self.n_iterations = 1000                          # number of iterations
        self.start_update_probe = 2                       # iteration number start updating probe
        self.end_update_probe = self.n_iterations         # iteration number ends updating probe
        self.search_range = 10                            # search range for centering
        self.sigma1 = 1.e-10                              # normalization weighting factor 1
        self.sigma2 = 5.e-5                               # normalization weighting factor 2
        self.amp_max = 1.0                                # maximum object magnitude
        self.amp_min = 0.0                                # minimum object magnitude
        self.pha_max = np.pi/2                                # maximum object phase
        self.pha_min = -np.pi/2                                 # minimum object phase
        self.ave_i = 0                                    # average number
        self.start_ave = 0.8                              # average starting iteration
        self.display_error_flag = True                    # display reconstruction result flag
        self.x_direction_flag = False
        self.prb_center_flag = False
        self.x_dr_um = 0.75                               # scan step size in x direction (um)
        self.y_dr_um = 0.75                               # scan step size in y direction (um)

        # experimental parameter
        self.x_range_um = 3.                              # x scan range
        self.y_range_um = 3.                              # y scan range
        self.dr_um = 0.2/1.59                             # radius increment
        self.nth = 5.0                                    # number of points in the first ring
        self.lambda_nm = 0.1459                           # wavelength
        self.z_m = 3.415                                  # ccd distance
        self.ccd_pixel_um = 55.0                          # ccd pixel size

        # partial coherence parameter
        self.kernel_n = 16                                # kernel size
        self.pc_sigma = 0.2                               # kernel width
        self.n_coh = 20                                   # number of iteration for kernel updating loop
        self.pc_interval = 15                             # how often to update coherence function
        self.update_coh_flag = False                      # update coherence function or not
        self.pc_flag = True                               # use partial coherence or not
        self.conv_flag = True
        self.conv_complex_flag = False
        self.conv_norm_flag = True
        self.coh_percent = 0.5                            # percentage of points used for coherence updating

        # position correction parameter
        self.position_correction_flag = False
        self.position_correction_search_range = 2
        self.position_correction_start = 0.1
        self.position_correction_step = 10

        # multiprocessing
        self.processes = 1
        self.regions = 1

        self.last_path = ''

    def set_widgets(self):
        # tab 1
        self.diffraction_data_label = QtGui.QLabel("Open file") #Add open file functionality -D
        self.open_file = FileSelector("Open file")
        self.diffraction_data_combobox = QtGui.QComboBox()
        self.diffraction_data_combobox.addItems(self.diffraction_data_options)
        self.diffraction_data_button = QtGui.QPushButton("Show")
        self.diffraction_data_button.setDefault(False)
        self.diffraction_data_button.setAutoDefault(False)
        self.diffraction_data_button.clicked.connect(lambda: self.show_file(type='diff'))#add the flip here-D
        #self.diffraction_data_button.clicked.connect(self.transpose_im) #one more transpose step -D
        #everything else not used -D
        self.scan_pattern_label = QtGui.QLabel("Scan pattern (points)")
        self.scan_pattern_fs = FileSelector("Scan pattern (points)")
        self.scan_pattern_combobox = QtGui.QComboBox()
        self.scan_pattern_combobox.addItems(self.scan_pattern_options)
        self.scan_pattern_button = QtGui.QPushButton("Show")
        self.scan_pattern_button.setDefault(False)
        self.scan_pattern_button.setAutoDefault(False)
        self.scan_pattern_button.clicked.connect(lambda: self.show_file('scan'))
        self.object_file_label = QtGui.QLabel("Object file")
        self.object_file_fs = FileSelector("Object file")
        self.object_file_combobox = QtGui.QComboBox()
        self.object_file_combobox.addItems(self.object_options)
        self.object_file_button = QtGui.QPushButton("Show")
        self.object_file_button.setDefault(False)
        self.object_file_button.setAutoDefault(False)
        self.object_file_button.clicked.connect(lambda: self.show_file('obj'))
        self.probe_file_label = QtGui.QLabel("Probe file")
        self.probe_file_fs = FileSelector("Probe file")
        self.probe_file_combobox = QtGui.QComboBox()
        self.probe_file_combobox.addItems(self.probe_options)
        self.probe_file_button = QtGui.QPushButton("Show")
        self.probe_file_button.setDefault(False)
        self.probe_file_button.setAutoDefault(False)
        self.probe_file_button.clicked.connect(lambda: self.show_file('prb'))
        self.x_scan_step_label = QtGui.QLabel("X Scan step size")
        self.x_scan_step_sb = QtGui.QDoubleSpinBox()
        self.x_scan_step_sb.setMaximumWidth(100)
        self.y_scan_step_label = QtGui.QLabel("Y Scan step size")
        self.y_scan_step_sb = QtGui.QDoubleSpinBox()
        self.y_scan_step_sb.setMaximumWidth(100)
        self.max_obj_amp_label = QtGui.QLabel("Maximum object amplitude")
        self.max_obj_amp_sb = QtGui.QDoubleSpinBox()
        self.max_obj_amp_sb.setMaximumWidth(100)
        self.min_obj_amp_label = QtGui.QLabel("Minimum object amplitude")
        self.min_obj_amp_sb = QtGui.QDoubleSpinBox()
        self.min_obj_amp_sb.setMaximumWidth(100)
        self.max_obj_phase_label = QtGui.QLabel("Maximum object phase")
        self.max_obj_phase_sb = QtGui.QDoubleSpinBox()
        self.max_obj_phase_sb.setRange(-1000., 1000.)
        self.max_obj_phase_sb.setDecimals(10)
        self.max_obj_phase_sb.setMaximumWidth(100)
        self.min_obj_phase_label = QtGui.QLabel("Minimum object phase")
        self.min_obj_phase_sb = QtGui.QDoubleSpinBox()
        self.min_obj_phase_sb.setRange(-1000., 1000.)
        self.min_obj_phase_sb.setDecimals(10)
        self.min_obj_phase_sb.setMaximumWidth(100)
        #self.x_roi_label = QtGui.QLabel("X ROI")
        #self.x_roi_sb = QtGui.QSpinBox()
        #self.y_roi_label = QtGui.QLabel("Y ROI")
        #self.y_roi_sb = QtGui.QSpinBox()
        self.save_name_label = QtGui.QLabel("Save file name")
        self.save_name_qle = QtGui.QLineEdit()
        self.save_name_qle.setMaximumWidth(100)

        # Advanced widgets
        #self.nx_obj_label = QtGui.QLabel("Object x dimension")
        #self.nx_obj_sb = QtGui.QSpinBox()
        #self.nx_obj_sb.setMaximumWidth(100)
        #self.ny_obj_label = QtGui.QLabel("Object y dimension")
        #self.ny_obj_sb = QtGui.QSpinBox()
        #self.ny_obj_sb.setMaximumWidth(100)
        self.start_ave_label = QtGui.QLabel("Average starting iteration")
        self.start_ave_sb = QtGui.QDoubleSpinBox()
        self.start_ave_sb.setMaximumWidth(100)
        self.n_iterations_label = QtGui.QLabel("Number of iterations")
        self.n_iterations_sb = QtGui.QSpinBox()
        self.n_iterations_sb.setRange(1, 10000)
        self.n_iterations_sb.setMaximumWidth(100)
        self.scan_num_label = QtGui.QLabel("Scan number")
        self.scan_num_qle = QtGui.QLineEdit()
        self.scan_num_qle.setMaximumWidth(100)
        self.x_scan_range_label = QtGui.QLabel("x scan range (um)")
        self.x_scan_range_sb = QtGui.QSpinBox()
        self.x_scan_range_sb.setMaximumWidth(100)
        self.y_scan_range_label = QtGui.QLabel("y scan range (um)")
        self.y_scan_range_sb = QtGui.QSpinBox()
        self.y_scan_range_sb.setMaximumWidth(100)
        self.dr_label = QtGui.QLabel("Radius increment size (um)")
        self.dr_sb = QtGui.QDoubleSpinBox()
        self.dr_sb.setMaximumWidth(100)
        self.nth_label = QtGui.QLabel("Points in first ring")
        self.nth_sb = QtGui.QSpinBox()
        self.nth_sb.setMaximumWidth(100)
        self.lambda_label = QtGui.QLabel("X-ray wavelength (nm)")
        self.lambda_sb = QtGui.QDoubleSpinBox()
        #self.lambda_sb.setMaximumWidth(100)
        self.z_label = QtGui.QLabel("Detector-to-sample distance (m)")
        self.z_sb = QtGui.QDoubleSpinBox()
        #self.z_sb.setMaximumWidth(100)
        self.ccd_pixel_label = QtGui.QLabel("Detector pixel size (um)")
        self.ccd_pixel_sb = QtGui.QDoubleSpinBox()
        #self.ccd_pixel_sb.setMaximumWidth(100)

        self.worker_processes_label = QtGui.QLabel("Worker processes")
        self.worker_processes_sb = QtGui.QSpinBox()
        self.regions_label = QtGui.QLabel("Regions")
        self.regions_sb = QtGui.QSpinBox()
        self.mesh_label = QtGui.QLabel("Mesh scan")
        self.mesh_checkbox = QtGui.QCheckBox()
        self.mesh_label.setBuddy(self.mesh_checkbox)

        self.start_button = QtGui.QPushButton("Start")
        self.stop_button = QtGui.QPushButton("Stop")
        self.advanced_button = QtGui.QPushButton("Advanced")
        self._settings = ["diffraction_file", "points_file", "object_file", "probe_file", "nx_obj", "ny_obj", "x_roi",
                          "y_roi", "save_name", "scan_num", "update_product_flag", "beta", "alpha", "n_iterations",
                          "outer_loops", "start_update_probe", "end_update_probe", "search_range", "sigma1", "sigma2",
                          "amp_max", "amp_min", "pha_max", "pha_min", "ave_i", "start_ave", "display_error_flag",
                          "x_direction_flag", "prb_center_flag", "processes", "regions", "x_range_um", "y_range_um",
                          "dr_um", "nth", "lambda_nm", "z_m", "ccd_pixel_um", "kernel_n", "pc_sigma", "n_coh",
                          "pc_interval", "update_coh_flag", "pc_flag", "conv_flag", "conv_complex_flag",
                          "conv_norm_flag", "coh_percent", "position_correction_flag",
                          "position_correction_search_range", "position_correction_start", "position_correction_step"]

        '''self._settings = ["points_file", "object_file", "probe_file", "save_name", "scan_num",
                          "update_product_flag", "n_iterations", "amp_max", "amp_min", "pha_max", "pha_min", "ave_i",
                          "start_ave", "processes", "regions", "x_range_um", "y_range_um", "dr_um", "nth", "lambda_nm",
                          "z_m", "ccd_pixel_um"]'''

    def toggle_advanced(self):
        if not self.advanced:
            self.mesh_checkbox.setVisible(True)
            self.mesh_label.setVisible(True)
            self.regions_sb.setVisible(True)
            self.regions_label.setVisible(True)
            self.worker_processes_sb.setVisible(True)
            self.worker_processes_label.setVisible(True)
            self.ccd_pixel_sb.setVisible(True)
            self.ccd_pixel_label.setVisible(True)
            self.z_sb.setVisible(True)
            self.z_label.setVisible(True)
            self.lambda_sb.setVisible(True)
            self.lambda_label.setVisible(True)
            self.nth_sb.setVisible(True)
            self.nth_label.setVisible(True)
            self.dr_sb.setVisible(True)
            self.dr_label.setVisible(True)
            self.y_scan_range_sb.setVisible(True)
            self.y_scan_range_label.setVisible(True)
            self.x_scan_range_sb.setVisible(True)
            self.x_scan_range_label.setVisible(True)
            #self.scan_num_qle.setVisible(True)
            #self.scan_num_label.setVisible(True)
            self.start_ave_sb.setVisible(True)
            self.start_ave_label.setVisible(True)
            self.n_iterations_sb.setVisible(True)
            self.n_iterations_label.setVisible(True)
            #self.ny_obj_sb.setVisible(True)
            #self.ny_obj_label.setVisible(True)
            #self.nx_obj_sb.setVisible(True)
            #self.nx_obj_label.setVisible(True)
            self.tab1_grid3_gbox.setVisible(True)
            self.advanced = True
            self.advanced_button.setText("Basic")
        else:
            '''self.tab1_grid.removeWidget(self.ccd_pixel_sb)
            self.tab1_grid.removeWidget(self.ccd_pixel_label)
            #self.tab1_grid_row -= 1
            self.tab1_grid.removeWidget(self.z_sb)
            self.tab1_grid.removeWidget(self.z_label)
            #self.tab1_grid_row -= 1
            self.tab1_grid.removeWidget(self.lambda_sb)
            self.tab1_grid.removeWidget(self.lambda_label)
            #self.tab1_grid_row -= 1
            self.tab1_grid.removeWidget(self.nth_sb)
            self.tab1_grid.removeWidget(self.nth_label)
            #self.tab1_grid_row -= 1
            self.tab1_grid.removeWidget(self.dr_sb)
            self.tab1_grid.removeWidget(self.dr_label)
            #self.tab1_grid_row -= 1
            self.tab1_grid.removeWidget(self.y_scan_range_sb)
            self.tab1_grid.removeWidget(self.y_scan_range_label)
            #self.tab1_grid_row -= 1
            self.tab1_grid.removeWidget(self.x_scan_range_sb)
            self.tab1_grid.removeWidget(self.x_scan_range_label)
            #self.tab1_grid_row -= 1
            self.tab1_grid.removeWidget(self.scan_num_qle)
            self.tab1_grid.removeWidget(self.scan_num_label)
            #self.tab1_grid_row -= 1
            self.tab1_grid.removeWidget(self.start_ave_sb)
            self.tab1_grid.removeWidget(self.start_ave_label)
            #self.tab1_grid_row -= 1
            self.advanced = False'''

            self.mesh_checkbox.setVisible(False)
            self.mesh_label.setVisible(False)
            self.regions_sb.setVisible(False)
            self.regions_label.setVisible(False)
            self.worker_processes_sb.setVisible(False)
            self.worker_processes_label.setVisible(False)
            self.ccd_pixel_sb.setVisible(False)
            self.ccd_pixel_label.setVisible(False)
            self.z_sb.setVisible(False)
            self.z_label.setVisible(False)
            self.lambda_sb.setVisible(False)
            self.lambda_label.setVisible(False)
            self.nth_sb.setVisible(False)
            self.nth_label.setVisible(False)
            self.dr_sb.setVisible(False)
            self.dr_label.setVisible(False)
            self.y_scan_range_sb.setVisible(False)
            self.y_scan_range_label.setVisible(False)
            self.x_scan_range_sb.setVisible(False)
            self.x_scan_range_label.setVisible(False)
            #self.scan_num_qle.setVisible(False)
            #self.scan_num_label.setVisible(False)
            self.start_ave_sb.setVisible(False)
            self.start_ave_label.setVisible(False)
            self.n_iterations_sb.setVisible(False)
            self.n_iterations_label.setVisible(False)
            #self.ny_obj_sb.setVisible(False)
            #self.ny_obj_label.setVisible(False)
            #self.nx_obj_sb.setVisible(False)
            #self.nx_obj_label.setVisible(False)
            self.tab1_grid3_gbox.setVisible(False)
            self.advanced = False
            self.advanced_button.setText("Advanced")

    def set_main_tab(self):
        #self.tab1_grid = QtGui.QGridLayout()
        self.tab1_grid1 = QtGui.QGridLayout()
        self.tab1_grid2 = QtGui.QGridLayout()
        self.tab1_grid3 = QtGui.QGridLayout()
        self.tab1_grid1_gbox = QtGui.QGroupBox("Import File")
        self.tab1_grid2_gbox = QtGui.QGroupBox("Main")
        self.tab1_grid3_gbox = QtGui.QGroupBox("Experimental")
        self.tab1_grid1_gbox.setLayout(self.tab1_grid1)
        self.tab1_grid2_gbox.setLayout(self.tab1_grid2)
        self.tab1_grid3_gbox.setLayout(self.tab1_grid3)

        '''basic'''
        self.tab1_grid1_row = 0
        self.tab1_grid1.addWidget(self.diffraction_data_label, self.tab1_grid1_row, 0)
        self.tab1_grid1.addWidget(self.open_file, self.tab1_grid1_row, 1)
        self.tab1_grid1.addWidget(self.diffraction_data_combobox, self.tab1_grid1_row, 2)
        self.tab1_grid1.addWidget(self.diffraction_data_button, self.tab1_grid1_row, 3)
        self.tab1_grid1_row += 1
        # self.tab1_grid1.addWidget(self.scan_pattern_label, self.tab1_grid1_row, 0)
        # self.tab1_grid1.addWidget(self.scan_pattern_fs, self.tab1_grid1_row, 1)
        # self.tab1_grid1.addWidget(self.scan_pattern_combobox, self.tab1_grid1_row, 2)
        # self.tab1_grid1.addWidget(self.scan_pattern_button, self.tab1_grid1_row, 3)
        # self.tab1_grid1_row += 1
        # self.tab1_grid1.addWidget(self.object_file_label, self.tab1_grid1_row, 0)
        # self.tab1_grid1.addWidget(self.object_file_fs, self.tab1_grid1_row, 1)
        # self.tab1_grid1.addWidget(self.object_file_combobox, self.tab1_grid1_row, 2)
        # self.tab1_grid1.addWidget(self.object_file_button, self.tab1_grid1_row, 3)
        # self.tab1_grid1_row += 1
        # self.tab1_grid1.addWidget(self.probe_file_label, self.tab1_grid1_row, 0)
        # self.tab1_grid1.addWidget(self.probe_file_fs, self.tab1_grid1_row, 1)
        # self.tab1_grid1.addWidget(self.probe_file_combobox, self.tab1_grid1_row, 2)
        # self.tab1_grid1.addWidget(self.probe_file_button, self.tab1_grid1_row, 3)

        self.tab1_grid2_row = 0
        self.tab1_grid2.addWidget(self.x_scan_step_label, self.tab1_grid2_row, 0)
        self.tab1_grid2.addWidget(self.x_scan_step_sb, self.tab1_grid2_row, 1)
        #self.tab1_grid2_row += 1
        self.tab1_grid2.addWidget(self.y_scan_step_label, self.tab1_grid2_row, 2)
        self.tab1_grid2.addWidget(self.y_scan_step_sb, self.tab1_grid2_row, 3)
        self.tab1_grid2_row += 1
        self.tab1_grid2.addWidget(self.max_obj_amp_label, self.tab1_grid2_row, 0)
        self.tab1_grid2.addWidget(self.max_obj_amp_sb, self.tab1_grid2_row, 1)
        #self.tab1_grid2_row += 1
        self.tab1_grid2.addWidget(self.min_obj_amp_label, self.tab1_grid2_row, 2)
        self.tab1_grid2.addWidget(self.min_obj_amp_sb, self.tab1_grid2_row, 3)
        self.tab1_grid2_row += 1
        self.tab1_grid2.addWidget(self.max_obj_phase_label, self.tab1_grid2_row, 0)
        self.tab1_grid2.addWidget(self.max_obj_phase_sb, self.tab1_grid2_row, 1)
        #self.tab1_grid2_row += 1
        self.tab1_grid2.addWidget(self.min_obj_phase_label, self.tab1_grid2_row, 2)
        self.tab1_grid2.addWidget(self.min_obj_phase_sb, self.tab1_grid2_row, 3)
        #self.tab1_grid_row += 1
        #self.tab1_grid.addWidget(self.x_roi_label, self.tab1_grid_row, 0)
        #self.tab1_grid.addWidget(self.x_roi_sb, self.tab1_grid_row, 1)
        #self.tab1_grid_row += 1
        #self.tab1_grid.addWidget(self.y_roi_label, self.tab1_grid_row, 0)
        #self.tab1_grid.addWidget(self.y_roi_sb, self.tab1_grid_row, 1)
        self.tab1_grid2_row += 1
        self.tab1_grid2.addWidget(self.save_name_label, self.tab1_grid2_row, 0)
        self.tab1_grid2.addWidget(self.save_name_qle, self.tab1_grid2_row, 1)
        self.tab1_grid2.addWidget(self.scan_num_label, self.tab1_grid2_row, 2)
        self.tab1_grid2.addWidget(self.scan_num_qle, self.tab1_grid2_row, 3)

        '''advanced'''
        #self.tab1_grid2_row += 1
        #self.tab1_grid2.addWidget(self.nx_obj_label, self.tab1_grid2_row, 0)
        #self.tab1_grid2.addWidget(self.nx_obj_sb, self.tab1_grid2_row, 1)
        #self.tab1_grid2_row += 1
        #self.tab1_grid2.addWidget(self.ny_obj_label, self.tab1_grid2_row, 2)
        #self.tab1_grid2.addWidget(self.ny_obj_sb, self.tab1_grid2_row, 3)
        self.tab1_grid2_row += 1
        self.tab1_grid2.addWidget(self.start_ave_label, self.tab1_grid2_row, 0)
        self.tab1_grid2.addWidget(self.start_ave_sb, self.tab1_grid2_row, 1)
        self.tab1_grid2.addWidget(self.n_iterations_label, self.tab1_grid2_row, 2)
        self.tab1_grid2.addWidget(self.n_iterations_sb, self.tab1_grid2_row, 3)
        self.tab1_grid2_row += 1
        self.tab1_grid2.addWidget(self.x_scan_range_label, self.tab1_grid2_row, 0)
        self.tab1_grid2.addWidget(self.x_scan_range_sb, self.tab1_grid2_row, 1)
        #self.tab1_grid2_row += 1
        self.tab1_grid2.addWidget(self.y_scan_range_label, self.tab1_grid2_row, 2)
        self.tab1_grid2.addWidget(self.y_scan_range_sb, self.tab1_grid2_row, 3)
        self.tab1_grid2_row += 1
        self.tab1_grid2.addWidget(self.dr_label, self.tab1_grid2_row, 0)
        self.tab1_grid2.addWidget(self.dr_sb, self.tab1_grid2_row, 1)
        #self.tab1_grid2_row += 1
        self.tab1_grid2.addWidget(self.nth_label, self.tab1_grid2_row, 2)
        self.tab1_grid2.addWidget(self.nth_sb, self.tab1_grid2_row, 3)
        self.tab1_grid2_row += 1
        self.tab1_grid2.addWidget(self.worker_processes_label, self.tab1_grid2_row, 0)
        self.tab1_grid2.addWidget(self.worker_processes_sb, self.tab1_grid2_row, 1)
        self.tab1_grid2.addWidget(self.regions_label, self.tab1_grid2_row, 2)
        self.tab1_grid2.addWidget(self.regions_sb, self.tab1_grid2_row, 3)
        self.tab1_grid2_row += 1
        self.tab1_grid2.addWidget(self.mesh_label, self.tab1_grid2_row, 0)
        self.tab1_grid2.addWidget(self.mesh_checkbox, self.tab1_grid2_row, 1)

        self.tab1_grid3_row = 0
        self.tab1_grid3.addWidget(self.lambda_label, self.tab1_grid3_row, 0)
        self.tab1_grid3.addWidget(self.lambda_sb, self.tab1_grid3_row, 1)
        self.tab1_grid3_row += 1
        self.tab1_grid3.addWidget(self.z_label, self.tab1_grid3_row, 0)
        self.tab1_grid3.addWidget(self.z_sb, self.tab1_grid3_row, 1)
        self.tab1_grid3_row += 1
        self.tab1_grid3.addWidget(self.ccd_pixel_label, self.tab1_grid3_row, 0)
        self.tab1_grid3.addWidget(self.ccd_pixel_sb, self.tab1_grid3_row, 1)

        #set advanced controls invisible (reverse order)
        self.mesh_checkbox.setVisible(False)
        self.mesh_label.setVisible(False)
        self.regions_sb.setVisible(False)
        self.regions_label.setVisible(False)
        self.worker_processes_sb.setVisible(False)
        self.worker_processes_label.setVisible(False)
        self.ccd_pixel_sb.setVisible(False)
        self.ccd_pixel_label.setVisible(False)
        self.z_sb.setVisible(False)
        self.z_label.setVisible(False)
        self.lambda_sb.setVisible(False)
        self.lambda_label.setVisible(False)
        self.nth_sb.setVisible(False)
        self.nth_label.setVisible(False)
        self.dr_sb.setVisible(False)
        self.dr_label.setVisible(False)
        self.y_scan_range_sb.setVisible(False)
        self.y_scan_range_label.setVisible(False)
        self.x_scan_range_sb.setVisible(False)
        self.x_scan_range_label.setVisible(False)
        #self.scan_num_qle.setVisible(False)
        #self.scan_num_label.setVisible(False)
        self.start_ave_sb.setVisible(False)
        self.start_ave_label.setVisible(False)
        self.n_iterations_sb.setVisible(False)
        self.n_iterations_label.setVisible(False)
        #self.nx_obj_sb.setVisible(False)
        #self.nx_obj_label.setVisible(False)
        #self.ny_obj_sb.setVisible(False)
        #self.ny_obj_label.setVisible(False)
        self.tab1_grid2_gbox.setVisible(False) #Shows/ hides the extra boxes on left -D
        self.tab1_grid3_gbox.setVisible(False)

        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.start_button)
        hbox1.addWidget(self.stop_button)
        hbox1.addStretch(0)
        hbox1.addWidget(self.advanced_button)

        self.tab1_scroll_area = QtGui.QScrollArea()
        self.tab1_scroll_area.setWidgetResizable(True)
        self.tab1_scroll_area.setMinimumHeight(510)
        self.tab1_scroll_area.setMinimumWidth(620)

        self.tab1_sa_groupbox = QtGui.QGroupBox()
        #self.tab1_sa_groupbox.setStyleSheet("QGroupBox { border:0; }")
        self.tab1_scroll_area.setStyleSheet("QScrollArea { border:0; }")

        self.tab1_sa_vbox = QtGui.QVBoxLayout()
        self.tab1_sa_groupbox.setLayout(self.tab1_sa_vbox)
        #self.tab1_sa_vbox.addLayout(self.tab1_grid)
        self.tab1_sa_vbox.addWidget(self.tab1_grid1_gbox)
        self.tab1_sa_vbox.addWidget(self.tab1_grid2_gbox)
        self.tab1_sa_vbox.addWidget(self.tab1_grid3_gbox)
        self.tab1_sa_vbox.addStretch(0)
        self.tab1_scroll_area.setWidget(self.tab1_sa_groupbox)

        self.console_info_gbox = QtGui.QGroupBox("Console information")
        self.console_info_grid = QtGui.QGridLayout()
        self.console_info_te = QtGui.QTextEdit()
        self.console_info_te.setReadOnly(True)
        self.console_info_gbox.setLayout(self.console_info_grid)
        self.console_info_grid.addWidget(self.console_info_te)

        self.tab1_vbox.addWidget(self.tab1_scroll_area)
        self.tab1_vbox.addLayout(hbox1)
        self.tab1_vbox.addWidget(self.console_info_gbox)

    def _set_color_map(self, index):
        """
        User changed color map callback.
        """
        cm_ = str(self.color_map.itemText(index))
        print('Color map set to: %s' % cm_)
        self._color_map = mpl.cm.get_cmap(cm_)
        try:
            '''for im in [self.canvas.imphi, ]:
                im.set_cmap(self._color_map)'''
            #self.image.set_cmap(self._color_map)
            #self.show_image(self.image)
            self.mod_image('cmap')
        except Exception as ex:
            print('failed to set color map: (%s) %s' % (ex.__class__.__name__, ex))
        finally:
            self.canvas.draw()

    def create_cmap_previews(self):
        """
        Create the color map previews for the combobox
        """
        cm_names = sorted(_cm for _cm in mpl.cm.datad.keys()
                          if not _cm.endswith('_r'))
        cm_filenames = [os.path.join(CMAP_PREVIEW_PATH, '%s.png' % cm_name)
                        for cm_name in cm_names]

        ret = zip(cm_names, cm_filenames)
        points = np.outer(np.ones(10), np.arange(0, 1, 0.01))
        if not os.path.exists(CMAP_PREVIEW_PATH):
            try:
                os.mkdir(CMAP_PREVIEW_PATH)
            except Exception as ex:
                print('Unable to create preview path: %s' % ex)

            return ret

        for cm_name, fn in zip(cm_names, cm_filenames):
            if not os.path.exists(fn):
                print('Generating colormap preview: %s' % fn)
                canvas = MplCanvas(width=2, height=0.25, dpi=50)
                fig = canvas.figure
                fig.clear()

                ax = fig.add_subplot(1, 1, 1)# mess with this -D
                ax.axis("off")
                fig.subplots_adjust(top=1, left=0, right=1, bottom=0)
                _cm = mpl.cm.get_cmap(cm_name)
                ax.imshow(points, aspect='auto', cmap=_cm, origin='lower', interpolation='none')
                try:
                    fig.savefig(fn)
                except Exception as ex:
                    '''print('Unable to create color map preview "%s"' % fn,
                          file=sys.stderr)'''
                    print("Unable to create color map preview")
                    break

        return ret

    def update_color_maps(self):
        size = None
        for i, (cm_name, fn) in enumerate(self.create_cmap_previews()):
            print('Color map', fn)
            if os.path.exists(fn):
                self.color_map.addItem(QtGui.QIcon(fn), cm_name)
                if size is None:
                    size = QtGui.QPixmap(fn).size()
                    self.color_map.setIconSize(size)
            else:
                self.color_map.addItem(cm_name)

            if cm_name == self.CM_DEFAULT:
                self.color_map.setCurrentIndex(i)

    @QtCore.pyqtSlot(str)
    def on_myStream_message(self, message):
        self.console_info_te.moveCursor(QtGui.QTextCursor.End)
        self.console_info_te.insertPlainText(message)

    # clears toolbar views (zoom/pan) (MAY BREAK WITH ANY MPL UPDATE)
    def _clear_views(self):
        self.mpl_toolbar._views.clear()
        self.mpl_toolbar._positions.clear()
        self.mpl_toolbar._update_view()

    def show_file(self, type):
        self.canvas.fig.clear()
        self.canvas.figure.subplots_adjust(top=0.95, bottom=0.15)
        if type == 'npy':
            #file_ = np.load(self.open_file.filename)
            #file_ = self.open_file.file_
            file_=self.image
            #file_.ndim=3
            #file_ = np.swapaxes(file_, 0, 2)
            if file_.ndim == 3:
                self.show_image(file_, dim='3', new_file=True)
                self._clear_views()
            else:
                self.show_image(file_)
                self._clear_views()
        if type == 'diff':
            #file_ = np.load(self.open_file.filename)
            file_ = self.open_file.file_
            file_ = np.swapaxes(file_,0,2)#ask xiao jing!
            if file_.ndim == 3:
                self.show_image(file_, dim='3', new_file=True)
                self._clear_views()
            else:
                self.show_image(file_)
                self._clear_views()
        elif type == 'scan':
            #file_ = np.load(self.scan_pattern_fs.filename)
            file_ = self.scan_pattern_fs.file_
            self.show_image(file_, dim='plot', new_file=True)
            self._clear_views()
        elif type == 'obj':
            #file_ = np.load(self.object_file_fs.filename)
            file_ = self.object_file_fs.file_
            self.show_image(file_, dim='complex', new_file=True)
            self._clear_views()
            '''if file_.ndim == 3:
                self.show_image(file_, dim='3')
            else:
                self.show_image(file_)'''
        elif type == 'prb':
            #file_ = np.load(self.probe_file_fs.filename)
            file_ = self.probe_file_fs.file_
            self.show_image(file_, dim='complex', new_file=True)
            self._clear_views()
        else:
            return

    def show_image(self, image, dim=None, new_file=False):
        # print('Test') #test 1 -D
        canvas = self.canvas
        fig = canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        self.img_type = dim
        if type(image) is not np.ndarray:
            image = np.array(image)
        if dim == '3':
            self.image_slider.setMaximum(image.shape[2] - 1)
            self.enable_slider()
            self.disable_complex()
            self.enable_mods()
            self.enable_roi_and_pix()
            #print(np.shape(image))
            #self.im = ax.imshow(image[:,:,self.image_slider.value()], cmap=self._color_map, interpolation='none')
            self.set_image(ax, image[:,:,self.image_slider.value()], new_file=new_file)
        # elif dim == 'plot':
        #     self.disable_slider()
        #     self.disable_complex()
        #     self.disable_mods()
        #     self.disable_roi_and_pix()
        #     self.plot = ax.plot(image[0, :], image[1, :], 'go', zorder=1)
        #     self.plot = ax.plot(image[0, :], image[1, :], zorder=2)
        #     '''self.canvas.fig.delaxes(self.canvas.fig.axes[1])
        #     self.colorbar = None
        #     self.canvas.fig.subplots_adjust(right=0.90)  # default right padding'''
        # elif dim == 'complex':
        #     self.disable_slider()
        #     self.enable_complex()
        #     self.enable_mods()
        #     self.enable_roi_and_pix()
        #     if self.amp_rbutton.isChecked():
        #         #self.im = ax.imshow(np.abs(image), cmap=self._color_map, interpolation='none')
        #         self.set_image(ax, np.abs(image), new_file=new_file)
        #     elif self.phase_rbutton.isChecked():
        #         #self.im = ax.imshow(np.angle(image), cmap=self._color_map, interpolation='none')
        #         self.set_image(ax, np.angle(image), new_file=new_file)
        #     else:
        #         print('complex array error')
        else:
            self.disable_slider()
            self.disable_complex()
            self.enable_mods()
            self.enable_roi_and_pix()
            self.image_slice_qle.setText("")
            #self.im = ax.imshow(image, cmap=self._color_map, interpolation='none')
            self.set_image(ax, image, new_file=new_file)

        if self.show_rect:
            self.rect=self.initrect()
            ax.add_patch(self.rect)

        self.image = image
        canvas.axes = ax
        #self.something(image) #Removing now to see if other something command works #This prints the mean value of the slice, updating each time the slice is changed
        canvas.draw()

    # deep copies image to be shown, allowing image modification without
    # modifying data (appropriate data modification will be done before
    # reconstruction begins)
    def set_image(self, axes, image, new_file=False):
        log_ = self.log_rbutton.isChecked()
        orient = self.orient_view #LOOK HERE
        im_to_show = copy.deepcopy(image)
        if log_:
            im_to_show = np.log(im_to_show + 1e-6)
        if self.bad_pixels_widget.item(0) is not None:
            for i in xrange(self.bad_pixels_widget.count()):
                y, x = self.bad_pixels_widget.item(i).text().split(',')
                y = int(y)
                x = int(x)
                if x >= 0 and y >= 0 and x < im_to_show.shape[0] and y < im_to_show.shape[1]:
                    im_to_show[x, y] = 0
        if self.bin_cb.isChecked():
            x_bin_val = int(self.bin_qle1.text())
            y_bin_val = int(self.bin_qle2.text())
            im_to_show = self.rebin(im_to_show, (im_to_show.shape[0] / x_bin_val, im_to_show.shape[1] / y_bin_val))
        if self.thresh:
            im_to_show[im_to_show < float(self.thresh_sb.value())] = 0
        if orient:
            im_to_show = np.flipud(im_to_show.T)
            axes.set_title('Image in proper orientation')
        else:
            axes.set_title('Image is flipped and transposed')

        '''if not self.im:
            self.im = axes.imshow(im_to_show, cmap=self._color_map, interpolation='none')
            if self.img_type != 'plot':
                colorbar = self.canvas.fig.colorbar(self.im)
        else:
            self.im.set_data(im_to_show)
            self.im.changed()'''
        #print(np.shape(im_to_show))
        self.im = axes.imshow(im_to_show, cmap=self._color_map, interpolation='none')
        #self.im = self.canvas.axes.imshow(im_to_show, cmap=self._color_map, interpolation='none')
        '''if not self.colorbar:
            if self.img_type != 'plot':
                self.colorbar = self.canvas.fig.colorbar(self.im)
        else:
            if self.img_type != 'plot':
                #self.colorbar.set_clim(im_to_show.min(), im_to_show.max())
                self.colorbar.update_bruteforce(self.im)
            else:
                self.canvas.fig.delaxes(self.canvas.fig.axes[1])
                self.colorbar = None
                self.canvas.fig.subplots_adjust(right=0.90)  # default right padding'''

        # preserves zoom when showing new image (MAY BREAK WITH ANY MATPLOTLIB UPDATE)
        if not new_file:
            toolbar = self.mpl_toolbar
            old_view = toolbar._views()
            #toolbar.update() #clear zoom history
            if old_view: #don't change current view
                toolbar.push_current()
                toolbar._views.push(old_view)
            toolbar._update_view()

        numrows, numcols = im_to_show.shape

        def format_coord(x, y):
            col = int(x+0.5)
            row = int(y+0.5)
            if col>=0 and col<numcols and row>=0 and row<numrows:
                z = im_to_show[row,col]
                #return 'x=%1.2f, y=%1.2f, z=%1.2f'%(x, y, z)
                return 'x=%1.2f, y=%1.2f'%(x, y)
            else:
                return 'x=%1.2f, y=%1.2f'%(x, y)

        axes.format_coord = format_coord
        #self.canvas.axes.format_coord = format_coord

    # rebin array a to specified shape
    def rebin(self, a, shape):
        sh = shape[0],a.shape[0]//shape[0],shape[1],a.shape[1]//shape[1]
        return a.reshape(sh).mean(-1).mean(1)

    # rebin 2d slices of 3d array into new 3d array
    def rebin3d(self, a, shape):
        new_array = np.zeros(shape)
        for i in range(shape[2]):
            new_array[:,:,i] = self.rebin(a[:,:,i], (shape[0], shape[1]))
        return new_array

    def disable_mods(self):
        self.color_map.setEnabled(False)
        self.flip_ud_button.setEnabled(False)
        self.flip_lr_button.setEnabled(False)
        self.transpose_button.setEnabled(False)

    def enable_mods(self):
        self.color_map.setEnabled(True)
        self.flip_ud_button.setEnabled(True)
        self.flip_lr_button.setEnabled(True)
        self.transpose_button.setEnabled(True)

    def disable_slider(self):
        self.image_slider.setEnabled(False)
        self.image_slice_qle.setEnabled(False)

    def enable_slider(self):
        self.image_slider.setEnabled(True)
        self.image_slice_qle.setEnabled(True)

    def disable_complex(self):
        self.amp_rbutton.setEnabled(False)
        self.phase_rbutton.setEnabled(False)

    def enable_complex(self):
        self.amp_rbutton.setEnabled(True)
        self.phase_rbutton.setEnabled(True)

    def disable_roi_and_pix(self):
        self.set_roi_button.setChecked(False)
        self.set_roi_button.setEnabled(False)
        self.bin_cb.setChecked(False)
        self.bin_cb.setEnabled(False)
        self.square_cb.setEnabled(False)
        self.bad_pix_button.setChecked(False)
        self.bad_pix_button.setEnabled(False)
        self.thresh_cb.setChecked(False)
        self.thresh_cb.setEnabled(False)
        self.save_pix_button.setEnabled(False)
        self.load_pix_button.setEnabled(False)

    def enable_roi_and_pix(self):
        self.set_roi_button.setEnabled(True)
        self.bin_cb.setEnabled(True)
        self.square_cb.setEnabled(True)
        self.bad_pix_button.setEnabled(True)
        self.thresh_cb.setEnabled(True)
        self.save_pix_button.setEnabled(True)
        self.load_pix_button.setEnabled(True)

    """def mod_image(self, mod):
        canvas = self.canvas
        fig = canvas.figure
        ax = fig.add_subplot(111)
        if self.image.ndim == 3:
            if mod == 'flipud':
                '''self.image[:,:,self.image_slider.value()] = np.flipud(self.image[:,:,self.image_slider.value()])
                self.im = ax.imshow(self.image[:,:,self.image_slider.value()], cmap=self._color_map, interpolation='none')'''
                ax.invert_yaxis()
            elif mod == 'fliplr':
                #self.image[:,:,self.image_slider.value()] = np.fliplr(self.image[:,:,self.image_slider.value()])
                #self.im = ax.imshow(self.image[:,:,self.image_slider.value()], cmap=self._color_map, interpolation='none')
                ax.invert_xaxis()
            elif mod == 'transpose':
                self.image[:,:,self.image_slider.value()] = self.image[:,:,self.image_slider.value()].T
                self.im = ax.imshow(self.image[:,:,self.image_slider.value()], cmap=self._color_map, interpolation='none')
                '''def swap(xdata, ydata):
                    line.set_xdata(ydata)
                    line.set_ydata(xdata)

                line = ax.lines[0]
                swap(line.get_xdata(), line.get_ydata())'''
            elif mod == 'cmap':
                self.im = ax.imshow(self.image[:,:,self.image_slider.value()], cmap=self._color_map, interpolation='none')
            else:
                print("Invalid transformation")
        else:
            if mod == 'flipud':
                '''self.image = np.flipud(self.image)
                if str(self.image.dtype) == 'complex128':
                    if self.amp_rbutton.isChecked():
                        self.im = ax.imshow(np.abs(self.image), cmap=self._color_map, interpolation='none')
                    elif self.phase_rbutton.isChecked():
                        self.im = ax.imshow(np.angle(self.image), cmap=self._color_map, interpolation='none')
                else:
                    print(self.image.dtype)
                    self.im = ax.imshow(self.image, cmap=self._color_map, interpolation='none')'''
                ax.invert_yaxis()
            elif mod == 'fliplr':
                #self.image = np.fliplr(self.image)
                #self.im = ax.imshow(self.image, cmap=self._color_map, interpolation='none')
                ax.invert_xaxis()
            elif mod == 'transpose':
                '''def swap(xdata, ydata):
                    line.set_xdata(ydata)
                    line.set_ydata(xdata)

                line = ax.lines[0]
                swap(line.get_xdata(), line.get_ydata())'''
                self.image = self.image.T
                self.im = ax.imshow(self.image, cmap=self._color_map, interpolation='none')
            elif mod == 'cmap':
                self.im = ax.imshow(self.image, cmap=self._color_map, interpolation='none')
            else:
                print("Invalid transformation")

        canvas.draw()"""

    def mod_image(self, mod, reset_zoom=False):
        canvas = self.canvas
        fig = canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        if mod == 'flipud':
            self.mod_bad_pix(mod)
            self.flippedud = not self.flippedud
            self.image = np.flipud(self.image)
            if self.img_type == '3':
                #ax.imshow(self.image[:,:,self.image_slider.value()], cmap=self._color_map, interpolation='none')
                self.set_image(ax, self.image[:,:,self.image_slider.value()])
            elif self.img_type == 'complex':
                if self.amp_rbutton.isChecked():
                    #ax.imshow(np.abs(self.image), cmap=self._color_map, interpolation='none')
                    self.set_image(ax, np.abs(self.image))
                else:
                    #ax.imshow(np.angle(self.image), cmap=self._color_map, interpolation='none')
                    self.set_image(ax, np.angle(self.image))
            else:
                self.rect = self.initrect()
                self.set_image(ax, self.image)
        elif mod == 'fliplr':
            self.mod_bad_pix(mod)
            self.flippedlr = not self.flippedlr
            self.image = np.fliplr(self.image)
            if self.img_type == '3':
                #ax.imshow(self.image[:,:,self.image_slider.value()], cmap=self._color_map, interpolation='none')
                self.set_image(ax, self.image[:,:,self.image_slider.value()])
            elif self.img_type == 'complex':
                if self.amp_rbutton.isChecked():
                    #ax.imshow(np.abs(self.image), cmap=self._color_map, interpolation='none')
                    self.set_image(ax, np.abs(self.image))
                else:
                    #ax.imshow(np.angle(self.image), cmap=self._color_map, interpolation='none')
                    self.set_image(ax, np.angle(self.image))
            else:
                self.rect = self.initrect()
                self.set_image(ax, self.image)
        elif mod == 'transpose':
            self.mod_bad_pix(mod)
            self.transposed = not self.transposed
            if self.img_type == '3':
                #self.image[:,:,self.image_slider.value()] = self.image[:,:,self.image_slider.value()].T


                #self.image = np.swapaxes(self.image, 0, 1)
                self.image= np.transpose(self.image,(1,0,2))

                #self.im = ax.imshow(self.image[:,:,self.image_slider.value()], cmap=self._color_map, interpolation='none')
                self.set_image(ax, self.image[:,:,self.image_slider.value()])
            elif self.img_type == 'plot':
                def swap(xdata, ydata):
                    line.set_xdata(ydata)
                    line.set_ydata(xdata)

                line = ax.lines[0]
                swap(line.get_xdata(), line.get_ydata())
            elif self.img_type == 'complex':
                self.image = self.image.T
                if self.amp_rbutton.isChecked():
                    #ax.imshow(np.abs(self.image), cmap=self._color_map, interpolation='none')
                    self.set_image(ax, np.abs(self.image))
                else:
                    #ax.imshow(np.angle(self.image), cmap=self._color_map, interpolation='none')
                    self.set_image(ax, np.angle(self.image))
            else:
                self.image = self.image.T
                #self.im = ax.imshow(self.image, cmap=self._color_map, interpolation='none')
                self.set_image(ax, self.image)
            if self.show_rect:
                self.rect = self.initrect()
                ax.add_patch(self.rect)
        elif mod == 'cmap':
            if self.img_type == '3':
                #self.im = ax.imshow(self.image[:,:,self.image_slider.value()], cmap=self._color_map, interpolation='none')
                self.set_image(ax, self.image[:,:,self.image_slider.value()], new_file=reset_zoom)
            elif self.img_type == 'complex':
                if self.amp_rbutton.isChecked():
                    #ax.imshow(np.abs(self.image), cmap=self._color_map, interpolation='none')
                    self.set_image(ax, np.abs(self.image), new_file=reset_zoom)
                else:
                    #ax.imshow(np.angle(self.image), cmap=self._color_map, interpolation='none')
                    self.set_image(ax, np.angle(self.image), new_file=reset_zoom)
            else:
                #ax.imshow(self.image, cmap=self._color_map, interpolation='none')
                self.set_image(ax, self.image, new_file=reset_zoom)
            if self.show_rect:
                self.rect = self.initrect()
                ax.add_patch(self.rect)
        elif mod == 'log':
            if self.img_type == '3':
                #self.im = ax.imshow(np.log(self.image[:,:,self.image_slider.value()] + 1e-9), cmap=self._color_map, interpolation='none')
                self.set_image(ax, self.image[:,:,self.image_slider.value()])
            elif self.img_type == 'plot':
                pass
            elif self.img_type == 'complex':
                if self.amp_rbutton.isChecked():
                    #ax.imshow(np.log(np.abs(self.image) + 1e-9), cmap=self._color_map, interpolation='none')
                    self.set_image(ax, np.abs(self.image))
                else:
                    #ax.imshow(np.log(np.angle(self.image) + 1e-9), cmap=self._color_map, interpolation='none')
                    self.set_image(ax, np.angle(self.image))
        elif mod == 'lin':
            if self.img_type == '3':
                #self.im = ax.imshow(self.image[:,:,self.image_slider.value()], cmap=self._color_map, interpolation='none')
                self.set_image(ax, self.image[:,:,self.image_slider.value()])
            elif self.img_type == 'plot':
                pass
            elif self.img_type == 'complex':
                if self.amp_rbutton.isChecked():
                    #ax.imshow(np.abs(self.image), cmap=self._color_map, interpolation='none')
                    self.set_image(ax, np.abs(self.image))
                else:
                    #ax.imshow(np.angle(self.image), cmap=self._color_map, interpolation='none')
                    self.set_image(ax, np.angle(self.image))
        else:
            print("Invalid mod")

        canvas.draw()

    def mod_bad_pix(self, mod):
        if mod == 'flipud':
            for i in xrange(self.bad_pixels_widget.count()):
                item = self.bad_pixels_widget.item(i)
                x, y = item.text().split(',')
                y = float(y)
                ratio = y / self.image.shape[1]
                ratio = 1 - ratio
                new_y = str(int(ratio * self.image.shape[1]) - 1)
                item.setText("%s, %s" % (x, new_y))
        elif mod == 'fliplr':
            for i in xrange(self.bad_pixels_widget.count()):
                item = self.bad_pixels_widget.item(i)
                x, y = item.text().split(',')
                x = float(x)
                ratio = x / self.image.shape[0]
                ratio = 1 - ratio
                new_x = str(int(ratio * self.image.shape[0]) - 1)
                item.setText("%s, %s" % (new_x, y))
        elif mod == 'transpose':
            for i in xrange(self.bad_pixels_widget.count()):
                item = self.bad_pixels_widget.item(i)
                x, y = item.text().split(',')
                x = int(x)
                y = int(y)
                item.setText("%i, %i" % (y, x))

    def flip_ud(self):
        self.mod_image('flipud')

    def flip_lr(self):
        self.mod_image('fliplr')

    def transpose_im(self):
        self.mod_image('transpose')

    def slide(self):
        self.show_image(self.image, dim='3')
        self.image_slice_qle.setText(str(self.image_slider.value()))

    def slide_from_qle(self):
        self.image_slider.setValue(int(self.image_slice_qle.text()))

    @property
    def settings(self):
        return QtCore.QSettings('BNL', 'Ptycho-GUI')

    def save_settings(self):
        settings = self.settings
        for attr in self._settings:
            settings.setValue(attr, getattr(self, attr))

        settings.setValue('geometry', self.geometry())
        settings.setValue('splitter', self.splitter.saveState())

        settings.setValue('diffraction_file', self.open_file.file_)
        settings.setValue('npy_file', self.open_file.file_)

        # pass some default values
        '''settings.setValue('nx_obj', self.nx_obj)
        settings.setValue('ny_obj', self.ny_obj)
        #settings.setValue('x_roi', self.open_file.file_.shape[1])
        #settings.setValue('y_roi', self.open_file.shape[0])
        settings.setValue('x_roi', self.x_roi)
        settings.setValue('y_roi', self.y_roi)
        settings.setValue('update_product_flag', self.update_product_flag)
        settings.setValue('beta', self.beta)
        settings.setValue('alpha', self.alpha)
        settings.setValue('outer_loops', self.outer_loops)
        settings.setValue('start_update_probe', self.start_update_probe)
        settings.setValue('end_update_probe', self.end_update_probe)
        settings.setValue('search_range', self.search_range)
        settings.setValue('sigma1', self.sigma1)
        settings.setValue('sigma2', self.sigma2)
        settings.setValue('ave_i', self.ave_i)
        settings.setValue('display_error_flag', self.display_error_flag)
        settings.setValue('x_direction_flag', self.x_direction_flag)
        settings.setValue('prb_center_flag', self.prb_center_flag)
        settings.setValue('kernel_x', self.kernel_n)
        settings.setValue('pc_sigma', self.pc_sigma)
        settings.setValue('n_coh', self.n_coh)
        settings.setValue('pc_interval', self.pc_interval)
        settings.setValue('update_coh_flag', self.update_coh_flag)
        settings.setValue('pc_flag', self.pc_flag)
        settings.setValue('conv_flag', self.conv_flag)
        settings.setValue('conv_norm_flag', self.conv_norm_flag)
        settings.setValue('coh_percent', self.coh_percent)
        settings.setValue('position_correction_flag', self.position_correction_flag)
        settings.setValue('position_correction_search_range', self.position_correction_search_range)
        settings.setValue('position_correction_start', self.position_correction_start)
        settings.setValue('position_correction_step', self.position_correction_step)'''

    def load_settings(self):
        settings = self.settings
        for attr in self._settings:
            value = settings.value(attr)
            if value is not None:
                try:
                    # Necessary in PyQt4, but not PySide
                    value = value.toPyObject()
                    setattr(self, attr, value)
                except:
                    pass

                #setattr(self, attr, value)

        try:
            self.setGeometry(settings.value('geometry').toPyObject())
            self.splitter.restoreState(settings.value('splitter').toByteArray())
        except:
            pass

    def closeEvent(self, event=None):
        self.save_settings()

    @property
    def full_settings(self):
        ret = {}
        for key in self._settings:
            ret[key] = getattr(self, key)
        return ret

    def _prepare_image(self):
        diff_file = self.open_file.file_
        if self.bad_pixels_widget.item(0) is not None:
            for i in xrange(self.bad_pixels_widget.count()):
                y, x = self.bad_pixels_widget.item(i).text().split(',')
                y = int(y)
                x = int(x)
                if x >= 0 and y >= 0 and x < self.image.shape[0] and y < self.image.shape[1]:
                    diff_file[x, y] = 0

        if self.bin_cb.isChecked():
            x_bin_val = int(self.bin_qle1.text())
            y_bin_val = int(self.bin_qle2.text())
            diff_file = self.rebin3d(diff_file, (diff_file.shape[0] / x_bin_val,
                                                 diff_file.shape[1] / y_bin_val,
                                                 diff_file.shape[2]))
        if self.thresh:
            diff_file[diff_file < float(self.thresh_sb.value())] = 0

    def start(self):
        self._prepare_image()
        self.save_settings()
        if self._thread is not None and self._thread.isFinished():
            self._thread = None

        if self._thread is None:
            thread = self._thread = PtychoThread(self.canvas)
            thread.settings = self.full_settings
            thread.start()
            self.set_running(True)

    def set_running(self, running):
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)

    def stop(self):
        if self._thread is not None:
            '''pool = self._thread.pool
            if pool is not None:
                pool.terminate()
                self._thread.pool = None'''

            time.sleep(0.2)
            self._thread.terminate()

            self._thread.update_display()

            self._thread = None
            self.set_running(False)

    # setters/getters

    @property
    def diffraction_file(self):
        """Open file"""
        return self.open_file.filename

    @diffraction_file.setter
    def diffraction_file(self, value):
        self.open_file.filename = str(value)

    @property
    def points_file(self):
        """Scan pattern (points)"""
        return self.scan_pattern_fs.filename

    @points_file.setter
    def points_file(self, value):
        self.scan_pattern_fs.filename = str(value)

    @property
    def object_file(self):
        """Object file"""
        return self.object_file_fs.filename

    @object_file.setter
    def object_file(self, value):
        self.object_file_fs.filename = str(value)

    @property
    def probe_file(self):
        """Probe file"""
        return self.probe_file_fs.filename

    @probe_file.setter
    def probe_file(self, value):
        self.probe_file_fs.filename = str(value)

    '''@property
    def nx_obj(self):
        """Object x dimension"""
        return self.nx_obj
        #return self.nx_obj_sb.value()

    @nx_obj.setter
    def nx_obj(self, value):
        self.nx_obj = value
        #self.nx_obj_sb.setValue(int(value))'''

    '''@property
    def ny_obj(self):
        """Object y dimension"""
        return self.ny_obj
        #return self.ny_obj_sb.value()

    @ny_obj.setter
    def ny_obj(self, value):
        self.ny_obj = value
        #self.ny_obj_sb.setValue(int(value))'''

    '''@property
    def x_roi(self):
        """X roi"""
        return self.x_roi
        #return self.x_roi_sb.value()'''

    '''@x_roi.setter
    def x_roi(self, value):
        self.x_roi = value
        #self.x_roi_sb.setValue(int(value))'''

    '''@property
    def y_roi(self):
        """Y roi"""
        return self.y_roi
        #return self.y_roi_sb.value()

    @y_roi.setter
    def y_roi(self, value):
        self.y_roi = value
        #self.y_roi_sb.setValue(int(value))'''

    @property
    def save_name(self):
        """Saving file name"""
        return str(self.save_name_qle.text())

    @save_name.setter
    def save_name(self, value):
        self.save_name_qle.setText(value)

    @property
    def scan_num(self):
        """Scan number"""
        return str(self.scan_num_qle.text())

    @scan_num.setter
    def scan_num(self, value):
        self.scan_num_qle.setText(value)

    '''@property
    def update_product_flag(self):
        """Update product flag"""
        return self.update_product_flag
        #return self.w_update_product_flag.isChecked()

    @update_product_flag.setter
    def update_product_flag(self, value):
        self.update_product_flag = value
        #self.w_update_product_flag.setChecked(str(value).lower() == "true")

    @property
    def beta(self):
        """General feedback parameter"""
        return self.beta
        #return self.w_beta.value()

    @beta.setter
    def beta(self, value):
        self.beta = value
        #self.w_beta.setValue(float(value))

    @property
    def alpha(self):
        """Espresso threshold coefficient"""
        return self.alpha
        #return self.w_alpha.value()

    @alpha.setter
    def alpha(self, value):
        self.alpha = value
        #self.w_alpha.setValue(float(value))'''

    @property
    def n_iterations(self):
        """Number of iterations (inner loop)"""
        return self.n_iterations_sb.value()
        #return self.w_n_iterations.value()

    @n_iterations.setter
    def n_iterations(self, value):
        self.n_iterations_sb.setValue(int(value))
        #self.w_n_iterations.setValue(int(value))

    '''@property
    def outer_loops(self):
        """Combining iterations (outer loop)"""
        return self.w_outer_loops.value()

    @outer_loops.setter
    def outer_loops(self, value):
        self.w_outer_loops.setValue(int(value))

    @property
    def start_update_probe(self):
        """Iteration number start updating probe"""
        return self.w_start_update_probe.value()

    @start_update_probe.setter
    def start_update_probe(self, value):
        self.w_start_update_probe.setValue(int(value))

    @property
    def end_update_probe(self):
        """Iteration number ends updating probe"""
        return self.w_end_update_probe.value()

    @end_update_probe.setter
    def end_update_probe(self, value):
        self.w_end_update_probe.setValue(int(value))

    @property
    def search_range(self):
        """Search range for centering"""
        return self.w_search_range.value()

    @search_range.setter
    def search_range(self, value):
        self.w_search_range.setValue(int(value))

    @property
    def sigma1(self):
        """Normalization weighting factor 1"""
        return self.w_sigma1.value()

    @sigma1.setter
    def sigma1(self, value):
        self.w_sigma1.setValue(float(value))

    @property
    def sigma2(self):
        """Normalization weighting factor 2"""
        return self.w_sigma2.value()

    @sigma2.setter
    def sigma2(self, value):
        self.w_sigma2.setValue(float(value))'''

    @property
    def amp_max(self):
        """Maximum object magnitude"""
        #return self.w_amp_max.value()
        return self.max_obj_amp_sb.value()

    @amp_max.setter
    def amp_max(self, value):
        #self.w_amp_max.setValue(float(value))
        self.max_obj_amp_sb.setValue(float(value))

    @property
    def amp_min(self):
        """Minimum object magnitude"""
        #return self.w_amp_min.value()
        return self.min_obj_phase_sb.value()

    @amp_min.setter
    def amp_min(self, value):
        #self.w_amp_min.setValue(float(value))
        self.min_obj_phase_sb.setValue(float(value))

    @property
    def pha_max(self):
        """Maximum object phase"""
        #return self.w_pha_max.value()
        return self.max_obj_phase_sb.value()

    @pha_max.setter
    def pha_max(self, value):
        #self.w_pha_max.setValue(int(value))
        self.max_obj_phase_sb.setValue(float(value))

    @property
    def pha_min(self):
        """Minimum object phase"""
        #return self.w_pha_min.value()
        return self.min_obj_phase_sb.value()

    @pha_min.setter
    def pha_min(self, value):
        #self.w_pha_min.setValue(int(value))
        self.min_obj_phase_sb.setValue(float(value))

    '''@property
    def ave_i(self):
        """Average number"""
        return self.w_ave_i.value()

    @ave_i.setter
    def ave_i(self, value):
        self.w_ave_i.setValue(int(value))'''

    @property
    def start_ave(self):
        """Average starting iteration"""
        #return self.w_start_ave.value()
        return self.start_ave_sb.value()

    @start_ave.setter
    def start_ave(self, value):
        #self.w_start_ave.setValue(float(value))
        self.start_ave_sb.setValue(float(value))

    '''@property
    def display_error_flag(self):
        """Display reconstruction result flag"""
        return self.w_display_error_flag.isChecked()

    @display_error_flag.setter
    def display_error_flag(self, value):
        self.w_display_error_flag.setChecked(str(value).lower() == "true")'''

    '''@property
    def x_direction_flag(self):
        """X direction flag"""
        return self.w_x_direction_flag.isChecked()

    @x_direction_flag.setter
    def x_direction_flag(self, value):
        self.w_x_direction_flag.setChecked(str(value).lower() == "true")'''

    '''@property
    def prb_center_flag(self):
        """Prb center flag"""
        return self.w_prb_center_flag.isChecked()

    @prb_center_flag.setter
    def prb_center_flag(self, value):
        self.w_prb_center_flag.setChecked(str(value).lower() == "true")'''

    @property
    def processes(self):
        """Worker processes"""
        #return self.w_processes.value()
        return self.worker_processes_sb.value()

    @processes.setter
    def processes(self, value):
        #self.w_processes.setValue(int(value))
        self.worker_processes_sb.setValue(int(value))

    @property
    def regions(self):
        """Regions"""
        #return self.w_regions.value()
        return self.regions_sb.value()

    @regions.setter
    def regions(self, value):
        #self.w_regions.setValue(int(value))
        self.regions_sb.setValue(int(value))

    @property
    def x_range_um(self):
        """X scan range"""
        #return self.w_x_range_um.value()
        return self.x_scan_range_sb.value()

    @x_range_um.setter
    def x_range_um(self, value):
        #self.w_x_range_um.setValue(float(value))
        self.x_scan_range_sb.setValue(float(value))

    @property
    def y_range_um(self):
        """Y scan range"""
        #return self.w_y_range_um.value()
        return self.y_scan_range_sb.value()

    @y_range_um.setter
    def y_range_um(self, value):
        #self.w_y_range_um.setValue(float(value))
        self.y_scan_range_sb.setValue(float(value))

    @property
    def x_dr_um(self):
        """scan step size in x direction"""
        return self.x_scan_step_sb.value()

    @x_dr_um.setter
    def x_dr_um(self, value):
        self.x_scan_step_sb.setValue(float(value))

    @property
    def y_dr_um(self):
        """scan step size in y direction"""
        return self.y_scan_step_sb.value()

    @y_dr_um.setter
    def y_dr_um(self, value):
        self.y_scan_step_sb.setValue(float(value))

    @property
    def dr_um(self):
        """Radius increment"""
        #return self.w_dr_um.value()
        return self.dr_sb.value()

    @dr_um.setter
    def dr_um(self, value):
        #self.w_dr_um.setValue(float(value))
        self.dr_sb.setValue(float(value))

    @property
    def nth(self):
        """Number of points in the first ring"""
        #return self.w_nth.value()
        return self.nth_sb.value()

    @nth.setter
    def nth(self, value):
        #self.w_nth.setValue(float(value))
        self.nth_sb.setValue(float(value))

    @property
    def lambda_nm(self):
        """Wavelength"""
        #return self.w_lambda_nm.value()
        return self.lambda_sb.value()

    @lambda_nm.setter
    def lambda_nm(self, value):
        #self.w_lambda_nm.setValue(float(value))
        self.lambda_sb.setValue(float(value))

    @property
    def z_m(self):
        """Ccd distance"""
        #return self.w_z_m.value()
        return self.z_sb.value()

    @z_m.setter
    def z_m(self, value):
        #self.w_z_m.setValue(float(value))
        self.z_sb.setValue(float(value))

    @property
    def ccd_pixel_um(self):
        """Ccd pixel size"""
        #return self.w_ccd_pixel_um.value()
        return self.ccd_pixel_sb.value()

    @ccd_pixel_um.setter
    def ccd_pixel_um(self, value):
        #self.w_ccd_pixel_um.setValue(float(value))
        self.ccd_pixel_sb.setValue(float(value))

    '''@property
    def kernel_n(self):
        """Kernel size"""
        return self.w_kernel_n.value()

    @kernel_n.setter
    def kernel_n(self, value):
        self.w_kernel_n.setValue(int(value))

    @property
    def pc_sigma(self):
        """Kernel width"""
        return self.w_pc_sigma.value()

    @pc_sigma.setter
    def pc_sigma(self, value):
        self.w_pc_sigma.setValue(float(value))

    @property
    def n_coh(self):
        """Number of iteration for kernel updating loop"""
        return self.w_n_coh.value()

    @n_coh.setter
    def n_coh(self, value):
        self.w_n_coh.setValue(int(value))

    @property
    def pc_interval(self):
        """How often to update coherence function"""
        return self.w_pc_interval.value()

    @pc_interval.setter
    def pc_interval(self, value):
        self.w_pc_interval.setValue(int(value))

    @property
    def update_coh_flag(self):
        """Update coherence function or not"""
        return self.w_update_coh_flag.isChecked()

    @update_coh_flag.setter
    def update_coh_flag(self, value):
        self.w_update_coh_flag.setChecked(str(value).lower() == "true")

    @property
    def pc_flag(self):
        """Use partial coherence or not"""
        return self.w_pc_flag.isChecked()

    @pc_flag.setter
    def pc_flag(self, value):
        self.w_pc_flag.setChecked(str(value).lower() == "true")

    @property
    def conv_flag(self):
        """Conv flag"""
        return self.w_conv_flag.isChecked()

    @conv_flag.setter
    def conv_flag(self, value):
        self.w_conv_flag.setChecked(str(value).lower() == "true")

    @property
    def conv_complex_flag(self):
        """Conv complex flag"""
        return self.w_conv_complex_flag.isChecked()

    @conv_complex_flag.setter
    def conv_complex_flag(self, value):
        self.w_conv_complex_flag.setChecked(str(value).lower() == "true")

    @property
    def conv_norm_flag(self):
        """Conv norm flag"""
        return self.w_conv_norm_flag.isChecked()

    @conv_norm_flag.setter
    def conv_norm_flag(self, value):
        self.w_conv_norm_flag.setChecked(str(value).lower() == "true")

    @property
    def coh_percent(self):
        """Percentage of points used for coherence updating"""
        return self.w_coh_percent.value()

    @coh_percent.setter
    def coh_percent(self, value):
        self.w_coh_percent.setValue(float(value))

    @property
    def position_correction_flag(self):
        """Position correction flag"""
        return self.w_position_correction_flag.isChecked()

    @position_correction_flag.setter
    def position_correction_flag(self, value):
        self.w_position_correction_flag.setChecked(str(value).lower() == "true")

    @property
    def position_correction_search_range(self):
        """Position correction search range"""
        return self.w_position_correction_search_range.value()

    @position_correction_search_range.setter
    def position_correction_search_range(self, value):
        self.w_position_correction_search_range.setValue(int(value))

    @property
    def position_correction_start(self):
        """Position correction start"""
        return self.w_position_correction_start.value()

    @position_correction_start.setter
    def position_correction_start(self, value):
        self.w_position_correction_start.setValue(float(value))

    @property
    def position_correction_step(self):
        """Position correction step"""
        return self.w_position_correction_step.value()

    @position_correction_step.setter
    def position_correction_step(self, value):
        self.w_position_correction_step.setValue(int(value))'''

    #-------------------------------------------------

def subprocess_main(region_index):
    instance = ptycho.ptycho_parallel.instance
    try:
        return instance.recon_ptycho_pc(region_index)
    except KeyboardInterrupt:
        print('Cancelled')
    except Exception as ex:
        print('Subprocess failed (%s) %s' % (ex.__class__.__name__, ex))

        import traceback
        traceback.print_exc()

class PtychoThread(QtCore.QThread):
    def __init__(self, canvas, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.canvas = canvas

    def update_display(self):
        main = PtychoDialog.instance
        canvas = self.canvas
        fig = canvas.figure
        fig.clear()

        fig.subplots_adjust(top=0.95, left=0, right=0.95, bottom=0)

        instance = self.instance
        main.prb = instance.prb
        main.obj = instance.obj

        ax = fig.add_subplot(2, 2, 1)
        ax.imshow(np.abs(main.prb))
        ax.set_title('Probe Amplitude')

        ax = fig.add_subplot(2, 2, 2)
        ax.imshow(np.abs(main.obj))
        ax.set_title('Object Amplitude')

        ax = fig.add_subplot(2, 2, 3)
        ax.imshow(np.angle(main.prb))
        ax.set_title('Probe Phase')

        ax = fig.add_subplot(2, 2, 4)
        ax.imshow(np.angle(main.obj))
        ax.set_title('Object Phase')

        canvas.draw()

    def run(self):
        print('Ptycho thread started')

        settings = self.settings
        try:
            num_regions = settings['regions']
            outer_loops = settings['outer_loops']
            n_iterations = settings['n_iterations']
            instance = ptycho.ptycho_parallel(settings['diffraction_file'], settings['points_file'],
                                              object_file=settings['object_file'],
                                              probe_file=settings['probe_file'],
                                              )

            self.instance = instance
            for setting, value in self.settings.items():
                print(setting, value)
                setattr(instance, setting, value)

            instance.setup_regions(num_regions)

            shifts = {}

            nx, ny, nz = instance.nx_prb, instance.ny_prb, len(instance.diff_array)

            instance.time_start = time.time()

            for iter_ in range(outer_loops):
                '''self.pool = pool = mp.Pool(processes=num_regions)
                print('x')

                results = [pool.apply_async(subprocess_main, (i, ))
                           for i in range(len(instance.regions))]

                pool.close()
                print('c')
                pool.join()'''
                results = [subprocess_main(i, ) for i in range(len(instance.regions))]

                prb = None
                ref_prb = None
                instance.product = [None] * nz

                for i, result in enumerate(results):
                    one_obj, one_probe, sub_products = result

                    if prb is None:
                        prb = np.zeros_like(one_probe)
                        ref_prb = one_probe
                    else:
                        if i not in shifts:
                            _, x_shift, y_shift = align_class.subpixel_align(ref_prb, one_probe, 0, 0, 1)
                            shifts[i] = (x_shift, y_shift)

                        x_shift, y_shift = shifts[i]
                        one_probe = align_class.pixel_shift_2d(one_probe, x_shift, y_shift)

                    region = instance.regions[i]
                    for i, (x, y, idx) in enumerate(instance.region_points[region]):
                        instance.product[idx] = sub_products[i]

                    prb += one_probe
                    # if iter_ == (outer_loops - 1):
                    #     plt.figure(i)
                    #     plt.imshow(np.abs(one_probe))

                    # plt.figure(i)
                    # plt.imshow(np.abs(one_obj))
                    # plt.draw()

                instance.set_full_region()
                instance._update_point_info()

                # Set the probe
                instance.prb = prb / len(results)

                # And calculate the object
                instance.cal_object_trans()

            instance.time_end = time.time()

            print('regions', num_regions)
            print('per-region parallel processes', instance.processes)

            elapsed = instance.time_end - instance.time_start
            total_iters = n_iterations * outer_loops
            print('overall elapsed time', elapsed)
            print('total iterations', total_iters)
            print('per iteration time', elapsed / total_iters)

            print('%d %d %d %d %.2f' % (num_regions, instance.processes,
                                        outer_loops, n_iterations,
                                        elapsed),
                  sys.stderr)

            print('Ptycho finished')

            # main = PtychoDialog.instance
            # main.a, main.gx, main.gy, main.phi = a, gx, gy, phi
            self.update_display()
        finally:
            PtychoDialog.instance.set_running(False)

class MplToolbar(NavigationToolbar):
    # only display the buttons we need
    toolitems = [t for t in NavigationToolbar.toolitems if
                 t[0] in ('Home', 'Back', 'Forward', 'Pan', 'Zoom')]

def brush_to_color_tuple(brush):
    r, g, b, a = brush.color().getRgbF()
    return (r, g, b)

class MplCanvas(FigureCanvas):
    """
    Canvas which allows us to use matplotlib with pyqt4
    """
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)

        # We want the axes cleared every time plot() is called
        self.axes = self.fig.add_subplot(1, 1, 1)

        self.axes.hold(False)

        #FigureCanvas.__init__(self, fig)
        super(MplCanvas, self).__init__(self.fig)

        # self.figure
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self._title = ''
        self.title_font = {'family': 'serif', 'fontsize': 10}
        self._title_size = 0
        self.figure.subplots_adjust(top=0.95, bottom=0.15)

        window_brush = self.window().palette().window()
        self.fig.set_facecolor(brush_to_color_tuple(window_brush))
        self.fig.set_edgecolor(brush_to_color_tuple(window_brush))
        self._active = False

class FileSelector(QtGui.QFrame,PtychoDialog):
    def __init__(self, name, filter_='*.h5', parent=None, open_=True): #changed from .npy to .h5 -D #very quick
        QtGui.QFrame.__init__(self, parent)
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

        self.file_ = None

        self.filter_ = filter_

        self.name = name
        self.line_edit = QtGui.QLineEdit('')
        self.line_edit.setMinimumWidth(100)
        self.line_edit.setMinimumHeight(20)
        self.line_edit.textChanged.connect(self.line_edit_updated)
        #self.line_edit.returnPressed.connect(self.line_edit_updated)
        self.browse_button = QtGui.QPushButton('...')

        self.browse_button.setDefault(False)
        self.browse_button.setAutoDefault(False)

        self.setMinimumHeight(35)

        self.browse_button.clicked.connect(self.select_file) #create button? -D
        self.layout.addWidget(self.line_edit, 0, 0)
        self.layout.addWidget(self.browse_button, 0, 1)

        if open_:
            self.open_fcn = QtGui.QFileDialog.getOpenFileName
        else:
            self.open_fcn = QtGui.QFileDialog.getSaveFileName

    def line_edit_updated(self, text):
        self.filename = str(text)

    def select_file(self):
        filename = self.open_fcn(self, self.name, '', self.filter_)
        if not filename:
            return

        if isinstance(filename, tuple):
            filename = filename[0]

        self.filename = filename

        # load the file (change this to .h5 format)

        with h5py.File(self.filename, 'r') as f: # This works to open .h5 files. However, throws weird pickle error -D
            a = f['proj'][()]
            # b= np.swapaxes(a,2,0) #swap axis works, but used when displayed in above code instead -D
            #self.mod_image('transpose') #not this one -D
            self.file_=np.fliplr(a) #Flippling is not the issue -D



        print('%s set to %s %s' % (self.name, self._filename, str(np.load(self._filename).shape)))

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        value = str(value)

        if value:
            self._filename = os.path.relpath(value)
            #print('%s set to %s %s' % (self.name, self._filename, str(np.load(self._filename).shape)))
        else:
            self._filename = value

        self.line_edit.setText(self._filename)

class MyStream(QtCore.QObject):
    message = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(MyStream, self).__init__(parent)

    def write(self, message):
        self.message.emit(str(message))

    def flush(self):
        pass

'''class KImage(np.ndarray):

    def __init__(self, image, parent=None):
        super(KImage, self).__init__(parent)
        if type(image) is not np.ndarray:
            self = np.array(image)

        self.flippedh = False
        self.flippedv = False
        self.transposed = False'''


if __name__ == '__main__': #seems to open program -D
    app = QtGui.QApplication(sys.argv)

    dialog = PtychoDialog()
    dialog.show()

    myStream = MyStream()
    myStream.message.connect(dialog.on_myStream_message)

    sys.stdout = myStream

    sys.exit(app.exec_())


print("done")
