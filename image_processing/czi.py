import aicspylibczi
import numpy as np
import os
import pathlib
import tifffile
import gc
from sys import getsizeof

def get_stitched_czis(args, czi):
  #stitches the czi images. It returns a np.array of values.
  data = []
  dims_shape = czi.dims_shape()

  if not 'C' in dims_shape[0]:
    raise Exception("Image lacks Channels")

  channels = dims_shape[0]['C'][1]
  print('info – czi dims_shape: ', dims_shape)
  # M is mosaic: index of tile for compositing a scene
  print('info – czi channels: ', channels)

  for channel in range(channels):
    mosaic = czi.read_mosaic(C=channel, scale_factor=1)
    print('info – channel', channel, 'stitched')
    data.append(mosaic[0,0,:,:])

    del mosaic
    gc.collect()

  return np.array(data)

#def get_stitched_czis(args, czis):
#  return stitch(args, czis[0])

def get_czis(files):
  # Takes the string of files and creates np.array of the czi images 
  # WARNING: the array consists of CZI images not transformed to np.array yet.
  czis = []

  for file in files:
    czis.append(aicspylibczi.CziFile(pathlib.Path(file)))
  return np.array(czis)

def get_images(args, file):
  #Takes file as argument and returns the stitched images of the file
  print('--- Processing:', file.split())
  stitched_czi = get_stitched_czis(args,get_czis(file.split())[0])
  print('Shape of stitched shape: ', np.shape(stitched_czi), 'of size', getsizeof(np.array(stitched_czi))/10**6, 'MB')
  #------------------------
  return stitched_czi
  