#import cv2
import numpy as np
from skimage import data, io
from skimage.feature import register_translation
#from skimage.feature.register_translation import _upsampled_dft # not needed
from scipy.ndimage import fourier_shift
from scipy.ndimage import shift

## align images based on the first dapi provided

def align_images(args, processed_czi0, processed_czi):
  #all channels minus the dapi of processed_czi --- remove -1 to add the dapi of the channel
  totalChannels = np.shape(processed_czi)[0] - 1
  #this will be a problem when czi have different shapes (to work on soon)
  aligned_images = []

  dapi_target = processed_czi0[-1]
  dapi_to_offset = processed_czi[-1]
  print('dapi_target shape', np.shape(dapi_target))
  print('dapi_to_offset shape', np.shape(dapi_to_offset))
  shifted, error, diffphase = register_translation(dapi_target, dapi_to_offset, 100)
  print(f"Detected subpixel offset (y, x): {shifted}")

  #DAPI is the last channel, thus i don't have to read the last channel as it is used for alignment
  for channel in range(totalChannels):
    #aligned_images[channel,:,:] = shift(processed_czi[channel,:,:], shift=(shifted[0], shifted[1]), mode='constant')
    aligned_images.append(shift(processed_czi[channel,:,:], shift=(shifted[0], shifted[1]), mode='constant'))
  print('transformed channels done, image is of size', np.shape(aligned_images))
  return aligned_images

'''
#OLD CODE 10/09/20
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
'''