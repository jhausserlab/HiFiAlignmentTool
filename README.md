# Microscopy Image Processing

Code to register czi microscopy images or OME.TIF/TIF with **python 3**.
This code is optimised at a memory level to be able to stitch and register (translation + rotation) high resolution images in **ome.tif**. 

Currently, for images of dimension 16'000 x 21'000 pixels the computer uses a maximum of 52GB to run all the code.
I recommend these dimensions (give or take ~1000 pixels) if you are using a 64GB RAM computer. 
The images do not need to have the same dimension X,Y as the code will pad all images with the maximum X,Y dimensions of the image set.

**Keywords**: Image Registration, Image alignment, CZI, OME.TIF, TIF, High Resolution Imagery, Python

## Getting started

Download the folder from Github.

From the **terminal**, access that folder using **cd** to arrive to that folder path, as it will be used as the working directory.

To install the required librairies for the code, you can run in the terminal from that folder:

```
python3 installLib.py
```

This installs all the librairies that you require for the process (via pip, which is built-in by default with python3). 
After having done so, you can remove this script if desired.

From the folder where you are launching the code, you will have:
- a folder **czi**, where the czi files that you want to process will be stored (which will be the "source").
- an EMPTY folder called **stitched** (where stitched images and image dimension will be save, it will be the "destination").
- an EMPTY folder called **aligned** (where registered images will be saved).
- **channel_name.csv** with the experimental layout of the images (a matrix with files x channels and in the cross section the respective marker).
- **image_processing** folder with the python scripts.
- **main.py** the main script to run all the code
- **installLib.py** the script to install all librairies required for the code

Here is how your folder should look like where you run the code:
<p align="center">
  <img src="structure.png"  width="500" height="300">
</p>

If you have downloaded the folder from Github, you should have the same structure as the image above (with the addition of a couple of files that should be removed).

**Please remove the following files as they are not needed for the code**:

- **README.md**
- **structure.png**
- ./czi/**empty.txt**
- ./aligned/**empty.txt**
- ./stitched/**image_shape.txt**


**WARNING:** If you are running a new set of czi, it is important that the conditions previously mentioned are met (meaning: stitched folder is empty, aligned folder is empty,  czi folder has only the czis you want to process, channel_name.csv has the correct layout). Else "old" files will be read with the new ones.

To run main.py you need to run at least the 2 arguments "source" and "destination" (with the example of the structure in the image, which is what you downloaded):
```
python3 main.py ./czi ./stitched
```
main.py has also 8 optional arguments:
1. -y, --yes --> runs the code without asking questions before stitching and before registration
2. --reference CHAN --> in place of chan put the channel you want to align with (DAPI by default)
3. --resolution XX --> the resolution of input images in um/pixel which will be added in the metadata(0.325 um by default)
4. --disable-stitching --> if you want to skip the stitching
5. --disable-registration --> if you want to skip the image registeration
6. -d, --downscale --> if you want to reduce the resolution of your image (default is 0.33) if your image is too large for processing.
7. --factor 0.XX --> the downscale factor you want between 0 and 1 ( the argument --downscale is required else it is full resolution that is done)
8. --finalimage --> if you want to save the final image containing all the channels without the reference channel except for the one used as reference for registration


if you want more information on the arguments run
```
python3 main.py --help
```

## Test code

When downloading the github folder, you have a mock image set with its respective csv file. For demonstration purposes the markers are named a letter in alphabetical order with respect to the reference channel. 
To ensure the code is running and to also try the different options, you can work with this small image set.
First of all I suggest to run the following code
```
python3 main.py ./czi ./stitched --reference DAPI --resolution 0.325 --finalimage
```
This will stitch, register and save the final image and ask you to confirm for every step. Once this works, you can skip the ask for approval part by adding -y like so:
```
python3 main.py ./czi ./stitched --reference DAPI --resolution 0.325 --finalimage -y
```
Finally, if the images are too large for your computer to process and you would like to downscale the image (e.g 50% resolution) you can do the following:
```
python3 main.py ./czi ./stitched --reference DAPI --resolution 0.325 --finalimage -y --downscale --factor 0.5
```
## What does the code do

**STITCHING**
1. Load the czi file paths
2. Take one czi file and stitch the image
3. Save the dimensions of the image in a txt file called "images_shape.txt" in the "destination" folder
4. Save the stitched image in ome.tif in the "destination" folder
5. Restart from step 2 for the next czi file.

**IMAGE REGISTRATION**

0. If no stitching done, load each image and save the dimensions in a txt file.
1. Load the first image in the csv list which will be used as the reference
2. Extract reference channel which is used for alignment using the CSV file.
3. Delete other channels
4. Load the next image i and extract reference channel used to align (delete other channels)
5. Pad images if needed
6. Rescale if asked in command line
7. Do image registration on chan_ref and chan_i using pystackreg library
8. Transform the other channels of image i with the known transformation
9. Save the registered images in ome.tif into the folder aligned. They are saved with metadata for the channel names and scale of the image (changes the scale accordingly if downsized)
10. Restart from step 4. with the next image
11. Save a txt file with the marker names in the right order with the new images based on the CSV file (MARKER_CHANNEL_FILE)

**FINAL IMAGE**
1. Loads the first image into an array
2. Loads the next image and removes reference channel
3. Repeat step 2 until the end
4. Final image is saved in ome.tif in the main folder where you run the code. It is saved with metadata for the channel names and scale of the image
5. Save a txt file with the marker names in the right order for the final image based on the CSV file (MARKER_CHANNEL_FILE)

It is important to note that the loading of the file paths are done in the order given in the CSV file. The CSV file must be correct for proper running of the code!

NB: The image registration is done thanks to pystackreg library. In this code, RIGID_BODY (translation + rotation) is hard coded as it is the most consistent. However you can also add scaling or scaling + shear. If you want to change the registration process you need to access the script registration.py and modify the line: **sr = StackReg(StackReg.RIGID_BODY)** replace RIGID_BODY with: SCALED_ROTATION or AFFINE.
See https://pystackreg.readthedocs.io/en/latest/ for more information on the registration process.
