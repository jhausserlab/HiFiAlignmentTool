import os
import argparse
from image_registration.image_processing import run

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
  help='input path, the folder of czi to reassemble')
parser.add_argument(
  'destination', 
  type=dir_path, 
  help='output path, the folder where to put the reassembled images')
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
  help ='The reference channel that will be used for registration, based on the csv file (defaut is DAPI)'
)
parser.add_argument(
  '--resolution', 
  type = float,
  default=0.325,
  help ='Resolution of the original image: what does 1 pixel represent in micrometers (default is 0.325)'
) 
parser.add_argument(
  '--disable-reassemble',
  action='store_const',
  const=True,
  default=False,
  help='disable reassembling of czi file into an image (useful for devel or if OME TIFFs are provided)'
)
parser.add_argument(
  '--disable-registration',
  action='store_const',
  const=True,
  default=False,
  help='disable image registration (useful for devel)'
)
parser.add_argument(
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
  help ='Scale factor between 0. - 1. (only used if --downscale is set)'
) 
parser.add_argument(
  '--nofinalimage',
  action='store_const',
  const=False,
  default=True,
  help='If you do not want to create the final image with all the channels'
)
parser.add_argument(
  '--background',
  type = str,
  default= 'False',
  help='Filename to do background subtraction on your images'
)
parser.add_argument(
  '--backgroundMult',
  type = float,
  default= 1,
  help='To multiply the background intensity of all channel that is subtracted for each respective channels '
)
parser.add_argument(
  '--fullname',
  action='store_const',
  const=True,
  default=False,
  help='If you use this argument, in the metadata of your final image, you will have the full name marker|channel|filename. Else it is just marker'
)

args = parser.parse_args()

run(args)
