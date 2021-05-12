# Microscopy Image Registration

Code to register czi microscopy images or OME.TIF with **python 3**.
This code is optimised at a memory level to be able to reassemble and register (translation + rotation) high resolution images in **ome.tif**. 

Currently, for images of dimension 16'000 x 21'000 pixels the computer uses a maximum of 52GB to run all the code.
I recommend these dimensions (give or take ~1000 pixels) if you are using a 64GB RAM computer. If you are working with bigger images, you will likely need to have a computer with more RAM.
The images do not need to have the same dimension X,Y as the code will pad all images with the maximum X,Y dimensions of the image set. If you have created a set of images with empty channels for background subtraction, the code can do the background subtraction for you.

**Keywords**: Image Registration, Image alignment, CZI, OME.TIF, High Resolution Imagery, Python, HIFI

## Getting started

Download the folder from Github.

From the **terminal**, access that folder using **cd** to arrive to that folder path, as it will be used as the working directory.

If you have root access, to install the required librairies for the code, you can run in the terminal from that folder:

```
python3 installLib.py
```

else if you do not have root access (e.g from a server or multi-account computer), you can run:

```
python3 installLibUser.py
```

This installs all the librairies that you require for the process (via pip, which is built-in by default with python3). 
After having done so, you can remove this script if desired.

From the folder where you are launching the code, you will have:
- a folder **czi**, where the czi files that you want to process will be stored (which will be the "source").
- an EMPTY folder called **reassembled** (where reassembled images and image dimension will be save, it will be the "destination").
- an EMPTY folder called **aligned** (where registered images will be saved).
- **channel_name.csv** with the experimental layout of the images (a matrix with files x channels and in the cross section the respective marker).
- **image_registration** folder with the python scripts.
- **main.py** the main script to run all the code.
- **installLib.py** the script to install all librairies required for the code if you have root access.
- **installLibUser.py** the script to install all librairies required for the code if you do not have root access.

**Please** respect the CSV file structure with: the name of the CSV called channel_name.csv, the filenames as the rows and the channels as the columns.
The structure given in the mock dataset is the correct one. 
**Please be sure that the order of the channels in the CSV file is the same as in the image** (e.g. in CZI channel1 is Cy3, channel2 Cy5 and channel3 Cy7 -> so in CSV file you have the first column as Cy3, second column as Cy5 and third column as Cy7). In the case you have a czi file for the background subtraction, it should **not** be included in the CSV file.

**WARNING:** Do not put the special character **|** in any of the names in the CSV files (whether marker names, filenames or channel names). This **will** cause errors in the processing of the images if you want the fullname in the metadata.

Here is how your folder should look like where you run the code:
<p align="center">
  <img src="structure.png"  width="500" height="300">
</p>

If you have downloaded the folder from Github, you should have the same structure as the image above (with the addition of a couple of files that can be removed).

**You can remove the following files as they are not needed for the code**:

- **README.md**
- **structure.png**
- ./aligned/**empty.txt**

To run main.py you need to run at least the 2 arguments "source" and "destination" (with the example of the structure in the image, which is what you downloaded):
```
python3 main.py ./czi ./reassembled
```
main.py has also optional arguments:
1. -y, --yes --> runs the code without asking questions before reassembling, registration and final_image creation.
2. --reference CHAN --> in the place of CHAN put the channel you want to align with (DAPI by default).
3. --resolution XX --> in the place of XX the resolution of input images in um/pixel which will be added in the metadata (0.325 um by default).
4. --disable-reassemble --> if you want to skip the reassembling.
5. --disable-registration --> if you want to skip the image registeration.
6. --downscale --> if you want to reduce the resolution of your image (default is 0.33) if your image is too large for processing.
7. --factor 0.XX --> the downscale factor you want between 0 and 1 ( the argument --downscale is required else it is full resolution that is done). CAREFUL: if you put 0.20 for example that means that the image will be 20% of the full resolution thus for a 1000x1000 pixel image you will have a 200x200 pixel output image.
8. --nofinalimage --> if you do not want to save the final image (containing all the channels without the reference channel except for the one used as reference for registration).
9. --background filename --> if you have a czi file that contains the channels with no markers except for the reference channel used for registration. You can put it in the czi folder and the code will remove the background for each respective channel (except for reference channel) in the final image output. If no argument provided, it will not do any background subtraction.
10. --backgroundMult XX --> if you want to remove the background multiplied by a certain factor XX (1 by default).
11. --fullname --> if you want the full name of the channels (e.g marker | channel | filename). By default it gives just the marker name.
12. --pyramidal --> if you want to save a new final image that is compressed and pyramidal. 


if you want to know what are the arguments via the terminal, type:
```
python3 main.py --help
```

## What does the code do

**REASSEMBLING**
1. Load the czi file paths
2. Take one czi file and reassemble the image
3. Save the dimensions of the image in a txt file called "images_shape.txt" in the "destination" folder
4. Save the reassembled image in ome.tif in the "destination" folder
5. Restart from step 2 for the next czi file
6. This is also done with the background czi file if the argument is provided

**IMAGE REGISTRATION**

0. If no reassembling done, load each image and save the dimensions in a txt file
1. Load the first image in the csv list which will be used as the reference
2. Extract reference channel which is used for alignment using the CSV file
3. Delete other channels
4. Load the next image i and extract reference channel used to align (delete other channels)
5. Pad images if needed
6. Rescale if asked in command line
7. Do image registration on chan_ref and chan_i using pystackreg library
8. Transform the other channels of image i with the known transformation
9. Save the registered images in ome.tif into the folder aligned. They are saved with metadata for the channel names and scale of the image (changes the scale accordingly if downsized)
10. Restart from step 4. with the next image
11. Save a txt file with the marker names in the right order with the new images based on the CSV file (MARKER_CHANNEL_FILE)
12. Image registration is also done with the background czi file if the argument is provided

**FINAL IMAGE**
1. Loads the first image into an array
2. Loads the next image and removes reference channel
3. If asked, does a background subtraction with respect to the background file that you provided.
4. Repeat step 2-3 until the end
5. Final image is saved in ome.tif in the main folder where you run the code. It is saved with metadata for the channel names and scale of the image
6. Save a txt file with the marker names in the right order for the final image based on the CSV file (MARKER_CHANNEL_FILE)
7. If  --pyramidal was called, the code will load fina_image.ome.tif and create a new compressed tiled pyramidal image.

It is important to note that the loading of the file paths are done in the order given in the CSV file. The CSV file must be correct for proper running of the code!

## Test code

When downloading the github folder, you have a mock image set with its respective csv file. For demonstration purposes the markers are named a letter in alphabetical order with respect to the reference channel. 
To ensure the code is running and to also try the different options, you can work with this small image set.
First of all, run the following code
```
python3 main.py ./czi ./reassembled --reference DAPI --resolution 0.325
```
This will reassemble, register and save the final image (in the metadata, it will have the resolution of 0.325um/pixel) and ask you to confirm for every step. Once this works, you can skip the ask for approval option by adding -y like so:
```
python3 main.py ./czi ./reassembled --reference DAPI --resolution 0.325 -y
```
If the images are too large for your computer to process and you would like to downscale the image (e.g 80% of the full resolution) you can do the following:
```
python3 main.py ./czi ./reassembled --reference DAPI --resolution 0.325 -y --downscale --factor 0.8
```
If you provided a background czi file (in our case the background is a copy of test1.czi) you can add the following argument to add background subtraction on your final image:
```
python3 main.py ./czi ./reassembled --reference DAPI --resolution 0.325 -y --background background
```
The resulting image will give you 4 channels that are empty as we are subtracting the channels of test1 with itself.

If you want to increase the background subtraction and you have already done the reassembling and registration, you can skip those steps and just construct the new final image with the following code:
```
python3 main.py ./czi ./reassembled --reference DAPI --resolution 0.325 -y --background background --backgroundMult 2 --disable-reassemble --disable-registration
```

Finally, if you want to have a compressed tiled pyramidal OME-TIF you can add the argument --pyramidal. 
```
python3 main.py ./czi ./reassembled --reference DAPI --resolution 0.325 -y --pyramidal
```
This can also be done after having done the whole process by disabling the previous steps and only doing the pyramidal step (you need to have the final image created as it creates the compressed pyramidal image in function of the final_image).
```
python3 main.py ./czi ./reassembled --reference DAPI --resolution 0.325 -y --disable-reassemble --disable-registration --nofinalimage --pyramidal
```
WARNING: If you want to try the pyramidal function with the test set you need to go into the script registration.py and modify line 582 tileSize = 512 to tileSize = 32. This is because the test image is too small for 512 pixels tilesize.

N.B: The small set of image is taken from a region where the reassembling from czi was poorly done, thus there are slight shifts in the image. 
This is just to help you run the code and understand how the code works.

## F.A.Q:

**Does your code work on all systems?**

Yes, this code runs on Mac, Windows and Linux systems. 

**The code crashes during the step in the terminal:**
```
Getting Transform matrix
```
**What does this mean?**

This means that your computer does not have enough RAM for the image sizes you want to register. You can: crop the image to reduce the size, use the --downscale argument in the code to reduce the resolution of your image, use a computer with more RAM.

**I am getting an error:**
```
'CziFile' object has no attribute 'dims_shape'
```
**What does this mean?**

You likely have an older version of the library aicspylibczi (latest version is 3.0.1). Previous version used the function dims_shape(). You have to uninstall and reinstall the library or you can also change in the script czi.py in line12 the function from get_dims_shape to dims_shape (I recommend using the first solution).

**I am getting an error:**
```
'TiffWriter' object has no attribute 'write'
```
**What does this mean?**

You have an older version of the library tifffile (latest version is 2021.4.8). Previous version used the function tif.save to save tiffs but it has been deprecated and now tif.write is the function to use. Be sure to install the latest version of tifffile. Or else you can replace the parts of the code where there is tif.write by tif.save. WARNING: Do not do this for the function pyramidal_final_image as it is only in the latest version that you can do a pyramidal compressed tiff. 

**Can I use Qupath to analyse further the final image?**

Yes, this image can be used in Qupath. However, if you are working with a very large image, you will need a tiled pyramidal image for QuPath to open. This can be done using the argument --pyramidal to save the image in that format. Or you can also open the final_image.ome.tif in ZEN and save that image in CZI format. QuPath can handle both.

**I am trying to do pyramidal from the test set and I am getting an error**

If you want to try the pyramidal function with the test set you need to go into the script registration.py and modify line 582 **tileSize = 512** to **tileSize = 32**. This is because the test image is too small for 512 pixels tilesize.

**Can I have more details on the pyramidal argument?**

What it does is:
- loads the final_image.ome.tif 
- creates 4 levels of resolution (100% 50% 25% 12.5%)
- tiles it with size 512 pixels 
- compresses the file by using the lossless zlib compression 
- save it as pyr_final_image.ome.tif.

For my use case, I used a tumor image: 13'500 x 14'000 x 49 channels of original size 18.7 GB.
This file I cannot load directly into QuPath so it is a good use case to see if --pyramidal works.
The created compressed tiled pyramidal image was 15 GB compared to 27GB if I had done uncompressed tiled pyramidal. 
This process is quite lengthy though on a 64 GB computer. It took 28 minutes to do the whole step for the original 18.7 GB image so if you are working with larger images, do not be surprised.
The RAM used during this whole process was around 27GB and as the registration process required more RAM than that, I would say: if you can do the registration, you can also create the compressed file with the same computer/server. 

**Can I do another type of image registration?**

The image registration is done thanks to pystackreg library. In this code, RIGID_BODY (translation + rotation) is hard coded as it is the most consistent. However you can do simple translation, scaling or scaling + shear. 
If you want to change the registration process you need to access the script **registration.py** and modify in **line 250** and **line 363**: **sr = StackReg(StackReg.RIGID_BODY)** replace RIGID_BODY with: TRANSLATION, SCALED_ROTATION or AFFINE.
See https://pystackreg.readthedocs.io/en/latest/ for more information on the registration process.

**When running installLib.py or installLibUser.py, I am getting the following error**

```
Collecting aicspylibczi
Could not find a version that satisfies the requirement aicspylibczi (from versions: )
No matching distribution found for aicspylibczi
```
**How can I solve this?**

This is due to a version problem of your linux system or python. The easiest way to solve this is to have a miniconda environment or you can manually install it. For more details about this problem, please look at this ticket that I opened for the same issue:
https://github.com/AllenCellModeling/aicspylibczi/issues/82
