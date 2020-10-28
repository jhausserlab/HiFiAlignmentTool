import glob
import numpy as np
import os
import tifffile
import pathlib
from image_processing.czi import get_image
from image_processing.registration import get_tiffiles, get_aligned_images, final_image
from sys import getsizeof
import gc
import pandas as pd

def get_czifiles(source):
    data_strct = pd.read_csv("channel_name.csv")
    file_name = []
    for i in range(data_strct.shape[0]):
      filepath = glob.glob(source+'/'+data_strct['Filename'][i]+'*.czi', recursive=True)[0]
      file_name.append(filepath.split('/')[2])

    return file_name

def list_files(source, files):
  file_names = '\n'.join(files)
  file_list = f'''Found the following image files in {source}: \n\n{file_names}\n'''

  print(file_list)

def ask_for_approval():
  hasApproval = False

  while not hasApproval:
    user_input = input('Continue with image processing for the above files? (Yes/No): ').strip().lower()
    if user_input == 'yes' or user_input == 'y':
      hasApproval = True
    elif user_input == 'no' or user_input == 'n':
      print('Terminating image processing.')
      exit()
    else:
      print('Please enter a valid option.')

def write(args, file, image):
  #saves a txt file with the images dimensions (C,X,Y) to know if padding will be required during registration
  #saves the stitched image in the destination file
  if args.destination:
    if os.path.exists(args.destination):
      name = file.split('.')[0]
      name_txt = 'image_shape'
      file = f'{os.path.basename(args.destination)}/{name}'

      with tifffile.TiffWriter(file  + '_st.ome.tif', bigtiff = True) as tif:
        tif.save(image)

      with open(f'{os.path.basename(args.destination)}/{name_txt}' + '.txt', 'a') as f:
        #Save dimension C X Y for processing when we want to register
        f.write(str(np.shape(image)[0])+','+str(np.shape(image)[1])+','+str(np.shape(image)[2])+';')
    else:
      print('destination path does not exist')

def channel_check(args, source):
  print('------- Verifying that CSV file matches images -------')
  ref = args.reference
  data_strct = pd.read_csv("channel_name.csv")

  #To check if the reference channel is present in all images
  for i in range(data_strct.shape[0]):
    if(str(data_strct[ref][i]) == 'nan'):
      print('Image', data_strct['Filename'][i],'does not have the reference channel.')
      print(data_strct[['Filename',ref]])
      print('Please check your CSV file.')
      print('--------- Terminating program ---------')
      exit()
  print('Reference channel is present in all images, continue program.')

  #To check if the images have the same number of channels as in the CSV
  idx_values = data_strct.copy()
  for i in range(data_strct.shape[0]):
    idx = 0
    for j in range(data_strct.shape[1]-1):
      if(str(data_strct[data_strct.columns[j+1]][i]) != 'nan'):
        idx_values[data_strct.columns[j+1]][i] = idx
        idx += 1

  file = open(source + '/image_shape.txt','r')
  images_shape = file.read()
  split = images_shape.split(';')
  for i in range(len(split)-1):
    chan = split[i].split(',')
    if(int(chan[0]) != idx_values.iloc[:,-1][i]+1):
      print('The number of channels in CSV file doesn’t match the number of channels in image', idx_values.iloc[:,0][i],'.')
      print(int(split[i].split(',')[0]),'in image', idx_values.iloc[:,0][i] ,'and', idx_values.iloc[:,-1][i]+1,'in CSV file.')
      print(data_strct.loc[i])
      print('Please modify your CSV file')
      print('--------- Terminating program ---------')
      exit()
  print('# Channels in CSV match channels in images, continue program')
  print('------- CSV matches images and all images have the reference channel -------')

def get_img_dim(source):
  print('----- Extracting image dimensions and putting them in image_shape.txt -----')
  files = get_tiffiles(source)
  file_name = open(source +'/image_shape.txt',"w")
  for i in range(len(files)):
    tif = tifffile.imread(source +'/'+ files[i])
    file_name.write(str(np.shape(tif)[0])+','+str(np.shape(tif)[1])+','+str(np.shape(tif)[2])+';')
    del tif
    gc.collect()
  file_name.close()

def run(args):
  #runs the different steps of the code: - stiching - registration - save all in one image
  if not args.disable_stitching:
    source = args.source
    files = get_czifiles(source)
    list_files(source, files)

    if not args.yes:
      ask_for_approval()

    # To reset the txt file. Often during my testing I would forget and that created errors.
    # In case others do the same thing. This will help
    file_name = open(args.destination +'/image_shape.txt',"w")
    file_name.write('')
    file_name.close()
    for file in files:
      image = get_image(source, file)
      print('Saving image and image dimension')
      write(args, file, image)
      print('DONE!')
      del image
      gc.collect()
  else:
    print("------- No stitching done -------")

  if not args.disable_registration:
    source = args.destination
    files = get_tiffiles(source)
    list_files(source,files)

    if not args.yes:
      ask_for_approval()

    if args.getdim:
      get_img_dim(source)
    channel_check(args, source)
    get_aligned_images(args, source)
  else:
    print("----- No image registration -----")

  if args.finalimage:
    source = './aligned'
    files = get_tiffiles(source)
    list_files(source,files)

    if not args.yes:
      ask_for_approval()

    final_image(args, source)
  else:
    print("-------- No final image ---------")
