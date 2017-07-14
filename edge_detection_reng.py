from __future__ import print_function

import tomopy

# Project: ptycho_gui

import os
import sys
import time
#new file imports -D

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
import os
import sys
import time
import scipy.misc
from PIL import Image
import Corners
import cv2


import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage as ndi

from skimage import feature
from skimage import filters






filename = "/Users/Dmitry/PycharmProjects/Mk2/tomo_wo3_xrf.h5"

with h5py.File(filename, 'r') as f:  # This works to open .h5 files. However, throws weird pickle error -D
    a = f['proj'][()]

filename2 = "/Users/Dmitry/PycharmProjects/Mk2/tomo_2_Ga_K.h5"

with h5py.File(filename2, 'r') as f:  # This works to open .h5 files. However, throws weird pickle error -D
    b = f['proj'][()]


def edge_find(im):
    # im = np.zeros((128, 128))
    # im[32:-32, 32:-32] = 1
    #
    # im = ndi.rotate(im, 15, mode='constant')
    # im = ndi.gaussian_filter(im, 4)
    # im += 0.2 * np.random.random(im.shape)
    #
    # Compute the Canny filter for two values of sigma
    edges1 = feature.canny(im, sigma=1., low_threshold=0.1, high_threshold=0.9, mask=None,
          use_quantiles=True)
    edges2 = feature.canny(im, sigma=3., low_threshold=0.1, high_threshold=0.9, mask=None,
          use_quantiles=True)

    # display results
    fig, (ax1, ax2, ax3) = plt.subplots(nrows=1, ncols=3, figsize=(8, 3),
                                        sharex=True, sharey=True)

    ax1.imshow(im, cmap=plt.cm.gray)
    ax1.axis('off')
    ax1.set_title('noisy image', fontsize=20)

    ax2.imshow(edges1, cmap=plt.cm.gray)
    ax2.axis('off')
    ax2.set_title('Canny filter, $\sigma=1$', fontsize=20)

    ax3.imshow(edges2, cmap=plt.cm.gray)
    ax3.axis('off')
    ax3.set_title('Canny filter, $\sigma=3$', fontsize=20)

    fig.tight_layout()

    plt.show()






for i in range(1):
    j=i+20
    single = a[j, :, :]
    edge_find(single)
    single = b[j, :, :]
    edge_find(single)








# Generate noisy image of a square
