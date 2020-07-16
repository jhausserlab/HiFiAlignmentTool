import os
import glob
from image_processing.process import get_images
import numpy as np
import tifffile

def get_files(source):
  return glob.glob(source + '/**/*.czi', recursive=True)

def list_files(source, files):
  file_names = '\n'.join(files)
  msg = f'''Found the following image files in {source}: \n\n{file_names}\n'''

  print(msg)

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

def run(args):

  # if args.destination:
  #   print('d', args.destination)
  #   if os.path.exists(args.destination):
  #     print('has  path')
  #     try:
  #       print(os.path.basename(args.destination))
  #     except:
  #       print('no base')

  source = args.source
  files = get_files(source)

  list_files(source, files)

  if not args.yes:
    ask_for_approval()

  images = get_images(files)

  print('np.shape', np.shape(images))
  print('type', type(images))
  # print('all', images)

  # show(args, images)
      # viewer = napari.view_image(images[0][0].astype(np.uint8))

  if args.destination:
    # print('d', args.destination)
    if os.path.exists(args.destination):
      # print('has  path')
      # try:
        # print(os.path.basename(args.destination))
      file =  f'{os.path.basename(args.destination)}/{"test.ome.tif"}'
      # file =  '/Users/fredrik/Dropbox/_projects/_praktik/_dev/test_aicsimageio/images/temp.ome.tiff'
      with tifffile.TiffWriter(file) as tif:
          # tif.save(images, metadata={'axes':'TZCYX'})
          tif.save(np.array(images), metadata={'axes':'TZCYX'})
      # except:
        # print('files save failed')

