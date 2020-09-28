import aicspylibczi
import napari
import numpy as np
import os
import pathlib
import tifffile
import time
from datetime import timezone, datetime, timedelta
from image_processing.subtract_background import subtract_background
import gc

import numpy as np
from skimage import data, io

from skimage.transform import warp_polar, rotate, rescale
from skimage.registration import phase_cross_correlation # new form of register_translation
from scipy.ndimage import shift
import napari
import glob
import gc
import sys
import tifffile
from sys import getsizeof # To know the size of the variables in bytes


from skimage.transform import ProjectiveTransform, SimilarityTransform
from skimage.measure import ransac
from skimage.feature import plot_matches
from skimage.feature import ORB, match_descriptors, plot_matches
from skimage.transform import warp
from skimage.registration import optical_flow_tvl1


def get_dapi():
  tif2 = tifffile.imread('./r22_pr.tif')
  tif5 = tifffile.imread('./r25_pr.tif')

  dapi2 = np.array(tif2[-1])
  dapi5 = np.array(tif5[-1])

  with tifffile.TiffWriter('./dapi2.tif',
                                 bigtiff = True) as tif:
      tif.save(dapi2)

  with tifffile.TiffWriter('./dapi5.tif',
                                 bigtiff = True) as tif:
      tif.save(dapi5)

  return print('HAHA')


def get_tiffiles(source):
  return glob.glob(source + '/**/*.tif', recursive=True)

def get_max_shape(source):
  
  filepath = glob.glob(source + '/**/*.txt', recursive=True)
  print ('Getting max dimensions with: ',filepath)
  file = open(filepath[0],'r')
  images_shape = file.read()
  split = images_shape.split(';')
  xmax = 0
  ymax = 0
  print(split)
  for i in range(len(split)-1):
     frag = split[i].split(',')
     xmax = max(xmax,int(frag[1]))
     ymax = max(ymax,int(frag[2]))
  print('(Xmax, Ymax) --------------- ',xmax,ymax)
        
  return xmax,ymax

def pad_image(xmax, ymax, image):
  #image must be of dimension X,Y so we input channels not the whole image C,X,Y
  x_diff = xmax - np.shape(image)[0]
  y_diff = ymax - np.shape(image)[1]

  #pads (up, down),(left,right)
  padded_image = np.pad(image,((int(np.floor((x_diff)/2)), int(np.ceil((x_diff)/2)))
                              ,(int(np.floor((y_diff)/2)), int(np.ceil((y_diff)/2)))),'constant')
  return padded_image


def get_dapi_alignedORB():
  print('DOING ORB!')
  source = 'output'

  files = get_tiffiles(source)

  print ('Reference dapi is from:', files[0].split())
  processed_tif0 = tifffile.imread(files[0].split())
  print('Loaded processed_tif0', getsizeof(processed_tif0)/10**6, 'MB')
  dapi_target = np.array(processed_tif0)
  print('Extracted dapi_target', getsizeof(dapi_target)/10**6, 'MB')
    
  #Do not need processed_tif0 only dapi_target from it
  del processed_tif0
  gc.collect()
  
  xmax, ymax = get_max_shape(source)

  for file in files:
    print('--- Aligning tif i:', file.split())
    processed_tif = tifffile.imread(file.split())
    print('Shape of image i is: ', np.shape(processed_tif), 'size', getsizeof(processed_tif)/10**6, 'MB')
    dapi_to_offset = np.array(processed_tif)
    #delete processed_tif as it is not needed for registration (only need dapi) this is done to free memory.
    del processed_tif
    gc.collect()

    #shifted = get_shift(xmax, ymax, dapi_target, dapi_to_offset)
    ###################
    print('dapi_target shape', np.shape(dapi_target))
    print('dapi_to_offset shape', np.shape(dapi_to_offset))

    print('Recalibrating image size to', xmax, ymax)
    #padding of dapi
    max_dapi_target = pad_image(xmax, ymax, dapi_target)
    max_dapi_to_offset = pad_image(xmax, ymax, dapi_to_offset)
    print('DONE, padded dapiS are of size', getsizeof(max_dapi_target)/10**6)

    del dapi_to_offset
    gc.collect()

    print('Getting Transform matrix')
    ########################################################################################
    ########################################################################################
    # Size of the sub image at the center. (25'000, 20'000) is 1GB size
    #image1 original image2 the one to register

    orb = ORB(n_keypoints=500, fast_threshold=0.05)
    orb.detect_and_extract(max_dapi_target)
    keypoints1 = orb.keypoints
    descriptors1 = orb.descriptors

    orb.detect_and_extract(max_dapi_to_offset)
    keypoints2 = orb.keypoints
    descriptors2 = orb.descriptors

    matches12 = match_descriptors(descriptors1, descriptors2, cross_check=True)


    # Select keypoints from the source (image to be registered)
    # and target (reference image)
    src = keypoints2[matches12[:, 1]][:, ::-1]
    dst = keypoints1[matches12[:, 0]][:, ::-1]

    model_robust, inliers = ransac((src, dst), SimilarityTransform,
                               min_samples=10, residual_threshold=1, max_trials=300)


    image1_ = max_dapi_target
    output_shape = max_dapi_target.shape

    image2_ = warp(max_dapi_to_offset, model_robust.inverse, preserve_range=True,
                   output_shape=output_shape, cval=0)

    image2_ = np.ma.array(image2_, mask=image2_==-1)



    print('Saving aligned image',file.split()[0].split('/')[1])
    with tifffile.TiffWriter('./aligned/'+file.split()[0].split('/')[1].split('.')[0]+'_al.tif',
                                 bigtiff = True) as tif:
      tif.save(np.array(image2_))

  print('DONE!')


def get_dapi_alignedPCC():
  print('DOING PCC!')
  source = 'output'

  files = get_tiffiles(source)

  print ('Reference dapi is from:', files[0].split())
  processed_tif0 = tifffile.imread(files[0].split())
  print('Loaded processed_tif0', getsizeof(processed_tif0)/10**6, 'MB')
  dapi_target = np.array(processed_tif0)
  print('Extracted dapi_target', getsizeof(dapi_target)/10**6, 'MB')
    
  #Do not need processed_tif0 only dapi_target from it
  del processed_tif0
  gc.collect()
  
  xmax, ymax = get_max_shape(source)

  for file in files:
    print('--- Aligning tif i:', file.split())
    processed_tif = tifffile.imread(file.split())
    print('Shape of image i is: ', np.shape(processed_tif), 'size', getsizeof(processed_tif)/10**6, 'MB')
    dapi_to_offset = np.array(processed_tif)
    #delete processed_tif as it is not needed for registration (only need dapi) this is done to free memory.
    del processed_tif
    gc.collect()

    #shifted = get_shift(xmax, ymax, dapi_target, dapi_to_offset)
    ###################
    print('dapi_target shape', np.shape(dapi_target))
    print('dapi_to_offset shape', np.shape(dapi_to_offset))

    print('Recalibrating image size to', xmax, ymax)
    #padding of dapi
    max_dapi_target = pad_image(xmax, ymax, dapi_target)
    max_dapi_to_offset = pad_image(xmax, ymax, dapi_to_offset)
    print('DONE, padded dapiS are of size', getsizeof(max_dapi_target)/10**6)

    del dapi_to_offset
    gc.collect()

    print('Getting Transform matrix')
    # Size of the sub image at the center. (25'000, 20'000) is 1GB size
    x_size = int(3000/2)
    y_size = int(2000/2)

    xhalf = int(np.floor(xmax/2))
    yhalf = int(np.floor(ymax/2))
    print('center of image', xhalf, yhalf)

    shifted, error, diffphase = phase_cross_correlation(max_dapi_target[(xhalf-x_size):(xhalf+x_size), (yhalf-y_size):(yhalf+y_size)],
                                                     max_dapi_to_offset[(xhalf-x_size):(xhalf+x_size), (yhalf-y_size):(yhalf+y_size)])
    print(f"Detected subpixel offset (y, x): {shifted}")

    aligned_dapi = shift(max_dapi_to_offset, shift=(shifted[0], shifted[1]), mode='constant')

    image_polar = warp_polar(max_dapi_target[(xhalf-x_size):(xhalf+x_size), (yhalf-y_size):(yhalf+y_size)], radius=xmax, multichannel=False)
    rotated_polar = warp_polar(aligned_dapi[(xhalf-x_size):(xhalf+x_size), (yhalf-y_size):(yhalf+y_size)], radius=xmax, multichannel=False)

    shifts, error, phasediff = phase_cross_correlation(image_polar, rotated_polar)

    print(shifts[0])
    rotated_dapi = rotate(aligned_dapi, -shifts[0]/2) # the - makes sense but /2 nope.

    print('Saving aligned image',file.split()[0].split('/')[1])
    with tifffile.TiffWriter('./aligned/'+file.split()[0].split('/')[1].split('.')[0]+'_al.tif',
                                 bigtiff = True) as tif:
      tif.save(np.array(rotated_dapi))

  print('DONE!')





def get_dapi_alignedOF():
  print('DOING Opitcal flow!')
  source = 'output'

  files = get_tiffiles(source)

  print ('Reference dapi is from:', files[0].split())
  processed_tif0 = tifffile.imread(files[0].split())
  print('Loaded processed_tif0', getsizeof(processed_tif0)/10**6, 'MB')
  dapi_target = np.array(processed_tif0)
  print('Extracted dapi_target', getsizeof(dapi_target)/10**6, 'MB')
    
  #Do not need processed_tif0 only dapi_target from it
  del processed_tif0
  gc.collect()
  
  xmax, ymax = get_max_shape(source)

  for file in files:
    print('--- Aligning tif i:', file.split())
    processed_tif = tifffile.imread(file.split())
    print('Shape of image i is: ', np.shape(processed_tif), 'size', getsizeof(processed_tif)/10**6, 'MB')
    dapi_to_offset = np.array(processed_tif)
    #delete processed_tif as it is not needed for registration (only need dapi) this is done to free memory.
    del processed_tif
    gc.collect()

    #shifted = get_shift(xmax, ymax, dapi_target, dapi_to_offset)
    ###################
    print('dapi_target shape', np.shape(dapi_target))
    print('dapi_to_offset shape', np.shape(dapi_to_offset))
    print('dapi size is', getsizeof(dapi_target)/10**6)

    print('Recalibrating image size to', xmax, ymax)
    #padding of dapi
    max_dapi_target = pad_image(xmax, ymax, dapi_target)
    max_dapi_to_offset = pad_image(xmax, ymax, dapi_to_offset)
    print('DONE, padded dapiS are of size', getsizeof(max_dapi_target)/10**6)

    del dapi_to_offset
    gc.collect()

    print('Getting Transform matrix')

        # --- Compute the optical flow image0 is reference
    v, u = optical_flow_tvl1(max_dapi_target, max_dapi_to_offset)
    print('optical flow done!', np.shape(v), np.shape(u), getsizeof(np.array(v))/10**6)

    # --- Use the estimated optical flow for registration

    nr, nc = max_dapi_target.shape

    row_coords, col_coords = np.meshgrid(np.arange(nr), np.arange(nc),
                                         indexing='ij')
    print('mesh grid done!', np.shape(row_coords), np.shape(col_coords), getsizeof(np.array(row_coords))/10**6)

    image1_warp = warp(max_dapi_to_offset, np.array([row_coords + v, col_coords + u]),
                       mode='nearest')
    print('warp done!', np.shape(image1_warp), getsizeof(np.array(image1_warp))/10**6)

    image1_warp = image1_warp*10**2
    print(image1_warp[2000:2100,2000:2100])
    image1_warp = np.around(image1_warp)

    image1_warp = image1_warp.astype(int)
    print(image1_warp[2000:2100,2000:2100])

    print('warp modified!', np.shape(image1_warp), getsizeof(np.array(image1_warp))/10**6)



    print('Saving aligned image',file.split()[0].split('/')[1])
    with tifffile.TiffWriter('./aligned/'+file.split()[0].split('/')[1].split('.')[0]+'_al.tif',
                                 bigtiff = True) as tif:
      tif.save(np.array(image1_warp))

  print('DONE!')


get_dapi_alignedOF()
