import multiprocessing as mp
import pathlib
import aicspylibczi
import pprint
import napari
import numpy as np
from image_processing.subtract_background import subtract_background

pp = pprint.PrettyPrinter(indent=2)

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

def read(czi):
  data = []
  dims_shape = czi.dims_shape()
  channels = dims_shape[0]['C'][1]
  print('channels', channels)

  # mosaic_data = czi.read_mosaic((-132192, 25704, width, height), C=0, scale_factor=scale_factor)

  for channel in range(channels):
    mosaic = czi.read_mosaic(C=channel, scale_factor=1)
    normed_mosaic_data = norm_by(mosaic[0, 0, :, :], 5, 98) * 255

    data.append(normed_mosaic_data)

  return data

def get_processed_czis(czis):
  processed_czis = []

  for czi in czis:
    processed_czis.append(read(czi))

  return processed_czis

def get_czis(files):
  czis = []

  for file in files:
    czis.append(aicspylibczi.CziFile(pathlib.Path(file)))

  # sorting?
  # "file handling: load files in order of numerical round, not alphab sorting"
  return np.array(czis)

def toType(x):
  return x.astype(np.uint8)

def images(files):
  czis = get_czis(files)
  processed_czis = get_processed_czis(czis)
  print('np.shape', np.shape(processed_czis))
  print('type', type(processed_czis))

  with napari.gui_qt():
    viewer = napari.Viewer()
    for czi in processed_czis:
      print('np.shape', np.shape(czi))
      viewer.add_image(np.array(czi))
    # viewer = napari.view_image(processed_czis[0][0].astype(np.uint8))
    # print("display_with_napari", time.process_time() - display_with_napari)
