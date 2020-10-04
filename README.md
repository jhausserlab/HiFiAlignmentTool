# Microscopy Image Processing

Prototype to register czi microscopy images.
This code is optimised at a memory level to be able to stitch and register high resolution images.

## Getting started
From the folder where you are launching the code, you need to have:
- a folder with the czi files that you want to process (which will be the "source")
- an EMPTY output folder (where stitched images and image dimension will be save, it will be the "destination")
- a folder called aligned (where registered images will be saved).

If you are running a new set of czi, it is important that the conditions previously mentioned are met (meaning output file is empty and the czi file has only the files you want to process). Else all files will be read.

Currently, for an image of dimension 16'000 x 21'000 pixels the computer uses a maximum of 52GB to run all the code.

WARNING: It is important that in your CZI files the reference channel (in our case dapi) is the last channel of your image stack.

To run main.py you need to run at least the 2 arguments "source" and "destination":
```
python3 main.py ./path/to/czi_files ./output_folder
```
main.py has also 5 optional arguments:
1. -y, --yes --> runs the code without asking questions before stitching and before registration
2. --disable-stitching --> if you want to only register
3. --disable-registration --> if you want to only stitch
3. -r --removeDapi --> if you want to remove the dapi channels from registered image (except for the dapi used as reference for alignment)
4. -d, --downscale --> if you want to reduce the resolution of your image (default is 0.33)
5. --factor 0.XX --> the downscale factor you want between 0 and 1 ( --downscale is required else it is full resolution that is done)

if you want more information on the arguments run
```
python3 main.py --help
```

## What does the code do
STITCHING
1. Load the czi file paths
2. Take one czi file and stitch the image
3. Save the dimensions of the image in a txt file called "images_shape.txt" in the "destination" folder(at the start the .txt should not exist and the program will create it)
4. Save the stitched image in the "destination" folder
5. Restart from step 2 for the next czi file.

IMAGE REGISTRATION
1. Load the first image in the list which will be used as the reference
2. Extract last channel which is used to align (in our case DAPI)
3. Delete other channels
4. Load the next image i and extract last channel used to align (delete other channels)
5. Pad if needed
6. Rescale if asked in command line (0.33 factor by default)
7. Do image registration on dapi_ref and dapi_i using pystackreg library
8. Transform the other channels of image i with the known transformation
9. Remove the dapi channel (if not the reference image) if asked
10. Save the registered images into the folder aligned.
11. Restart from step 4. with the next image


