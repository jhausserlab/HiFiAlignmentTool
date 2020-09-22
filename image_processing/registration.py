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

from guppy import hpy

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

def get_aligned_images(source):

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

    shifted = get_shift(xmax, ymax, dapi_target, dapi_to_offset)

    #Reload processed_tif to align all the images with the shift that we got from registration
    processed_tif = tifffile.imread(file.split())
    align_tif = align_images(xmax, ymax, shifted, processed_tif)

    del processed_tif
    gc.collect()

    print('Saving aligned image')
    with tifffile.TiffWriter('./aligned/'+file.split()[0].split('/')[2].split('.')[0]+'_al.tif',
                                 bigtiff = True) as tif:
      tif.save(align_tif)

    del align_tif
    gc.collect()

  print('DONE!')


def align_images(xmax, ymax, shifted, processed_tif):

  aligned_images = []

  for channel in range(np.shape(processed_tif)[0]):
    max_processed_tif = pad_image(xmax, ymax, processed_tif[channel,:,:])
    print('Done Recalibrating channel', channel)
    aligned_images.append(shift(max_processed_tif, shift=(shifted[0], shifted[1]), mode='constant'))
    print('channel', channel,'aligned')
    del max_processed_tif
    gc.collect()

  print('Transformed channels done, image is of size', np.shape(aligned_images), getsizeof(np.array(aligned_images))/10**6)
  return np.array(aligned_images)

def get_shift(xmax, ymax, dapi_target, dapi_to_offset):
  print('dapi_target shape', np.shape(dapi_target))
  print('dapi_to_offset shape', np.shape(dapi_to_offset))


  print('Recalibrating image size to', xmax, ymax)
  max_dapi_target = pad_image(xmax, ymax, dapi_target)
  print('DONE, for dapi target (size in MB)', getsizeof(max_dapi_target)/10**6)
  #padding of dapi_to_offset
  max_dapi_to_offset = pad_image(xmax, ymax, dapi_to_offset)
  print('DONE, for dapi offset')

  del dapi_target
  del dapi_to_offset
  gc.collect()

  print('Getting Transform matrix')
  xhalf = int(np.floor(xmax/2))
  yhalf = int(np.floor(ymax/2))
  print('Slicing image', xhalf, yhalf)

  shifted, error, diffphase = phase_cross_correlation(max_dapi_target[:xhalf,:yhalf], max_dapi_to_offset[:xhalf,:yhalf])
  print(f"Detected subpixel offset UP LEFT(y, x): {shifted}")
  #shifted, error, diffphase = phase_cross_correlation(max_dapi_target[xhalf:,:yhalf], max_dapi_to_offset[xhalf:,:yhalf])
  #print(f"Detected subpixel offset DOWN LEFT(y, x): {shifted}")
  #shifted, error, diffphase = phase_cross_correlation(max_dapi_target[:xhalf,yhalf:], max_dapi_to_offset[:xhalf,yhalf:])
  #print(f"Detected subpixel offset UP RIGHT(y, x): {shifted}")
  #shifted, error, diffphase = phase_cross_correlation(max_dapi_target[xhalf:,yhalf:], max_dapi_to_offset[xhalf:,yhalf:])
  #print(f"Detected subpixel offset DOWN RIGHT(y, x): {shifted}")

  #Full image alignment
  #shifted, error, diffphase = phase_cross_correlation(max_dapi_target, max_dapi_to_offset)
  #print(f"Detected subpixel offset Original (y, x): {shifted}")


  del max_dapi_target
  del max_dapi_to_offset
  gc.collect()

  return shifted