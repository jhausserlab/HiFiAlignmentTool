import multiprocessing as mp
import pathlib
import aicspylibczi
import pprint
import napari
import numpy as np

pp = pprint.PrettyPrinter(indent=2)

def norm_by(x, min_, max_):
    norms = np.percentile(x, [min_, max_])
    i2 = np.clip((x - norms[0])/(norms[1]-norms[0]), 0, 1)
    return i2

def print_info(czi):
  dims_shape = czi.dims_shape()
  mosaic_size = czi.read_mosaic_size()

  print('dims_shape')
  pp.pprint(dims_shape)
  print('mosaic_size')
  pp.pprint(mosaic_size)

def read(czi, channel):
  # print('run channel', channel)
  # scale_factor = 1
  # # mosaic_data = czi.read_mosaic((-132192, 25704, width, height), C=0, scale_factor=scale_factor)
  # mosaic_data = czi.read_mosaic(C=channel, scale_factor=scale_factor)
  # normed_mosaic_data = norm_by(mosaic_data[0, 0, :, :], 5, 98) * 255

  # return normed_mosaic_data
  # print(czi.dims_shape())
  return '1'

def get_mosaic_data(czi):
  print_info(czi)
  dims_shape = czi.dims_shape()
  c = dims_shape[0]['C'][1]
  channels = range(c)
  print(channels)

  nprocs = mp.cpu_count()
  processes = min(c, nprocs -1)
  print(f"""Number of CPU cores: {nprocs} \n channels: {channels} \n will run {processes} processes""")
  pool = mp.Pool(processes=processes)
  result = pool.map(lambda x: read(czi, x), channels)
  # result = map(lambda x: read(czi, x), channels)

  return list(result)

def get_czis(file):
  # sorting?
  # "file handling: load files in order of numerical round, not alphab sorting"
  return aicspylibczi.CziFile(pathlib.Path(file))



def images(files):
  czis = map(get_czis, files)
  channels = map(get_mosaic_data, czis)
  print('list!!!')
  test = list(channels)

  print(test[0][0])
  # with napari.gui_qt():
    # viewer = napari.view_image(test[0][0].astype(np.uint8))
    # print("display_with_napari", time.process_time() - display_with_napari)
