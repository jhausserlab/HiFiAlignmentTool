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

def get_tiffiles(source):
  return sorted(glob.glob(source + '/**/*.tif', recursive=True))

def final_image(source):
  files = get_tiffiles(source)
  tif = tifffile.imread(files[0].split())

  final_image = tif
  print('Adding first image:', files[0].split() ,np.shape(final_image))

  for idx in range(len(files)-1):
    print('--- Adding:', files[idx+1].split())
    tif = tifffile.imread(files[idx+1].split())
    print('Tif shape', np.shape(tif))
    #idx != 0 because we want to the first dapi channel from our reference image and then remove all the other dapis.
    tif = np.delete(tif, 0, 0)
    print('Removed alignment channel', np.shape(tif))

    final_image = np.append(final_image, tif, axis = 0)
    print(np.shape(final_image))
    print('Image size: ', getsizeof(np.array(final_image))/10**6, 'MB')

  print('Final image size: ',np.shape(final_image), getsizeof(np.array(final_image))/10**6, 'MB')
  print('Saving aligned image')
  with tifffile.TiffWriter('./final_image.ome.tif', bigtiff = True) as tif:
    tif.save(np.array(final_image))
  print('Final image saved!')

def show(args, images):
  if not args.yes:
    with napari.gui_qt():
      viewer = napari.Viewer()
      for czi in images:
        viewer.add_image(np.array(czi))

##### The functions below are not needed anymore, functions v1 and v2 were implemented in registration. They are now outdated
### V1 has the subimage possibility and v0 is when i used phase_cross_correlation function for image registration
from skimage.registration import phase_cross_correlation # new form of register_translation
from scipy.ndimage import shift

def get_aligned_images_V1(args, source):

  files = get_tiffiles(source)

  print ('Reference dapi is from:', files[0].split())
  tif_ref = tifffile.imread(files[0].split())
  print('Loaded tif_ref', getsizeof(tif_ref)/10**6, 'MB')
  dapi_ref = np.array(tif_ref[-1])
  print('Extracted dapi_ref', getsizeof(dapi_ref)/10**6, 'MB')
    
  #Do not need tif_ref only dapi_ref from it
  del tif_ref
  gc.collect()
  
  i_max, j_max = get_max_shape(source)

  anti_alias = True
  rescale_fct = 0.25

  pad_dapi_ref = pad_image(i_max, j_max, dapi_ref)
  pad_dapi_ref = rescale(pad_dapi_ref, rescale_fct, anti_aliasing=anti_alias)
  print('dapi_ref padded and rescaled', getsizeof(np.array(pad_dapi_ref))/10**6, 'MB')

  del dapi_ref
  gc.collect()

  for file in files:

    print('--- Aligning tif i:', file.split())
    tif_mov = tifffile.imread(file.split())
    print('Shape of image i is: ', np.shape(tif_mov), 'size', getsizeof(tif_mov)/10**6, 'MB')
    dapi_mov = np.array(tif_mov[-1])
    #delete tif_mov as it is not needed for registration (only need dapi) this is done to free memory.
    del tif_mov
    gc.collect()

    print('dapi_mov shape', np.shape(dapi_mov))

    print('Padding image size to', i_max, j_max)
    #padding of dapi
    pad_dapi_mov = pad_image(i_max, j_max, dapi_mov)
    print('pad_dapi_mov is of size',np.shape(pad_dapi_mov), getsizeof(pad_dapi_mov)/10**6)
    del dapi_mov
    gc.collect()

    pad_dapi_mov = rescale(pad_dapi_mov, rescale_fct, anti_aliasing=anti_alias)
    print('Down scaled the image to', np.shape(pad_dapi_mov))

    print('Getting Transform matrix')

    sr = StackReg(StackReg.RIGID_BODY)
    """
    #The code didn't seem to work to register subimages. Better to register the image as a whole
    #Keeping the code in case we still want to try
    subimage = False
    i_size = int(6000*rescale_fct/2)
    j_size = int(6000*rescale_fct/2)
    if subimage:
      # register mov to ref sr.register(ref, mov)
      # Size of the sub image at the center. (25'000, 20'000) is 1GB size

      ihalf = int(np.floor(i_max*rescale_fct/2))
      jhalf = int(np.floor(j_max*rescale_fct/2))
      print('center of image', ihalf, jhalf)
      print('Taking sub image registration')
      sr.register(pad_dapi_ref[(ihalf-i_size):(ihalf+i_size), (jhalf-j_size):(jhalf+j_size)],
                  pad_dapi_mov[(ihalf-i_size):(ihalf+i_size), (jhalf-j_size):(jhalf+j_size)])
    else:
      print('Taking full image registration')
      sr.register(pad_dapi_ref, pad_dapi_mov)
    """
    
    sr.register(pad_dapi_ref, pad_dapi_mov)
    print('Registration matrix acquired and now transforming the channels')

    del pad_dapi_mov
    gc.collect()

    #Reload tif_mov to align all the images with the shift that we got from registration
    tif_mov = tifffile.imread(file.split())
    ######################
    aligned_images = []
    channels = np.shape(tif_mov)[0]
    for channel in range(channels):
      pad_tif_mov = pad_image(i_max, j_max, tif_mov[0,:,:])
      pad_tif_mov = rescale(pad_tif_mov, rescale_fct, anti_aliasing=anti_alias)
      #To free memory as we do not need these channels
      if np.shape(tif_mov)[0] > 1: 
        tif_mov = np.delete(tif_mov, 0, axis = 0)

      aligned_images.append(sr.transform(pad_tif_mov))
      print('info -- channel', channel,'aligned')
      del pad_tif_mov
      gc.collect()

    print('Transformed channels done, image is of size', np.shape(aligned_images), 
                                  getsizeof(np.array(aligned_images))/10**6, 'MB')

    del tif_mov
    gc.collect()

    print('Saving aligned image')
    with tifffile.TiffWriter('./aligned/'+file.split()[0].split('/')[2].split('.')[0]+'_al.tif',
                                 bigtiff = True) as tif:
      tif.save(np.array(aligned_images))

    del aligned_images
    gc.collect()

  print('DONE! All images are registered')

def get_aligned_images_V0(args, source):

  files = get_tiffiles(source)

  print ('Reference dapi is from:', files[0].split())
  tif_ref = tifffile.imread(files[0].split())
  print('Loaded tif_ref', getsizeof(tif_ref)/10**6, 'MB')
  dapi_ref = np.array(tif_ref[-1])
  print('Extracted dapi_ref', getsizeof(dapi_ref)/10**6, 'MB')
    
  #Do not need tif_ref only dapi_ref from it
  del tif_ref
  gc.collect()
  
  i_max, j_max = get_max_shape(source)

  for file in files:
    print('--- Aligning tif i:', file.split())
    tif_mov = tifffile.imread(file.split())
    print('Shape of image i is: ', np.shape(tif_mov), 'size', getsizeof(tif_mov)/10**6, 'MB')
    dapi_mov = np.array(tif_mov[-1])
    #delete tif_mov as it is not needed for registration (only need dapi) this is done to free memory.
    del tif_mov
    gc.collect()

    print('dapi_ref shape', np.shape(dapi_ref))
    print('dapi_mov shape', np.shape(dapi_mov))

    print('Padding image size to', i_max, j_max)
    #padding of dapi
    pad_dapi_ref = pad_image(i_max, j_max, dapi_ref)
    pad_dapi_mov = pad_image(i_max, j_max, dapi_mov)
    print('Padded dapis are of size', getsizeof(pad_dapi_ref)/10**6)

    del dapi_mov
    gc.collect()

    print('Getting Transform matrix')
    i_size = int(3000/2)
    j_size = int(2000/2)

    ihalf = int(np.floor(i_max/2))
    jhalf = int(np.floor(j_max/2))
    print('center of image', ihalf, jhalf)

    shifted, error, diffphase = phase_cross_correlation(pad_dapi_ref[(ihalf-i_size):(ihalf+i_size), (jhalf-j_size):(jhalf+j_size)],
                                                     pad_dapi_mov[(ihalf-i_size):(ihalf+i_size), (jhalf-j_size):(jhalf+j_size)])
    print(f"Detected subpixel offset (y, x): {shifted}")

    del pad_dapi_ref
    del pad_dapi_mov
    gc.collect()

    #Reload tif_mov to align all the images with the shift that we got from registration
    tif_mov = tifffile.imread(file.split())

    aligned_images = []
    channels = np.shape(tif_mov)[0]
    for channel in range(channels):
      pad_tif_mov = pad_image(i_max, j_max, tif_mov[0,:,:])
      #To free memory as we do not need these channels
      if np.shape(tif_mov)[0] > 1: 
        tif_mov = np.delete(tif_mov, 0, axis = 0)

      print('Done padding channel', channel,'. Now doing registration')
      aligned_images.append(shift(pad_tif_mov, shift=(shifted[0], shifted[1]), mode='constant'))
      print('info -- channel', channel,'aligned')
      del pad_tif_mov
      gc.collect()

    print('Transformed channels done, image is of size', np.shape(aligned_images), getsizeof(np.array(aligned_images))/10**6)

    del tif_mov
    gc.collect()

    print('Saving aligned image')
    with tifffile.TiffWriter('./aligned/'+file.split()[0].split('/')[2].split('.')[0]+'_al.tif',
                                 bigtiff = True) as tif:
      tif.save(np.array(aligned_images))

    del aligned_images
    gc.collect()

  print('DONE! All images are registered')

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

#  her i tried to implement different registration processes 
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


