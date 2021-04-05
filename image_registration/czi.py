import aicspylibczi
import numpy as np
import os
import pathlib
import tifffile
import gc
from sys import getsizeof

def get_reassembled_czi(czi):
  #Reassembles the czi images. It returns a np.array of uint16.
  data = []
  dims_shape = czi.dims_shape()

  if not 'C' in dims_shape[0]:
    raise Exception("Image lacks Channels")

  channels = dims_shape[0]['C'][1]
  print('info – czi dim_shape: ', dims_shape)
  # M is mosaic: index of tile for compositing a scene
  print('info – czi channels: ', channels)

  for channel in range(channels):
    mosaic = czi.read_mosaic(C=channel, scale_factor=1)
    print('info – channel', channel, 'reassembled')

    #If Windows OS, mosaic has 3 dimensions and if it is mac/linux it is 4
    if (mosaic.ndim == 4):
      data.append(mosaic[0,0,:,:])
    else:
      data.append(mosaic[0,:,:])

    del mosaic
    gc.collect()

  return np.array(data)

def get_image(source, file):
  #Takes file as argument and returns the reassembled images of the file
  print('--- Processing:', source + '/' + file)
  czi = aicspylibczi.CziFile(pathlib.Path(source + '/' + file ))
  reassembled_czi = get_reassembled_czi(czi)
  print('Shape of reassembled_czi: ', np.shape(reassembled_czi), 'of size', getsizeof(np.array(reassembled_czi))/10**6, 'MB')
  return reassembled_czi
  