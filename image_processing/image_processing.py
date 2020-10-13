import glob
import numpy as np
import os
import tifffile
import pathlib
import napari
from image_processing.czi import get_images
from image_processing.registration import get_aligned_images
from image_processing.registration import get_tiffiles
from sys import getsizeof
import gc

def get_files(source):
  return sorted(glob.glob(source + '/**/*.czi', recursive=True))

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

def show(args, images):
  if not args.yes:
    with napari.gui_qt():
      viewer = napari.Viewer()
      for czi in images:
        viewer.add_image(np.array(czi))

def write(args, file, image):

  if args.destination:
    if os.path.exists(args.destination):
      name = file.split('.')[1].split('/')[2]
      name_txt = 'image_shape'
      file = f'{os.path.basename(args.destination)}/{name}'

      with tifffile.TiffWriter(file  + '_pr.ome.tif', bigtiff = True) as tif:
        tif.save(image)

      with open(f'{os.path.basename(args.destination)}/{name_txt}' + '.txt', 'a') as f:
        #Save dimension C X Y for processing when we want to register
        f.write(str(np.shape(image)[0])+','+str(np.shape(image)[1])+','+str(np.shape(image)[2])+';')
    else:
      print('destination path does not exist')

def run(args):
  # gets the files and then gets the stitched images (through get_images) and finally does image registration
  # and finally saves a tif

  source = args.source
  files = get_files(source)
  list_files(source, files)

  if not args.yes:
    ask_for_approval()

  if not args.disable_stitching:
    for file in files:
      image = get_images(args, file)
      #show in napari
      #show(args, image)
      print('Saving image and image dimension')
      write(args, file, image)
      print('DONE!')
      del image
      gc.collect()
  else:
    print("No stitching done")

  if not args.disable_registration:
    source = args.destination
    list_files(source,get_tiffiles(source))

    if not args.yes:
      ask_for_approval()

    get_aligned_images(args, source)
  else:
    print("Image not registered")
    exit()
