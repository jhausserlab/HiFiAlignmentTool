import glob
import numpy as np
import time
import os
from datetime import timezone, datetime, timedelta
import tifffile
import pathlib
import napari
#from image_processing.czi import show, write
from image_processing.process import get_images

def get_files(source):
  return glob.glob(source + '/**/*.czi', recursive=True)

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
      # viewer = napari.view_image(images[0][0].astype(np.uint8))
      for czi in images:
        viewer.add_image(np.array(czi))

def write(args, imagesToShape):

  source = args.source
  files = get_files(source)

  if args.destination:
    if os.path.exists(args.destination):
      #name = f'{datetime.now().strftime("%Y-%m-%d")}_{int(datetime.now(tz=timezone.utc).timestamp() * 1000)}'
      name = files[0].split('.')[1].split('/')[2]
      names = 'images_shape'
      #extension = 'ome.tif'
      #extension = 'tif'
      #file = f'{os.path.basename(args.destination)}/{name}.{extension}'
      file = f'{os.path.basename(args.destination)}/{name}'

      with tifffile.TiffWriter(file  + '.tif', bigtiff = True) as tif:
        # additional metadata can be added, and in a more compatible format
        # axes is just an (incorrect) example
        # https://stackoverflow.com/questions/20529187/what-is-the-best-way-to-save-image-metadata-alongside-a-tif
        #for image in images:
        #tif.save(images, metadata={'axes':'TZCYX'}) <--- metadata does not work
        tif.save(imagesToShape)

      with open(f'{os.path.basename(args.destination)}/{names}' + '.txt', 'w') as f:
        f.write(str(np.shape(imagesToShape))+'\n')
    else:
      print('destination path does not exist')


'''
Was just below def write 
  # Because i have np-array before, this part of code isn't needed as 
  # it was used to get dimensions from a list and not np-array
  #shape = np.shape(imagesToShape)
  #newShape = shape[0] * shape[1]
  #images = np.array(imagesToShape).reshape(1, newShape, shape[2], shape[3])
  #images = np.array(imagesToShape).reshape(shape)
  #images = np.array(imagesToShape)
  #print(type(images))

  #print('np.array(images).flatten()', np.shape(images))
'''


def run(args):
  # gets the files and then gets the processed aligned images (through get_images) after shows through napari 
  # and finally saves a tif
  if args.time: run_time = time.monotonic()

  source = args.source
  files = get_files(source)

  list_files(source, files)

  if not args.yes:
    ask_for_approval()

  images = get_images(args, files)

  print('In RUN.py, shape of images', np.shape(images))

  # show in napaari
  show(args, images)
  print('Saving image and image dimension')
  write(args, images)

  if args.time: print(timedelta(seconds=time.monotonic() - run_time))
