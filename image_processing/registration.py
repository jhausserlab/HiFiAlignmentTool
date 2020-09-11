import numpy as np
from skimage import data, io
from skimage.registration import phase_cross_correlation # new form of register_translation
from scipy.ndimage import shift
import napari
import glob
import gc
import sys
import tifffile

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

def pad_images(xmax, ymax, image):
  #image must be of dimension X,Y so we input channels not the whole image C,X,Y
  x_diff = xmax - np.shape(image)[0]
  y_diff = ymax - np.shape(image)[1]

  padded_image = np.pad(image,((int(np.floor((x_diff)/2)), int(np.ceil((x_diff)/2)))
                              ,(int(np.floor((y_diff)/2)), int(np.ceil((y_diff)/2)))),'constant')
  return padded_image


def align_images(source, dapi_target, processed_tif):

  aligned_images = []

  dapi_to_offset = processed_tif[-1]
  print('dapi_target shape', np.shape(dapi_target))
  print('dapi_to_offset shape', np.shape(dapi_to_offset))
  
  xmax, ymax = get_max_shape(source)
  print('Recalibrating image size to', xmax, ymax)
  max_dapi_target = pad_images(xmax, ymax, dapi_target)

  #padding of dapi_to_offset, calling it max_processed_tif to keep variables low
  max_processed_tif = pad_images(xmax, ymax, dapi_to_offset)

  shifted, error, diffphase = phase_cross_correlation(max_dapi_target, max_processed_tif)
  print(f"Detected subpixel offset (y, x): {shifted}")

  for channel in range(np.shape(processed_tif)[0]):
    max_processed_tif = pad_images(xmax, ymax, processed_tif[channel,:,:])
    aligned_images.append(shift(max_processed_tif, shift=(shifted[0], shifted[1]), mode='constant'))
        
  print('transformed channels done, image is of size', np.shape(aligned_images))
  return np.array(aligned_images)

def get_aligned_images(source):
  # source needs to be a str of where are the tif stored
  files = get_tiffiles(source)

  print ('Reference dapi is from:', files[0].split())
  processed_tif0 = tifffile.imread(files[0].split())
  dapi_target = processed_tif0[-1]
    
  #save_reference(source, files[0].split(), processed_tif0)
  #Do not need processed_tif0 only dapi_target from it
  del processed_tif0
  gc.collect()
    
  #for file in files[1:]:
  for file in files:
    print('--- Aligning tif i:', file.split())
    processed_tif = tifffile.imread(file.split())
    print('Shape of image i is: ', np.shape(processed_tif))
    align_tif = align_images(source, dapi_target, processed_tif)

    del processed_tif
    gc.collect()
    
    print('Saving aligned image')
    with tifffile.TiffWriter('./aligned/'+file.split()[0].split('/')[2].split('.')[0]+'_align.tif',
                                 bigtiff = True) as tif:
      tif.save(align_tif)

    del align_tif
    gc.collect()

  print('DONE!')







