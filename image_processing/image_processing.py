import glob
import numpy as np
import time
from datetime import timedelta
from image_processing.czi import show, write
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

def run(args):
  if args.time: run_time = time.monotonic()

  source = args.source
  files = get_files(source)

  list_files(source, files)

  if not args.yes:
    ask_for_approval()

  images = get_images(args, files)

  print('np.shape', np.shape(images))
  print('type', type(images))

  show(args, images)
  # write(args, images)

  if args.time: print(timedelta(seconds=time.monotonic() - run_time))
