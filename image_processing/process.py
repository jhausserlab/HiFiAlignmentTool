import numpy as np
from image_processing.czi import get_czis, get_processed_czis
from image_processing.registration import align_images

# def toType(x):
#   return x.astype(np.uint8)

def get_images(files):
  czis = get_czis(files)
  processed_czis = get_processed_czis(czis)
  return align_images(processed_czis)
