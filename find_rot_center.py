import tomopy
import h5py
import matplotlib.pylab as pl
import numpy as np
import sys

#fname='/data/users/2017Q2/Chiu_2017Q2/Scanning 1/alignment without data shift in X axis/'+sys.argv[1]+'.h5'
fname = sys.argv[1]+'.h5'
fname_out=sys.argv[1]+'_center.h5'
pos = np.int(sys.argv[2])
num = np.int(sys.argv[3])

f=h5py.File(fname,'r')
prj=np.array(f['proj'])
#prj = np.array(f['t0/channel0'])

theta=np.array(f['angle'])
#theta = np.arange(-90,91,2)
theta=np.array(theta.copy())/180.*np.pi

f.close()


#prj = np.swapaxes(prj,1,2)

s=prj.shape
#pos = 20 #np.int(s[1]/2)i
nn = s[2]
nn += np.mod(nn,2)
cent_test = np.zeros([num,s[2],s[2]])
cent_guess = np.linspace(nn/2-num/2,nn/2+num/2,num+1)

for i in range(num):
    print(cent_guess[i])
    cent_test[i]=tomopy.recon(prj[:,pos:pos+1,:], theta, center=cent_guess[i], algorithm='mlem',num_iter=10)

hf = h5py.File(fname_out, 'w')
hf.create_dataset('recon_slice', data=cent_test)
hf.create_dataset('rot_center',data=cent_guess)

hf.close()
