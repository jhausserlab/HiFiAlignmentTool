#import cv2
import numpy as np
from skimage import data, io
from skimage.feature import register_translation
#from skimage.feature.register_translation import _upsampled_dft # not needed
from scipy.ndimage import fourier_shift
from scipy.ndimage import shift

## align images based on the first dapi provided
## 
## register_translation, is fast
def align_images(args, processed_czis):
  aligned_images = []

  for czi in processed_czis:
    #print('length of a', len(aligned_images))

    if len(aligned_images):
      dapi_target = aligned_images[0][-1]
      dapi_to_offset = czi[-1]
      print('dapi_target shape', np.shape(dapi_target))
      print('dapi_to_offset shape', np.shape(dapi_to_offset))
      shifted, error, diffphase = register_translation(dapi_target, dapi_to_offset, 100)

      print(f"Detected subpixel offset (y, x): {shifted}")

      alignedCzi = []

      for image_from_channel in czi:
        #print('channel size', np.shape(image_from_channel))

        corrected_image = shift(image_from_channel, shift=(shifted[0], shifted[1]), mode='constant')

        alignedCzi.append(corrected_image)

      print('transformed channels done')
      aligned_images.append(alignedCzi)

    else:
      aligned_images.append(czi)

  return aligned_images
