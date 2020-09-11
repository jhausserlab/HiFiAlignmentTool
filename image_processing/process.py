import numpy as np
from image_processing.czi import get_czis, get_processed_czis
from image_processing.registration import align_images
import time
from datetime import timedelta

def get_registration(args, processed_czi0, processed_czi):
  if args.disable_registration:
    return np.concatenate((processed_czi0, processed_czi), axis = 0)
  else:
    return align_images(args, processed_czi0, processed_czi)


def get_images(args, file):

  print('--- Processing:', file.split())
  processed_czi = get_processed_czis(args,get_czis(file.split()))
  print('Shape of processed image i is: ', np.shape(processed_czi), type(processed_czi))
  #------------------------
  return processed_czi