import numpy as np
from image_processing.czi import get_czis, get_processed_czis
from image_processing.registration import align_images
import time
from datetime import timedelta
import numpy as np
from skimage import data, io
from skimage.registration import phase_cross_correlation # new form of register_translation
from scipy.ndimage import shift

# def toType(x):
#   return x.astype(np.uint8)

def get_registration(args, processed_czi0, processed_czi):
  if args.disable_registration:
    return np.concatenate((processed_czi0, processed_czi), axis = 0)
  else:
    return align_images(args, processed_czi0, processed_czi)

## align images based on the first dapi provided

def align_images(args, processed_czi0, processed_czi):

  aligned_images = []

  dapi_target = processed_czi0[-1]
  dapi_to_offset = processed_czi[-1]
  print('dapi_target shape', np.shape(dapi_target))
  print('dapi_to_offset shape', np.shape(dapi_to_offset))

  Xmax, Ymax = get_max_shape(image_shapes)

  print('Recalibrating image size to', Xmax, Ymax)

  max_czi0 = np.empty()


  shifted, error, diffphase = phase_cross_correlation(dapi_target, dapi_to_offset)
  print(f"Detected subpixel offset (y, x): {shifted}")

  for channel in range(np.shape(processed_czi)[0]):
    aligned_images.append(shift(processed_czi[channel,:,:], shift=(shifted[0], shifted[1]), mode='constant'))
  print('transformed channels done, image is of size', np.shape(aligned_images))
  return aligned_images





#img = AICSImage("../output/old.tif") #../czi/align1.czi   ../align2.czi   ../output/2020-08-27_1598554331997.ome.tif
#channel_names = img.get_channel_names()

#with napari.gui_qt():
#    viewer = napari.Viewer()
#    for c, c_name in enumerate(channel_names):
#        viewer.add_image(img.get_image_data("ZYX", C=c, S=0, T=0), 
#                         name=c_name)