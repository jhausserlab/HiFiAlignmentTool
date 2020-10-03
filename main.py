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

parser.add_argument('source', type=dir_path, help='input path, the folder of czi to stitch')
parser.add_argument('destination', type=dir_path, help='output path, the folder where to put the stitched images')
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
  '-d',
  '--downscale',
  action='store_const',
  const=True,
  default=False,
  help='downscale images if images too large for computer RAM'
)
parser.add_argument(
  '--factor', 
  metavar ='N', 
  type = float, 
  nargs ='+', 
  default=[0.2],
  help ='Scale factor between 0. - 1.') 


args = parser.parse_args()

run(args)
