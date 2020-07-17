import numpy as np
from image_processing.czi import get_czis, get_processed_czis
from image_processing.registration import align_images
import time
from datetime import timedelta

# def toType(x):
#   return x.astype(np.uint8)

def get_images(args, files):
  czis = get_czis(files)
  processed_czis = get_processed_czis(args, czis)

  if args.time: aligned_images_time = time.monotonic()
  aligned_images = align_images(args, processed_czis)
  if args.time: print('info – image registration', timedelta(seconds=time.monotonic() - aligned_images_time))

  return aligned_images
