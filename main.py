import os
import argparse
from image_processing.image_processing import run
# calls the run function and enables to put different arguments to process the images.
def dir_path(string):
  if os.path.isdir(string):
    return string
  else:
    raise argparse.ArgumentTypeError(f'"{string}" is not a valid path')

parser = argparse.ArgumentParser(description='Microscopy Image processing')

parser.add_argument('source', type=dir_path, help='input path, the folder of images to process')
parser.add_argument('destination', type=dir_path, help='ouput path, the folder where to put the generated image')
parser.add_argument(
  '-t',
  '--time',
  action='store_const',
  const=True,
  default=False,
  help='measure time of slow running function calls'
)
parser.add_argument(
  '-y',
  '--yes',
  action='store_const',
  const=True,
  default=False,
  help='generate image without asking any questions'
)
parser.add_argument(
  '--disable-registration',
  action='store_const',
  const=True,
  default=False,
  help='disable image registration'
)
parser.add_argument(
  '--disable-subtract-background',
  action='store_const',
  const=True,
  default=False,
  help='disable subtract background'
)

args = parser.parse_args()

run(args)
