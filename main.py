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

parser.add_argument(
  'source', 
  type=dir_path, 
  help='input path, the folder of czi to stitch')
parser.add_argument(
  'destination', 
  type=dir_path, 
  help='output path, the folder where to put the stitched images')
parser.add_argument(
  '-y',
  '--yes',
  action='store_const',
  const=True,
  default=False,
  help='generate image without asking any questions'
)
parser.add_argument(
  '--reference', 
  type = str,
  default='DAPI',
  help ='The reference channel that will be used for registration (based on the csv file)'
)
parser.add_argument(
  '--resolution', 
  type = float,
  default=0.325,
  help ='Resolution of the image: what does 1 pixel represent in micrometers'
) 
parser.add_argument(
  '--disable-stitching',
  action='store_const',
  const=True,
  default=False,
  help='disable stitching of czi file into an image'
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
  type = float,
  default=0.33,
  help ='Scale factor between 0. - 1. (needs --downscale to work else it is full resolution)'
) 
parser.add_argument(
  '--finalimage',
  action='store_const',
  const=True,
  default=False,
  help='Saves all the channels into one image and removes all dapis except from the first image'
)
parser.add_argument(
  '--getdim',
  action='store_const',
  const=True,
  default=False,
  help='If you already have tif images and you do not do czi stitching, use this argument to create the image_shape.txt'
)

args = parser.parse_args()

run(args)
