import numpy as np
from skimage.transform import rescale
from pystackreg import StackReg
import glob
import gc
import sys
import tifffile
from sys import getsizeof

import pandas as pd

def get_filename():
  data_strct = pd.read_csv("channel_name.csv")
  file_name = []
  for i in range(data_strct.shape[0]):
    file_name.append(data_strct['Filename'][i])

  return file_name

def get_tiffiles(source):
    data_strct = pd.read_csv("channel_name.csv")
    file_name = []
    for i in range(data_strct.shape[0]):
      filepath = glob.glob(source+'/'+data_strct['Filename'][i]+'*.tif', recursive=True)[0]
      file_name.append(filepath.split('/')[2])

    return file_name

def get_aligned_marker_names(ref):
  data = pd.read_csv("channel_name.csv")
  #create a list of the channel names. in the order that they were saved as in CZI
  chan_name = []
  #i is image
  for i in range(data.shape[0]):
    #j is channel
    for j in range(data.shape[1]-1):
      if(str(data[data.columns[j+1]][i]) != 'nan'):
        chan_name.append(data[data.columns[j+1]][i] +'_'+ data.columns[j+1] +'_'+ data['Filename'][i])

  #Modify the list to put the reference channel as the first channel of each image
  img = chan_name[0].split('_')[2]
  img_idx = 0
  for i in range(len(chan_name)):
    if chan_name[i].split('_')[2] == img:
      if (chan_name[i].split('_')[1] == ref):  
        chan_name.insert(i-img_idx, chan_name.pop(i))
      img_idx += 1
    else:
      img_idx = 1
      img = chan_name[i].split('_')[2]
  
  file_name = open("./aligned/marker_names_al.txt","w")
  for i in range(len(chan_name)):
    file_name.write(chan_name[i]+'\n')
  file_name.close()

def get_final_marker_names(ref):
  file_al = open("./aligned/marker_names_al.txt","r")
  data = pd.read_csv("channel_name.csv")
  marker_al = file_al.readlines()
  marker_names_final = []
  for i in marker_al:
      marker_names_final.append(i)
  file_al.close()

  for i in range(len(marker_names_final)-data.shape[0]):
    if (marker_names_final[i].split('_')[1] == ref):
      if i != 0:
        print('Removed reference channel', i,'called', marker_names_final[i])
        marker_names_final.pop(i)
  print(len(marker_names_final))

  file_name = open("marker_names_final.txt","w")
  for i in range(len(marker_names_final)):
    file_name.write(marker_names_final[i])
  file_name.close()
  print('-------------- marker_names_final.txt saved')

def get_max_shape(source):
  #this function gets the maximum dimensions from all the images that are going to be registered
  filepath = glob.glob(source + '/**/image_shape.txt', recursive=True)
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
  #pads the images if the dimensions are not the same for all of them
  #image must be of dimension X,Y so we input channels not the whole image C,X,Y
  i_diff = i_max - np.shape(image)[0]
  j_diff = j_max - np.shape(image)[1]

  #pads (up, down),(left,right)
  padded_image = np.pad(image,((int(np.floor((i_diff)/2)), int(np.ceil((i_diff)/2)))
                              ,(int(np.floor((j_diff)/2)), int(np.ceil((j_diff)/2)))),'constant')
  return padded_image

def get_aligned_images(args, source):
  #function used to do registration on all images with respect to the first image of the file list.

  files = get_tiffiles(source)
  filename = get_filename()
  ref = args.reference

  #Read the csv file with the data structure
  data_strct = pd.read_csv("channel_name.csv")
  # The following bit of code is to know which idx is the reference channel. 
  # I create a new dataframe idx_values that return the idx of the reference channel with respect to the image 
  # that is being treated
  # this takes into account the empty cells if a channel is not used for a given image. 
  # (reference channel should always be used)
  idx_values = data_strct.copy()
  chan_name = []
  for i in range(data_strct.shape[0]):
  #i is image
    idx = 0
    for j in range(data_strct.shape[1]-1):
    #j is channel
      if(str(data_strct[data_strct.columns[j+1]][i]) != 'nan'):
        chan_name.append(data_strct[data_strct.columns[j+1]][i] +'_'+ data_strct.columns[j+1] +'_'+ data_strct['Filename'][i])
        idx_values[data_strct.columns[j+1]][i] = idx
        idx += 1

  print('Reference channel used is:', ref)
  print ('Reference image is from:', files[0])
  tif_ref = tifffile.imread(source +'/'+ files[0])

  print('Loaded tif_ref', getsizeof(tif_ref)/10**6, 'MB')
  chan_ref = np.array(tif_ref[idx_values[ref][idx_values['Filename'] == filename[0]].values[0]])
  print('Extracted chan_ref', getsizeof(chan_ref)/10**6, 'MB')
    
  #Do not need tif_ref only chan_ref from it (free memory)
  del tif_ref
  gc.collect()
  
  i_max, j_max = get_max_shape(source)

  # To see if padding is required
  if(np.shape(chan_ref)[0] == i_max and np.shape(chan_ref)[1] == j_max):
    pad_chan_ref = chan_ref
  else:
    print('---------------- Images will be padded -----------------')
    pad_chan_ref = pad_image(i_max, j_max, chan_ref)
  
  #If you asked for downscaling the image
  if args.downscale:
    anti_alias = True
    rescale_fct = args.factor
    print('----- Images will be downscaled',rescale_fct*100,'%  resolution------')
    pad_chan_ref = rescale(pad_chan_ref, rescale_fct, anti_aliasing=anti_alias, preserve_range = True)
    print('chan_ref rescaled', getsizeof(np.array(pad_chan_ref))/10**6, 'MB')
  else:
    print('--------------- Keeping full resolution ----------------')
    print('chan_ref ', getsizeof(np.array(pad_chan_ref))/10**6, 'MB')

  del chan_ref
  gc.collect()

  # We have our reference channel, now we go get our image to align
  for idx in range(len(filename)):
    print('--- Aligning tif:', files[idx])
    tif_mov = tifffile.imread(source +'/'+ files[idx])
    print('Shape of image is: ', np.shape(tif_mov), 'size', getsizeof(tif_mov)/10**6, 'MB')
    print('------- Reference Channel idx in the image:',idx_values[ref][idx_values['Filename'] == filename[idx]].values[0] + 1)
    chan_mov = np.array(tif_mov[idx_values[ref][idx_values['Filename'] == filename[idx]].values[0]])
    
    #delete tif_mov as it is not needed for registration (only need chan_ref) this is done to free memory.
    del tif_mov
    gc.collect()

    #padding image if it is needed
    if(np.shape(chan_mov)[0] == i_max and np.shape(chan_mov)[1] == j_max):
      pad_chan_mov = chan_mov
    else:
      print('Padding image size to', i_max, j_max)
      pad_chan_mov = pad_image(i_max, j_max, chan_mov)
    del chan_mov
    gc.collect()

    #Downscaling image if asked
    if args.downscale:
      pad_chan_mov = rescale(pad_chan_mov, rescale_fct, anti_aliasing=anti_alias, preserve_range = True)
      print('Down scaled the image to', np.shape(pad_chan_mov), getsizeof(np.array(pad_chan_mov))/10**6, 'MB')

    #Doing the registration between both channels
    print('Getting Transform matrix')
    #ATTENTION: If you want to do other types of registration from pystackreg, here is where you do it!!!!!
    # you have the following options: TRANSLATION, RIGID_BODY, SCALED_ROTATION, AFFINE, BILINEAR
    # if you want more information, please check the following link 
    # https://pystackreg.readthedocs.io/en/latest/
    sr = StackReg(StackReg.RIGID_BODY)
    sr.register(pad_chan_ref, pad_chan_mov)
    print('Registration matrix acquired and now transforming the channels') 
    # if you want to see the transformation matrix : sr.get_matrix()

    del pad_chan_mov
    gc.collect()

    #Reload tif_mov to align all the images with the transformation that we got from registration
    tif_mov = tifffile.imread(source +'/'+ files[idx])
    
    aligned_images = []
    channels = np.shape(tif_mov)[0]
    for channel in range(channels):

      #To put reference channel as first channel in the image and to see if we need padding
      if channel == 0:
        if(np.shape(tif_mov)[1] == i_max and np.shape(tif_mov)[2] == j_max):
          pad_tif_mov = tif_mov[idx_values[ref][idx_values['Filename'] == filename[idx]].values[0],:,:]
        else:
          pad_tif_mov = pad_image(i_max, j_max, tif_mov[idx_values[ref][idx_values['Filename'] == filename[idx]].values[0],:,:])
      else:
        if(np.shape(tif_mov)[1] == i_max and np.shape(tif_mov)[2] == j_max):
          pad_tif_mov = tif_mov[0,:,:]
        else:
          pad_tif_mov = pad_image(i_max, j_max, tif_mov[0,:,:])

      #To free memory as we do not need these channels
      #if it was the first iteration, we want reference channel as our first registered channel
      #thus we have reference channel removed, after it is the normal order (remove first channel)
      if channel == 0:
        if np.shape(tif_mov)[0] > 1: 
          tif_mov = np.delete(tif_mov, idx_values[ref][idx_values['Filename'] == filename[idx]].values[0], axis = 0)
      else:
        if np.shape(tif_mov)[0] > 1: 
          tif_mov = np.delete(tif_mov, 0, axis = 0)
      
      #To downscale the channel if asked
      if args.downscale:
        pad_tif_mov = rescale(pad_tif_mov, rescale_fct, anti_aliasing=anti_alias, preserve_range = True)
      
      #Doing the image registration
      aligned_tif = sr.transform(pad_tif_mov)
      del pad_tif_mov
      gc.collect()

      #Due to the registration, some values become negative at the edges (with the transformation matrix)
      #If I do not correct this, i get white bands as these negative values get converted to maximum values in uint16.
      #I do equal to 0 as it is at the edge and can be considered as background
      aligned_tif[aligned_tif <= 0] = 0
      #when converting to uint, it troncatenates the values (eg 1000.7 -> 1000)
      aligned_tif = aligned_tif.astype(np.uint16)

      aligned_images.append(aligned_tif)
      print('info -- channel', channel,'aligned')
      del aligned_tif
      gc.collect()

    print('Transformed channels done, image is of size', np.shape(aligned_images), 
                                  getsizeof(np.array(aligned_images))/10**6, 'MB')
    del tif_mov
    gc.collect()

    print('Saving aligned image')
    with tifffile.TiffWriter('./aligned/'+filename[idx]+'_al.ome.tif',
                                 bigtiff = True) as tif:
      tif.save(np.array(aligned_images))

    del aligned_images
    gc.collect()

  get_aligned_marker_names(ref)
  print('DONE! All images are registered')

def final_image(args,source):
  # loads one registed image after another and saves them all into one image. The first image keeps the reference channel
  # whereas we remove reference channels for all the others
  print('-------------- Final image --------------')
  ref = args.reference
  get_final_marker_names(ref)
  files = get_tiffiles(source)
  tif = tifffile.imread(source +'/'+ files[0])

  final_image = tif
  print('Adding first image:', files[0], ' ------ ' ,np.shape(final_image))

  for idx in range(len(files)-1):
    print('--- Adding:', files[idx+1])
    tif = tifffile.imread(source +'/'+ files[idx+1])
    print('Tif shape', np.shape(tif))
    tif = np.delete(tif, 0, 0)
    print('Removed alignment channel', np.shape(tif))

    final_image = np.append(final_image, tif, axis = 0)
    print(np.shape(final_image))
    print('Image size: ', getsizeof(np.array(final_image))/10**6, 'MB')

  print('Final image size: ',np.shape(final_image), getsizeof(np.array(final_image))/10**6, 'MB')
  with tifffile.TiffWriter('./final_image.ome.tif', bigtiff = True) as tif:
    tif.save(np.array(final_image))

  print('Final image saved!')
