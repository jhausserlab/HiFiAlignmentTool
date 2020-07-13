from skimage.morphology import white_tophat, black_tophat, disk

def subtract_background(image, radius=50, light_bg=False):
  str_el = disk(radius) #you can also use 'ball' here to get a slightly smoother result at the cost of increased computing time

  if light_bg:
    return black_tophat(image, str_el)
  else:
    return white_tophat(image, str_el)
