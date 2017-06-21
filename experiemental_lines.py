from __future__ import print_function


import numpy as np
import matplotlib.pyplot as plt
import h5py
import align_class as ac
from scipy.ndimage.measurements import center_of_mass
import sys


__author__ = 'kylehenry' #testing
# Project: ptycho_gui

import os
import sys
import time
#new file imports -D

superfile= 0

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
from scipy.ndimage.measurements import center_of_mass

import scipy.misc as sm
import scipy.stats as st
import math
from scipy import interpolate
from scipy import ndimage
from mpl_toolkits.axes_grid1 import make_axes_locatable

import matplotlib.pyplot as plt

#import align_class #kcode
#import ptycho_trans_parallel as ptycho #kcode

#from PIL import Image
import copy

import xml.etree.cElementTree as ET

CMAP_PREVIEW_PATH = os.path.join(os.path.dirname(__file__), '.cmap_previews')

get_save_filename = QtGui.QFileDialog.getSaveFileName
get_open_filename = QtGui.QFileDialog.getOpenFileName

#align_proj implementation
import align_class as ac
app = QtGui.QApplication(sys.argv)

test_line = QtGui.QFileDialog.getOpenFileName
print(test_line)