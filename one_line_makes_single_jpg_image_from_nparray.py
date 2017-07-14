
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



def findCorners(img, window_size, k, thresh):
    """
    Finds and returns list of corners and new image with corners drawn
    :param img: The original image
    :param window_size: The size (side length) of the sliding window
    :param k: Harris corner constant. Usually 0.04 - 0.06
    :param thresh: The threshold above which a corner is counted
    :return:
    """
    #Find x and y derivatives
    dy, dx = np.gradient(img)
    Ixx = dx**2
    Ixy = dy*dx
    Iyy = dy**2
    height = img.shape[0]
    width = img.shape[1]

    cornerList = []
    newImg = img.copy()
    #color_img = cv2.cvtColor(newImg, cv2.COLOR_GRAY2RGB)
    color_img = newImg
    offset = window_size/2

    #Loop through image and find our corners
    print("Finding Corners...")
    for y in range(offset, height-offset):
        for x in range(offset, width-offset):
            #Calculate sum of squares
            windowIxx = Ixx[y-offset:y+offset+1, x-offset:x+offset+1]
            windowIxy = Ixy[y-offset:y+offset+1, x-offset:x+offset+1]
            windowIyy = Iyy[y-offset:y+offset+1, x-offset:x+offset+1]
            Sxx = windowIxx.sum()
            Sxy = windowIxy.sum()
            Syy = windowIyy.sum()

            #Find determinant and trace, use to get corner response
            det = (Sxx * Syy) - (Sxy**2)
            trace = Sxx + Syy
            r = det - k*(trace**2)

            #If corner response is over threshold, color the point and add to corner list
            if r > thresh:
                print(x, y, r)
                cornerList.append([x, y, r])
                color_img.itemset((y, x, 0), 0)
                color_img.itemset((y, x, 1), 0)
                color_img.itemset((y, x, 2), 255)
    return color_img, cornerList





filename = "/Users/Dmitry/PycharmProjects/Mk2/tomo_2_Ga_K.h5"

with h5py.File(filename, 'r') as f:  # This works to open .h5 files. However, throws weird pickle error -D
    a = f['proj'][()]





for i in range(5):
    j=i+20
    single = a[j, :, :]
    #scipy.misc.toimage(single, cmin=0.0, cmax=np.amax(single)).save('Application/outfile.jpg')
    #Corners.action("Application/outfile.jpg", i, 2, 0.04, 10000)
    Corners.action(single, i, 2, 0.04, 10000)

    #print("Single type", type(single))
    #TODO: get rid of really dumb step where numpy array is written to jpg here
    # and then jpg is made into numpy array in Corners





print(single.shape)







