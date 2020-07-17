# Microscopy Image Processing Pipeline

## Getting started

see the help

```
python3 main.py --help
```

run by

```
python3 main.py ./path/to/czi_files ./output_folder
```

prototype of using python to stitch together microscopy data

## main architectural improvements

reduce memory use by introducing "streaming" of channels, and calculating all image registrations from the DAPI before loading images

parallelize 

## Caveats
can, as of yet, only work with czi images of the same size (pixel size)
