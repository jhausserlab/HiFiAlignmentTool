import numpy as np
from image_processing.czi import get_czis, get_processed_czis
from image_processing.registration import align_images
import time
from datetime import timedelta
import gc

# def toType(x):
#   return x.astype(np.uint8)

def get_registration(args, processed_czis):
  if args.disable_registration:
    return processed_czis
  else:
    return align_images(args, processed_czis)


def get_images(args, files):
  # get the czi images with get_czis, then processes the images by background subtraction or normalization
  # Finally gets the aligned images with get_registration.
  czis = get_czis(files)
  processed_czis = get_processed_czis(args, czis)
  
  # after get_processed_czis, we do not need czis anymore, we delete to free memory
  del czis
  gc.collect()

  if args.time: aligned_images_time = time.monotonic()
  aligned_images = get_registration(args, processed_czis)
  if args.time: print('info – image registration', timedelta(seconds=time.monotonic() - aligned_images_time))

  # print('aligned_images', np.shape(aligned_images))

  return aligned_images
