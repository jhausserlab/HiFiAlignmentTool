
import napari
from aicsimageio import AICSImage

img = AICSImage("../output/2020-09-04_1599229915072.ome.tif") #../czi/align1.czi   ../align2.czi   ../output/2020-08-27_1598554331997.ome.tif
channel_names = img.get_channel_names()

print(len(channel_names))

with napari.gui_qt():
    viewer = napari.Viewer()
    for c, c_name in enumerate(channel_names):
        viewer.add_image(img.get_image_data("ZYX", C=c, S=0, T=0), 
                         name=c_name)