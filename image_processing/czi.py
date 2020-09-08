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

def norm_by(x, min_, max_):
    norms = np.percentile(x, [min_, max_])
    i2 = np.clip((x - norms[0])/(norms[1]-norms[0]), 0, 1)
    return i2

# def print_info(czi):
#   dims_shape = czi.dims_shape()
#   mosaic_size = czi.read_mosaic_size()

#   print('dims_shape')
#   pp.pprint(dims_shape)
#   print('mosaic_size')
#   pp.pprint(mosaic_size)

def read(args, czi):
  #reads the czi images and does background subtraction or normalization on it. It returns a np.array of values.
  data = []
  dims_shape = czi.dims_shape()

  #Debugger
  hp = hpy()
  #hp.setrelheal() # To start registering how memory is used
  #h = hp.heap() # Variable to use to read memory usage
  #print(h) # To see what is going on between setrelheal and the print.

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
    print('Mosaic', channel, 'DONE', np.shape(mosaic[0,0,:,:]))
    if args.time: read_time_total += time.monotonic() - read_time

    if args.time: subtract_background_time = time.monotonic()
    if not args.disable_subtract_background:
      #commented here to remove a local variable that isn't needed
      #normed_mosaic_data =  norm_by(mosaic[0, 0, :, :], 5, 98) * 255
      #normed_mosaic_data = subtract_background(mosaic[0, 0, :, :])
      data.append(norm_by(mosaic[0, 0, :, :], 5, 98) * 255)
      print(f'''info – channel {channel} read, and image processed''') #subtraction or normalization
    else:
      data.append(mosaic[0,0,:,:])
      print(f'''info – channel {channel} read''')
    if args.time: subtract_background_time_total += time.monotonic() - subtract_background_time
    #help free memory with garbage collector
    del mosaic
    gc.collect()

  if args.time:
    print('info – czi.read_mosaic time', timedelta(seconds=read_time_total))
    print('info – subtract_background time', timedelta(seconds=subtract_background_time_total))

  print('data shape ', np.shape(data))
  return data

def get_processed_czis(args, czis):
  #takes the np.array of czi and processes the array by doing background subtraction or normalization.
  processed_czis = []

  for czi in czis:
    processed_czis.append(read(args, czi))
  return processed_czis

def get_czis(files):
  # Takes the string of files and creates np.array of the czi images 
  # WARNING: the array consists of CZI images not transformed to values yet.
  czis = []

  for file in files:
    czis.append(aicspylibczi.CziFile(pathlib.Path(file)))

  # sorting?
  # "file handling: load files in order of numerical round, not alphab sorting"
  return np.array(czis)

def show(args, images):
  if not args.yes:
    with napari.gui_qt():
      viewer = napari.Viewer()
      # viewer = napari.view_image(images[0][0].astype(np.uint8))
      for czi in images:
        viewer.add_image(np.array(czi))

def write(args, imagesToShape):
  shape = np.shape(imagesToShape)
  newShape = shape[0] * shape[1]
  images = np.array(imagesToShape).reshape(1, newShape, shape[2], shape[3])
  images = np.array(imagesToShape).reshape(shape)
  #images = np.array(imagesToShape)
  #print(type(images))

  #print('np.array(images).flatten()', np.shape(images))
  if args.destination:
    if os.path.exists(args.destination):
      name = f'{datetime.now().strftime("%Y-%m-%d")}_{int(datetime.now(tz=timezone.utc).timestamp() * 1000)}'
      extension = 'ome.tif'
      file = f'{os.path.basename(args.destination)}/{name}.{extension}'

      with tifffile.TiffWriter(file, bigtiff = True) as tif:
        # additional metadata can be added, and in a more compatible format
        # axes is just an (incorrect) example
        # https://stackoverflow.com/questions/20529187/what-is-the-best-way-to-save-image-metadata-alongside-a-tif
        #for image in images:
        #tif.save(images, metadata={'axes':'TZCYX'}) <--- metadata does not work
        tif.save(images)
    else:
      print('destination path does not exist')
