import aicspylibczi
import numpy as np
import os
import pathlib

import numpy as np
from skimage import data, io

from skimage.transform import warp_polar, rotate, rescale
from skimage.registration import phase_cross_correlation # new form of register_translation
from scipy.ndimage import shift
import glob
import gc
import sys
import tifffile
from sys import getsizeof # To know the size of the variables in bytes

from pystackreg import StackReg

from skimage.transform import ProjectiveTransform, SimilarityTransform
from skimage.measure import ransac
from skimage.feature import ORB, match_descriptors
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
  # http://www.gilgalad.co.uk/post/image-registration-skimage/
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

    orb = ORB(n_keypoints=50, fast_threshold=0.05)
    orb.detect_and_extract(max_dapi_target)
    keypoints1 = orb.keypoints
    descriptors1 = orb.descriptors

    orb.detect_and_extract(max_dapi_to_offset)
    keypoints2 = orb.keypoints
    descriptors2 = orb.descriptors
    print('orb done')

    matches12 = match_descriptors(descriptors1, descriptors2, cross_check=True)
    print('match done')


    # Select keypoints from the source (image to be registered)
    # and target (reference image)
    src = keypoints2[matches12[:, 1]][:, ::-1]
    dst = keypoints1[matches12[:, 0]][:, ::-1]
    print(dst)

    model_robust, inliers = ransac((src, dst), SimilarityTransform,
                               min_samples=10, residual_threshold=1, max_trials=300)
    print('ransac done')

    print(model_robust)
    output_shape = max_dapi_target.shape

    image2_ = warp(max_dapi_to_offset, model_robust.inverse, preserve_range=True,
                   output_shape=output_shape, cval=0)
    print('warp done')

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

    #image1_warp = image1_warp*10**2
    #print(image1_warp[2000:2100,2000:2100])
    #image1_warp = np.around(image1_warp)

    #image1_warp = np.array(image1_warp, dtype = int)
    #print(image1_warp[2000:2100,2000:2100])

    print('warp modified!', np.shape(image1_warp), getsizeof(np.array(image1_warp))/10**6)



    print('Saving aligned image',file.split()[0].split('/')[1])
    with tifffile.TiffWriter('./aligned/'+file.split()[0].split('/')[1].split('.')[0]+'_al.tif',
                                 bigtiff = True) as tif:
      tif.save(np.array(image1_warp))

  print('DONE!')

#import cv2 
def get_dapi_alignedOpenCV():
  print('DOING openCV!')
  source = 'output'

  files = get_tiffiles(source)

  print ('Reference dapi is from:', files[0].split()[0])
  #processed_tif0 = tifffile.imread(files[0].split())
  processed_tif0 = cv2.imread('output/dapi2.tif', cv2.IMREAD_ANYDEPTH)    # Reference image. 0 is for cv2.IMREAD_GRAYSCALE
  print('Loaded processed_tif0', getsizeof(processed_tif0)/10**6, 'MB', type(processed_tif0))
  dapi_target = np.array(processed_tif0)
  print('Extracted dapi_target', getsizeof(dapi_target)/10**6, 'MB')
    
  #Do not need processed_tif0 only dapi_target from it
  del processed_tif0
  gc.collect()
  
  xmax, ymax = get_max_shape(source)

  for file in files:
    print('--- Aligning tif i:', file.split())
    #processed_tif = tifffile.imread(file.split())
    processed_tif = cv2.imread(file.split()[0], cv2.IMREAD_ANYDEPTH )  # Image to be aligned. 0 is for cv2.IMREAD_GRAYSCALE CV_LOAD_IMAGE_ANYDEPTH
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
    # IMAGE 1 is to be MODIFIED

    # Convert to grayscale. 
    #img1 = cv2.cvtColor(img1_color, cv2.COLOR_BGR2GRAY) 
    #img2 = cv2.cvtColor(img2_color, cv2.COLOR_BGR2GRAY) 
    #height, width = img2.shape 
      
    # Create ORB detector with 5000 features. 
    orb_detector = cv2.ORB_create(500) 
      
    # Find keypoints and descriptors. 
    # The first arg is the image, second arg is the mask 
    #  (which is not reqiured in this case). 
    kp1, d1 = orb_detector.detectAndCompute(max_dapi_to_offset, None) 
    kp2, d2 = orb_detector.detectAndCompute(max_dapi_target, None) 
      
    # Match features between the two images. 
    # We create a Brute Force matcher with  
    # Hamming distance as measurement mode. 
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck = True) 
      
    # Match the two sets of descriptors. 
    matches = matcher.match(d1, d2) 
      
    # Sort matches on the basis of their Hamming distance. 
    matches.sort(key = lambda x: x.distance) 
      
    # Take the top 90 % matches forward. 
    matches = matches[:int(len(matches)*90)] 
    no_of_matches = len(matches) 
      
    # Define empty matrices of shape no_of_matches * 2. 
    p1 = np.zeros((no_of_matches, 2)) 
    p2 = np.zeros((no_of_matches, 2)) 
      
    for i in range(len(matches)): 
      p1[i, :] = kp1[matches[i].queryIdx].pt 
      p2[i, :] = kp2[matches[i].trainIdx].pt 
      
    # Find the homography matrix. 
    homography, mask = cv2.findHomography(p1, p2, cv2.RANSAC) 
    print(homography)
      
    # Use this matrix to transform the 
    # colored image wrt the reference image. 
    transformed_img = cv2.warpPerspective(max_dapi_to_offset, 
                        homography, (width, height)) 
      
    # Save the output. 
    #cv2.imwrite('output.jpg', transformed_img) 

    print('Saving aligned image',file.split()[0].split('/')[1])
    with tifffile.TiffWriter('./aligned/'+file.split()[0].split('/')[1].split('.')[0]+'_al.tif',
                                 bigtiff = True) as tif:
      tif.save(np.array(transformed_img))

  print('DONE!')

def get_aligned_imagesStackReg():

  source = 'output'
  files = get_tiffiles(source)

  print ('Reference dapi is from:', files[0].split())
  processed_tif0 = tifffile.imread(files[0].split())
  print('Loaded processed_tif0', getsizeof(processed_tif0)/10**6, 'MB')
  dapi_target = np.array(processed_tif0[-1])
  print('Extracted dapi_target', getsizeof(dapi_target)/10**6, 'MB')
  #input('CHECK RAM ---- tif0 and dapi loaded')
    
  #Do not need processed_tif0 only dapi_target from it
  del processed_tif0
  gc.collect()
  #input('CHECK RAM ---- tif0 deleted')

  xmax, ymax = get_max_shape(source)

  #input('CHECK RAM ---- 1 dapi deleted AND next step is phase_cross_correlation')
  subimage = False
  anti_alias = True
  rescale_fct = 0.25

  max_dapi_target = pad_image(xmax, ymax, dapi_target)
  max_dapi_target = rescale(max_dapi_target, rescale_fct, anti_aliasing=anti_alias)
  print('dai target padded and rescaled', getsizeof(np.array(max_dapi_target))/10**6, 'MB')

  del dapi_target
  gc.collect()

  for file in files:
    print('--- Aligning tif i:', file.split())
    processed_tif = tifffile.imread(file.split())
    print('Shape of image i is: ', np.shape(processed_tif), 'size', getsizeof(processed_tif)/10**6, 'MB')
    dapi_to_offset = np.array(processed_tif[-1])
    #input('CHECK RAM ---- tif and dapi loaded')
    #delete processed_tif as it is not needed for registration (only need dapi) this is done to free memory.
    del processed_tif
    gc.collect()
    #input('CHECK RAM ---- tif deleted')

    #shifted = get_shift(xmax, ymax, dapi_target, dapi_to_offset)
    ###################
    print('dapi_to_offset shape', np.shape(dapi_to_offset))

    print('Recalibrating image size to', xmax, ymax)
    #padding of dapi
    max_dapi_to_offset = pad_image(xmax, ymax, dapi_to_offset)
    print('DONE, padded dapi are of size',np.shape(max_dapi_to_offset), getsizeof(max_dapi_to_offset)/10**6)
    #input('CHECK RAM ---- dapiS padded')

    del dapi_to_offset
    gc.collect()
    max_dapi_to_offset = rescale(max_dapi_to_offset, rescale_fct, anti_aliasing=anti_alias)
    print('Down scaled the images to', np.shape(max_dapi_to_offset))

    print('Getting Transform matrix')

    sr = StackReg(StackReg.RIGID_BODY)
    if subimage:
      # register mov to ref sr.register(ref, mov)
      # Size of the sub image at the center. (25'000, 20'000) is 1GB size
      x_size = int(6000*rescale_fct/2)
      y_size = int(6000*rescale_fct/2)

      xhalf = int(np.floor(xmax*rescale_fct/2))
      yhalf = int(np.floor(ymax*rescale_fct/2))
      print('center of image', xhalf, yhalf)
      print('Taking sub image registration')
      sr.register(max_dapi_target[(xhalf-x_size):(xhalf+x_size), (yhalf-y_size):(yhalf+y_size)],
                  max_dapi_to_offset[(xhalf-x_size):(xhalf+x_size), (yhalf-y_size):(yhalf+y_size)])
    else:
      print('Taking full image registration')
      sr.register(max_dapi_target, max_dapi_to_offset)

    print('Image registration done')

    del max_dapi_to_offset
    gc.collect()
    #input('CHECK RAM ---- padded dapiS deleted')
    ######################

    #Reload processed_tif to align all the images with the shift that we got from registration
    processed_tif = tifffile.imread(file.split())
    ######################
    aligned_images = []
    channels = np.shape(processed_tif)[0]
    for channel in range(channels):
      max_processed_tif = pad_image(xmax, ymax, processed_tif[0,:,:])
      max_processed_tif = rescale(max_processed_tif, rescale_fct, anti_aliasing=anti_alias)
      #input('CHECK RAM ---- padded channel')
      print('Shape of processed_tif', np.shape(processed_tif))
      #To free memory as we do not need these channels
      if np.shape(processed_tif)[0] > 1: 
        processed_tif = np.delete(processed_tif, 0, axis = 0)
        print('Shape of processed_tif after delete', np.shape(processed_tif))

      #input('CHECK RAM ---- tif channel deleted as it is padded')
      print('Done Recalibrating channel', channel)
      aligned_images.append(sr.transform(max_processed_tif))
      print('channel', channel,'aligned. Aligned images is of size', np.shape(np.array(aligned_images)))
      #input('CHECK RAM ---- shifted image given')
      del max_processed_tif
      gc.collect()
      #input('CHECK RAM ---- max_processed_tif variable deleted and Start again')

    print('Transformed channels done, image is of size', np.shape(aligned_images), getsizeof(np.array(aligned_images))/10**6)
    ######################

    del processed_tif
    gc.collect()
    #input('CHECK RAM ---- processed_tif deleted (what is left of it)')

    print('Saving aligned image')
    with tifffile.TiffWriter('./aligned/'+file.split()[0].split('/')[1].split('.')[0]+'_al.tif',
                                 bigtiff = True) as tif:
      #tif.save(align_tif)
      tif.save(np.array(aligned_images))
    #input('CHECK RAM ---- aligned_images saved')

    del aligned_images
    gc.collect()
    #input('CHECK RAM ---- aligned_images deleted')

  print('DONE!')


get_aligned_imagesStackReg()