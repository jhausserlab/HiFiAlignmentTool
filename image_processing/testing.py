import numpy as np
import numpy as np
from skimage import data, io
from skimage.registration import phase_cross_correlation # new form of register_translation
from scipy.ndimage import shift
import napari
import glob
import gc
import sys

from aicsimageio import AICSImage
import tifffile


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
    
def get_tiffiles(source):
    return glob.glob(source + '/**/*.tif', recursive=True)

def list_files(source, files):
    file_names = '\n'.join(files)
    file_list = f'''Found the following image files in {source}: \n\n{file_names}\n'''
    print(file_list)

def get_max_shape():
    filepath = './output/images_shape.txt'
    file = open(filepath,'r')
    images_shape = file.read()
    split = images_shape.split(';')
    xmax = 0
    ymax = 0
    print(split)
    #print('------------------------',xmax,ymax)
    for i in range(len(split)-1):
        print(i)
        frag = split[i].split(',')
        print(frag)
        xmax = max(xmax,int(frag[1]))
        ymax = max(ymax,int(frag[2]))
        print('------------------------',xmax,ymax)
        
    return xmax,ymax

## align images based on the first dapi provided

def align_images(dapi_target, processed_tif):

    aligned_images = []

    #dapi_target = processed_tif0[-1]
    dapi_to_offset = processed_tif[-1]
    print('dapi_target shape', np.shape(dapi_target))
    print('dapi_to_offset shape', np.shape(dapi_to_offset))

    xmax, ymax = get_max_shape()

    print('Recalibrating image size to', xmax, ymax)
    x0_diff = xmax - np.shape(dapi_target)[0]
    y0_diff = ymax - np.shape(dapi_target)[1]
    
    xi_diff = xmax - np.shape(dapi_to_offset)[0]
    yi_diff = ymax - np.shape(dapi_to_offset)[1]

    max_dapi_target = np.pad(dapi_target,((int(np.floor((x0_diff)/2)), int(np.ceil((x0_diff)/2)))
               ,(int(np.floor((y0_diff)/2)), int(np.ceil((y0_diff)/2)))),'constant')
    #padding of dapi_to_offset, calling it max_processed_tif to keep variables low
    max_processed_tif = np.pad(dapi_to_offset,((int(np.floor((xi_diff)/2)), int(np.ceil((xi_diff)/2)))
               ,(int(np.floor((yi_diff)/2)), int(np.ceil((yi_diff)/2)))),'constant')

    shifted, error, diffphase = phase_cross_correlation(max_dapi_target, max_processed_tif)
    print(f"Detected subpixel offset (y, x): {shifted}")

    for channel in range(np.shape(processed_tif)[0]):
        max_processed_tif = np.pad(processed_tif[channel,:,:],((int(np.floor((xi_diff)/2)), int(np.ceil((xi_diff)/2)))
                                                   ,(int(np.floor((yi_diff)/2)), int(np.ceil((yi_diff)/2))))
                                   ,'constant')
        aligned_images.append(shift(max_processed_tif, shift=(shifted[0], shifted[1]), mode='constant'))
    print('transformed channels done, image is of size', np.shape(aligned_images))
    return aligned_images

def get_aligned_images(source):
    # source needs to be a str of where are the tif stored
    files = get_tiffiles(source)
    list_files(source,files)
    
    ask_for_approval()

    print ('Reference dapi is from:', files[0].split())
    processed_tif0 = tifffile.imread(files[0].split())
    dapi_target = processed_tif0[-1]
    #Do not need processed_tif0 only dapi_target from it
    del processed_tif0
    gc.collect()
    
    for file in files[1:]:
        print('--- Aligning tif i:', file.split())
        processed_tif = tifffile.imread(file.split())
        print('Shape of image i is: ', np.shape(processed_tif))
        align_tif = align_images(dapi_target, processed_tif)
        print('Saving aligned image')
        with tifffile.TiffWriter('./aligned/aligned'+files[0].split()[0].split('/')[2].split('.')[0]+'.tif',
                                 bigtiff = True) as tif:
            tif.save(align_tif)


source = './output'
get_aligned_images(source)