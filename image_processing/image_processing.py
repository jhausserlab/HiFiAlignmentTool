import os
import glob
import image_processing.process

def get_file_names(source):
  return '\n'.join(glob.glob(source + '/**/*.czi', recursive=True))

def list_files(source):
  msg = f'''Found the following image files in {source}: \n\n{get_file_names(source)}'''
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
  source = args.source

  list_files(source)
  # ask_for_approval()
  process.images(source)


