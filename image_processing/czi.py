import aicspylibczi
import napari
import numpy as np
import os
import pathlib
import tifffile
import time
from datetime import timezone, datetime, timedelta
from image_processing.subtract_background import subtract_background
import gc

from guppy import hpy
from sys import getsizeof # To know the size of the variables in bytes

def read(args, czi):
  #reads the czi images and does background subtraction or normalization on it. It returns a np.array of values.

  data = []
  dims_shape = czi.dims_shape()

  #Debugger
  #hp = hpy()
  #hp.setrelheap()
  #h = hp.heap()
  #print('INITIAL SITUATION \n', h,'\n ---------------------')

  if not 'C' in dims_shape[0]:
    raise Exception("Image lacks Channels")

  channels = dims_shape[0]['C'][1]
  print('info – czi dims_shape: ', dims_shape)
  # M is mosaic: index of tile for compositing a scene
  print('info – czi channels: ', channels)

  read_time_total = 0
  subtract_background_time_total = 0

  for channel in range(channels):
    if args.time: read_time = time.monotonic()
    mosaic = czi.read_mosaic(C=channel, scale_factor=1)
    #To create a defined size of dataset with all the information needed to do it
    # meaning channels and size of the final stitched image
    #if channel == 0:
      #data = np.zeros((channels, np.shape(np.array(mosaic))[2], np.shape(np.array(mosaic))[3]))
      #print('Created dataset of size ', np.shape(data))
    print('Mosaic', channel, 'DONE', np.shape(mosaic[0,0,:,:]))
    if args.time: read_time_total += time.monotonic() - read_time

    if args.time: subtract_background_time = time.monotonic()
    if not args.disable_subtract_background:
      #commented here to remove a local variable that isn't needed
      #normed_mosaic_data = norm_by(mosaic[0, 0, :, :], 5, 98) * 255
      #normed_mosaic_data = subtract_background(mosaic[0, 0, :, :])
      data.append(norm_by(mosaic[0, 0, :, :], 5, 98) * 255)
      #data[channel,:,:] = norm_by(mosaic[0, 0, :, :], 5, 98) * 255
      print(f'''info – channel {channel} read, and image processed''') #subtraction or normalization
    else:
      data.append(mosaic[0,0,:,:])
      #data[channel,:,:] = mosaic[0,0,:,:]
      print(f'''info – channel {channel} read''')
    if args.time: subtract_background_time_total += time.monotonic() - subtract_background_time
    #help free memory with garbage collector
    del mosaic
    gc.collect()

    #h = hp.heap()
    #print('AFTER Garbage collect \n', h,'\n ---------------------')

  if args.time:
    print('info – czi.read_mosaic time', timedelta(seconds=read_time_total))
    print('info – subtract_background time', timedelta(seconds=subtract_background_time_total))

  #h = hp.heap()
  #print('FINAL SITUATION \n', h,'\n ---------------------','\n ---------------------')

  print('data shape: ', np.shape(data), ' and data type: ', type(data))
  return np.array(data)

def get_processed_czis(args, czis):
  return read(args, czis[0])

def get_czis(files):
  # Takes the string of files and creates np.array of the czi images 
  # WARNING: the array consists of CZI images not transformed to np.array yet.
  czis = []

  for file in files:
    czis.append(aicspylibczi.CziFile(pathlib.Path(file)))
  return np.array(czis)


#Don't need this code i think...
  def norm_by(x, min_, max_):
    norms = np.percentile(x, [min_, max_])
    i2 = np.clip((x - norms[0])/(norms[1]-norms[0]), 0, 1)
    return i2
