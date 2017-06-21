import numpy as np
import matplotlib.pyplot as plt
import h5py
import align_class as ac
from scipy.ndimage.measurements import center_of_mass
import sys

def align_image(superfile ): #put in file parameters
    def check_diff(ref,line):
        return np.sqrt(np.sum((ref-line)**2))

    def match_line(ref,line):
        n = np.size(line)
        offset = np.arange(n) - n/2
        error = np.zeros(n) + 1.e9
        for i in range(n):
            tmp = np.roll(line,np.int(offset[i]),0)
            if offset[i] < 0:
                error[i] = check_diff(ref[:offset[i]],tmp[:offset[i]])
            else:
                error[i] = check_diff(ref[offset[i]:],tmp[offset[i]:])
        index = np.where(error == np.min(error))
        #print(index[0][0])
        return offset[index[0][0]]

    def match_line_bp(ref,line):
        n = np.size(ref)
        cc = np.correlate(ref,line,'same')
        index = np.where(cc == np.max(cc))
        return index[0][0] - n/2


    def find_vertical_shift(proj):
        nx,ny = np.shape(proj)
        #ref = np.squeeze(proj[:,0])
        y_shift = np.zeros(ny)
        proj_new = np.zeros_like(proj)
        for i in range(ny):
            line = np.squeeze(proj[:,i])
            if i == 0:
                ref = line
                line_0 = line
            else:
                ref = line_0
            #norm_ref = np.sqrt(sum(ref)**2)
            #norm = np.sqrt(sum(line)**2)
            #line = line * norm_ref / norm
            y_shift[i] = match_line(ref,line)
            proj_new[:,i] = np.roll(line,np.int(y_shift[i]),0)
        return y_shift, proj_new

#TODO: Information needed"
    #file name
    #element
    #aligned or not

    fname = sys.argv[1]
    elem = sys.argv[2]



    check_align_flag = np.int(sys.argv[3])
    f = h5py.File(fname+'_'+elem+'.h5','r')
    data = np.array(f['proj'])
    angle = np.array(f['angle'])
    if not check_align_flag:
        f_shift = h5py.File(fname+'_xyshift.h5','r')
        x_shift = np.array(f_shift['x_shift'])
        y_shift = np.array(f_shift['y_shift'])
        f_shift.close()
    f.close()
    #data = np.delete(data,[1,19,20,21,22,33],axis=0)
    #angle = np.delete(angle,[1,19,20,21,22,33],axis=0)


    nz,ny,nx = np.shape(data)
    ys = 20
    ye = 100
    xs = 0
    xe = nx

    print(np.mean(data[0,:,:]))

    if check_align_flag:
        for i in range(nz):
            slice = np.squeeze(data[i,ys:ye,xs:xe].copy())
            norm = np.sqrt(np.sum(slice**2))
            if i == 0:
                cm_y = np.zeros(nz)
                proj_y = np.zeros((ye-ys,nz))
                norm_ref = norm
            slice = slice*norm_ref/norm
            data[i,:,:] *= norm_ref/norm
            cmx, cm_y[i] = center_of_mass(slice)
            proj_y[:,i] = np.sum(slice,axis=1)

        y_shift = cm_y - cm_y[0]
        x_shift, proj_new = find_vertical_shift(proj_y)
        f = h5py.File(fname+'_xyshift.h5','w')
        f.create_dataset('x_shift',data=x_shift)
        f.create_dataset('y_shift',data=y_shift)
        f.close

    print(np.mean(data[0,:,:]))


    plt.figure()
    for i in range(nz):
        print(i,x_shift[i],y_shift[i])
        tmp = ac.pixel_shift_2d(data[i,:,:],-1*x_shift[i],y_shift[i])
        tmp = tmp.real
        tmp[tmp <0 ] = 0
        data[i,:,:] =tmp.copy()
        plt.imshow(data[i,:,:],interpolation='none')
        plt.pause(0.1)
        plt.show()

    print(np.mean(data[0,:,:]))


    f = h5py.File(fname+'_'+elem+'_aligned_new.h5','w')
    f.create_dataset('proj',data=data)
    f.create_dataset('angle',data=angle)

    f.close()
    #this will return the new numpy array that is alinged
    return data
