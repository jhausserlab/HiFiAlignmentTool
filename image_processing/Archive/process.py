import numpy as np
from image_processing.czi import get_czis, get_processed_czis

def get_images(args, file):

  print('--- Processing:', file.split())
  processed_czi = get_processed_czis(args,get_czis(file.split()))
  print('Shape of processed image i is: ', np.shape(processed_czi), type(processed_czi))
  #------------------------
  return processed_czi