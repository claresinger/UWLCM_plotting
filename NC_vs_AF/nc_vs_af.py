from sys import argv, path, maxsize
path.insert(0, "/home/piotr/usr/local/lib/python2.7/dist-packages/")

import h5py
import numpy as np
import matplotlib.pyplot as plt
from libcloudphxx import common as lcmn

# print whole np arrays
np.set_printoptions(threshold=maxsize)

#plt.rcParams.update({'font.size': 40})
#plt.figure(figsize=(40,40))

timestep = 72000

input_dir = argv[1]
outfile = argv[2]

rhod = h5py.File(input_dir + "/const.h5", "r")["G"][:,:,:]
p_e = h5py.File(input_dir + "/const.h5", "r")["p_e"][:]
nx, ny, nz = rhod.shape
dz = h5py.File(input_dir + "/const.h5", "r").attrs["dz"]

filename = input_dir + "/timestep" + str(timestep).zfill(10) + ".h5"
rl = (h5py.File(filename, "r")["cloud_rw_mom3"][:,:,:] + h5py.File(filename, "r")["rain_rw_mom3"][:,:,:]) * 4. / 3. * 3.1416 * 1e3; # kg/kg
nc = h5py.File(filename, "r")["cloud_rw_mom0"][:,:,:] * rhod / 1e6; # 1 / cm^3

# cloudiness mask - as in RICO paper
#cloudy_mask = rl
#cloudy_mask = np.where(rl > 1e-5, 1, 0)

# ---- adiabatic LWC ----
adia_rl = np.zeros([nx, ny, nz])
# th and rv
th = h5py.File(filename, "r")["th"][:,:,:];
rv = h5py.File(filename, "r")["rv"][:,:,:];

# T
Vexner = np.vectorize(lcmn.exner)
T = th * Vexner(p_e.astype(float))

# RH
Vr_vs = np.vectorize(lcmn.r_vs)
r_vs = Vr_vs(T, p_e.astype(float))
RH = rv / r_vs

# cloud base
clb_idx = np.argmax(RH > 1, axis=2)

# clb condition per column
clb_rv = np.zeros([nx, ny])
#clb_th = np.zeros([nx, ny])

evap_lat = 2.5e6 # [J/kg] latent heat of evaporation
for i, j in zip(np.arange(nx), np.arange(ny)):
  parcel_rv = rv[i, j, clb_idx[i, j]]
  parcel_th = th[i, j, clb_idx[i, j]]
  for k in np.arange(nz):
    if k < clb_idx[i, j]:
      adia_rl[i,j,k] = 0
    else:
      parcel_T = parcel_th * lcmn.exner(p_e.astype(float)[k])
      delta_rv = parcel_rv - lcmn.r_vs(parcel_T, p_e.astype(float)[k])
      parcel_rv -= delta_rv
      parcel_th += delta_rv * evap_lat / lcmn.c_pd / lcmn.exner(p_e.astype(float)[k])
      adia_rl[i,j,k] = rl[i,j,k] / delta_rv

#      adia_rl[i,j,k] = clb_rv[i,j] - r_vs[i,j,k]

#adia_rl = np.where(adia_rl > 0., adia_rl, 0)
#print adia_rl

# translate rl to AF
AF = np.where(adia_rl > 0., rl / adia_rl, 0)
#AF = np.where(adia_rl > 1e-5, rl / adia_rl, 0)

#print AF
plt.plot(AF.flatten(), nc.flatten(), 'o')

#plt.plot((rl*cloudy_mask).flatten(), (nc*cloudy_mask).flatten(), 'o')
#
plt.xscale('log')
#
plt.show()
