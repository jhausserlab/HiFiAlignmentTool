import numpy as np
from skimage.transform import rescale
from pystackreg import StackReg
import glob
import gc
import sys
import tifffile
from sys import getsizeof # To know the size of the variables in bytes

def get_tiffiles(source):
  return glob.glob(source + '/**/*.tif', recursive=True)

def get_max_shape(source):
  
  filepath = glob.glob(source + '/**/*.txt', recursive=True)
  print ('Getting max dimensions with: ',filepath)
  file = open(filepath[0],'r')
  images_shape = file.read()
  split = images_shape.split(';')
  i_max = 0
  j_max = 0
  print(split)
  for i in range(len(split)-1):
     frag = split[i].split(',')
     i_max = max(i_max,int(frag[1]))
     j_max = max(j_max,int(frag[2]))
  print('(i_max, j_max) --------------- ',i_max,j_max)
        
  return i_max,j_max

def pad_image(i_max, j_max, image):
  #image must be of dimension X,Y so we input channels not the whole image C,X,Y
  i_diff = i_max - np.shape(image)[0]
  j_diff = j_max - np.shape(image)[1]

  #pads (up, down),(left,right)
  padded_image = np.pad(image,((int(np.floor((i_diff)/2)), int(np.ceil((i_diff)/2)))
                              ,(int(np.floor((j_diff)/2)), int(np.ceil((j_diff)/2)))),'constant')
  return padded_image

def get_aligned_images(source):

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
  subimage = False
  i_size = int(6000*rescale_fct/2)
  j_size = int(6000*rescale_fct/2)

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

##### The functions below are not needed anymore
from skimage.registration import phase_cross_correlation # new form of register_translation
from scipy.ndimage import shift
def get_aligned_images_V0(source):

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

def align_images(i_max, j_max, shifted, tif_mov):

  aligned_images = []

  for channel in range(np.shape(tif_mov)[0]):
    pad_tif_mov = pad_image(i_max, j_max, tif_mov[channel,:,:])
    print('Done Recalibrating channel', channel)
    aligned_images.append(shift(pad_tif_mov, shift=(shifted[0], shifted[1]), mode='constant'))
    print('channel', channel,'aligned')
    del pad_tif_mov
    gc.collect()

  print('Transformed channels done, image is of size', np.shape(aligned_images), getsizeof(np.array(aligned_images))/10**6)
  return np.array(aligned_images)

def get_shift(i_max, j_max, dapi_ref, dapi_mov):
  print('dapi_ref shape', np.shape(dapi_ref))
  print('dapi_mov shape', np.shape(dapi_mov))


  print('Recalibrating image size to', i_max, j_max)
  pad_dapi_ref = pad_image(i_max, j_max, dapi_ref)
  print('DONE, for dapi target (size in MB)', getsizeof(pad_dapi_ref)/10**6)
  #padding of dapi_mov
  pad_dapi_mov = pad_image(i_max, j_max, dapi_mov)
  print('DONE, for dapi offset')

  del dapi_ref
  del dapi_mov
  gc.collect()

  print('Getting Transform matrix')
  # Size of the sub image at the center. (25'000, 20'000) is 1GB size
  i_size = int(3000/2)
  j_size = int(2000/2)

  ihalf = int(np.floor(i_max/2))
  jhalf = int(np.floor(j_max/2))
  print('center of image', ihalf, jhalf)

  shifted, error, diffphase = phase_cross_correlation(pad_dapi_ref[(ihalf-i_size):(ihalf+i_size), (jhalf-j_size):(jhalf+j_size)],
                                                   pad_dapi_mov[(ihalf-i_size):(ihalf+i_size), (jhalf-j_size):(jhalf+j_size)])
  print(f"Detected subpixel offset (y, x): {shifted}")

  #Full image alignment
  #shifted, error, diffphase = phase_cross_correlation(pad_dapi_ref, pad_dapi_mov)
  #print(f"Detected subpixel offset Original (y, x): {shifted}")

  del pad_dapi_ref
  del pad_dapi_mov
  gc.collect()

  return shifte