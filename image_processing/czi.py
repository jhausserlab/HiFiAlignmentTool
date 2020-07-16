import pathlib
import aicspylibczi
import numpy as np
from image_processing.subtract_background import subtract_background
import napari

def norm_by(x, min_, max_):
    norms = np.percentile(x, [min_, max_])
    i2 = np.clip((x - norms[0])/(norms[1]-norms[0]), 0, 1)
    return i2

def read(czi):
  data = []
  dims_shape = czi.dims_shape()

  if not 'C' in dims_shape[0]:
    raise Exception("Image lacks Channels")

  channels = dims_shape[0]['C'][1]
  print('dims_shape', dims_shape)
  print('channels', channels)

  # mosaic_data = czi.read_mosaic((-132192, 25704, width, height), C=0, scale_factor=scale_factor)

  for channel in range(channels):
    # print_info(czi)
    mosaic = czi.read_mosaic(C=channel, scale_factor=1)
    # print('mosaic shape', np.shape(mosaic[0, 0, :, :]))

    # normed_mosaic_data = mosaic[0, 0, :, :]
    # normed_mosaic_data = norm_by(mosaic[0, 0, :, :], 5, 98) * 255
    normed_mosaic_data = subtract_background(mosaic[0, 0, :, :])

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

def show(args, images):
  print('c - show aligned images', args.show)

  if args.show:
    with napari.gui_qt():
      viewer = napari.Viewer()
      for czi in images:
        # print('np.shape', np.shape(czi))
        viewer.add_image(np.array(czi))
