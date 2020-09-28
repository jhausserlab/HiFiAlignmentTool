# http://www.gilgalad.co.uk/post/image-registration-skimage/
#from image_processing.registration import get_aligned_imagesCV for image_processing

import numpy as np
from skimage import data, io

from skimage.registration import phase_cross_correlation # new form of register_translation
from scipy.ndimage import shift
import napari
import glob
import gc
import sys
import tifffile
from sys import getsizeof # To know the size of the variables in bytes

def alignImages(im1, im2):
#WARNING: im1 is the image to align and im2 is the image reference!
# im1 will be DAPI to align and im2 will be dapi reference

#https://www.learnopencv.com/image-alignment-feature-based-using-opencv-c-python/
#reference code
  MAX_FEATURES = 500 #number of feature points to detect in each image
  GOOD_MATCH_PERCENT = 0.15 #the 15% best feature points that match between both images
  # Convert images to grayscale ----> Dunno if we need this part (my guess is no)
  im1Gray = cv2.cvtColor(im1, cv2.COLOR_GRAY2RGB)
  im2Gray = cv2.cvtColor(im2, cv2.COLOR_GRAY2RGB)
  
  # Detect ORB features and compute descriptors.
  orb = cv2.ORB_create(MAX_FEATURES)
  # find the keypoints with ORB
  print('BASDASDASDA', np.shape(im1Gray))
  keypoints1, descriptors1 = orb.detectAndCompute(im1Gray, None) # here is im1Gray
  keypoints2, descriptors2 = orb.detectAndCompute(im2Gray, None) # here is im2Gray
  
  # Match features.
  matcher = cv2.DescriptorMatcher_create(cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING)
  matches = matcher.match(descriptors1, descriptors2, None)
  
  # Sort matches by score
  matches.sort(key=lambda x: x.distance, reverse=False)

  # Remove not so good matches
  numGoodMatches = int(len(matches) * GOOD_MATCH_PERCENT)
  print('GOOD MATCHES', numGoodMatches)
  matches = matches[:numGoodMatches]
  
  # Extract location of good matches
  points1 = np.zeros((len(matches), 2), dtype=np.float32)
  points2 = np.zeros((len(matches), 2), dtype=np.float32)

  for i, match in enumerate(matches):
    points1[i, :] = keypoints1[match.queryIdx].pt
    points2[i, :] = keypoints2[match.trainIdx].pt
  
  # Find homography
  h, mask = cv2.findHomography(points1, points2, cv2.RANSAC)
  
  return im1Reg, h


  def get_aligned_imagesCV(source):

  files = get_tiffiles(source)

  print ('Reference dapi is from:', files[0].split())
  processed_tif0 = tifffile.imread(files[0].split())
  print('Loaded processed_tif0', getsizeof(processed_tif0)/10**6, 'MB')
  dapi_target = np.array(processed_tif0[-1])
  print('Extracted dapi_target', getsizeof(dapi_target)/10**6, 'MB')
    
  #Do not need processed_tif0 only dapi_target from it
  del processed_tif0
  gc.collect()
  
  xmax, ymax = get_max_shape(source)

  for file in files:
    print('--- Aligning tif i:', file.split())
    processed_tif = tifffile.imread(file.split())
    print('Shape of image i is: ', np.shape(processed_tif), 'size', getsizeof(processed_tif)/10**6, 'MB')
    dapi_to_offset = np.array(processed_tif[-1])
    #delete processed_tif as it is not needed for registration (only need dapi) this is done to free memory.
    del processed_tif
    gc.collect()
    # Find homography
    h = alignImages(dapi_to_offset, dapi_target)

    #Reload processed_tif to align all the images with the Transform matrix using homography that we got from registration
    processed_tif = tifffile.imread(file.split())

    aligned_images = []
    for channel in range(np.shape(processed_tif)[0]):
      ## Might not need padding for this
      #max_processed_tif = pad_image(xmax, ymax, processed_tif[channel,:,:])
      #print('Done Recalibrating channel', channel)
      # Use homography
      aligned_images.append(cv2.warpPerspective(processed_tif[channel,:,:], h, (xmax, ymax))) #(width, height)
      print('channel', channel,'aligned')
      #del max_processed_tif
      #gc.collect()

    print('Transformed channels done, image is of size', np.shape(aligned_images), getsizeof(np.array(aligned_images))/10**6)
    

    del processed_tif
    gc.collect()

    print('Saving aligned image')
    with tifffile.TiffWriter('./aligned/'+file.split()[0].split('/')[2].split('.')[0]+'_al.tif',
                                 bigtiff = True) as tif:
      tif.save(align_tif)

    del align_tif
    gc.collect()

  print('DONE!')
  print('Transformed channels done, image is of size', np.shape(aligned_images))
  return np.array(aligned_images)