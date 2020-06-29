import os
import argparse
from image_processing.image_processing import run

def dir_path(string):
  if os.path.isdir(string):
    return string
  else:
    raise argparse.ArgumentTypeError(f'"{string}" is not a valid path')

parser = argparse.ArgumentParser(description='Microscopy Image processing')

parser.add_argument('source', type=dir_path, help='input path, the folder of images to process')
parser.add_argument('destination', type=dir_path, help='ouput path, the folder where to put the generated image')
parser.add_argument(
  '-y',
  '--yes',
  action='store_const',
  const=True,
  default=False,
  help='generate image without asking any questions'
)

## maybe add step-by-step options for when to show napari-view
## i.e. -b flag for showing napari after brightness

args = parser.parse_args()

run(args)
