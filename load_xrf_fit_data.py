import numpy as np
import matplotlib.pyplot as plt
#import rm_grid_error as rge
import align_class as ac
import tifffile as tf
import line_align as la
import h5py
import sys
import scipy

#from databroker import get_table, db
#from hxntools.handlers import register
#import filestore
#register()

def match_line(ref,line):
    n = np.size(ref)
    cc = np.correlate(ref,line,'same')
    index = np.where(cc == np.max(cc))
    return index[0][0] - n/2


def find_vertical_shift(proj):
    nx,ny = np.shape(proj)
    ref = np.squeeze(proj[:,0])
    y_shift = np.zeros(ny)
    proj_new = np.zeros_like(proj)
    for i in range(ny):
        line = np.squeeze(proj[:,i])
        y_shift[i] = match_line(ref,line)
        proj_new[:,i] = np.roll(line,np.int(y_shift[i]),0)
    return y_shift, proj_new

def congrid_fft(array_in, shape):
    x_in, y_in = np.shape(array_in)
    array_in_fft = np.fft.fftshift(np.fft.fftn(np.fft.fftshift(array_in)))/np.sqrt(1.*x_in*y_in)
    array_in_fft_n = np.zeros((shape[0],shape[1])).astype(complex)
    if x_in < shape[0]:
        array_in_fft_n[shape[0]/2-x_in/2:shape[0]/2+x_in/2,shape[1]/2-y_in/2:shape[1]/2+y_in/2] \
            = array_in_fft
    else:
        array_in_fft_n \
            = array_in_fft[x_in/2-shape[0]/2:shape[0]/2+x_in/2,y_in/2-shape[1]/2:shape[1]/2+y_in/2]

    array_out =  np.fft.fftshift(np.fft.ifftn(np.fft.fftshift(array_in_fft_n)))*np.sqrt(1.*shape[0]*shape[1])
    return array_out

fname = sys.argv[1] #fname='tomo_wo3_xrf'
elem = sys.argv[2]
fdir = '/data/users/2017Q2/Chiu_2017Q2/'

angle_1 = np.arange(-90,55,2)
angle_2 = np.arange(56,63,2)
angle_3 = np.arange(64,89,2)
angle_4 = np.arange(90,91,2)
angle_list = np.array(np.concatenate((angle_1,angle_2,angle_3,angle_4),axis=0))

#angle_list = np.delete(angle_list,[0,1,4,23,63,65,71,85,88],axis=0)

scan_1 = np.arange(29524,29669,2)
scan_2 = np.arange(29671,29678,2)
scan_3 = np.arange(29681,29706,2)
scan_4 = np.arange(29709,29710,2)
scan_list = np.array(np.concatenate((scan_1,scan_2,scan_3,scan_4),axis=0))

#scan_list = np.delete(scan_list,[0,1,4,23,63,65,71,85,88],axis=0)


print(np.size(angle_list),np.size(scan_list))
print(angle_list)
print(scan_list)

num_frame = np.size(angle_list)

plt.figure(0)

for i in range(num_frame):
    fdir_tmp = fdir+'output_tiff_scan2D_'+np.str(scan_list[i])+'/'
    fname_tmp = 'detsum_'+elem+'_'+np.str(scan_list[i])+'.tiff'
    print('loading ',i, scan_list[i],angle_list[i])
    tmp = tf.imread(fdir_tmp+fname_tmp)
    ic = tf.imread(fdir_tmp+'sclr1_ch4_'+np.str(scan_list[i])+'.tiff')
    tmp /= ic
    if i == 0:
        ny,nx = np.shape(tmp)
        xrf = np.zeros((num_frame,ny,nx))
    if angle_list[i] > -45:
        tmp = np.fliplr(tmp)
    bg = np.mean(tmp[:,:10])
    tmp -= bg
    tmp[tmp<0] = 0
    xrf[i,:,:] = tmp
    plt.imshow(xrf[i,:,:],interpolation='none')
    plt.title(np.str(scan_list[i])+' '+np.str(angle_list[i]))
    plt.pause(0.01)
    plt.show()

f = h5py.File(fname+'_'+elem+'.h5','w')
dset = f.create_dataset('proj', data=xrf)
dset = f.create_dataset('angle', data=angle_list)
f.close()
