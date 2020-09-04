from registration import CrossCorr

## align images based on the first dapi provided
def align_images(processed_czis):
  aligned_images = []
  for czi in processed_czis:
    print('len a', len(aligned_images))
    if len(aligned_images):
      print('align images')

      register = CrossCorr()
      model = register.fit(czi[-1], reference=aligned_images[0][-1])

      # the estimated transformations should match the deltas we used
      print(model.transformations)
      print(type(czi))

      alignedCzi = []

      for channel in czi:
        registered = model.transform(channel)
        print(1, (type(registered)))
        alignedCzi.append(registered)
        print(2)

      print(3)
      aligned_images.append(alignedCzi)

    else:
      aligned_images.append(czi)

  return aligned_images
