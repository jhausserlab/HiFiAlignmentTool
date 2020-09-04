import cv2
import numpy as np
from skimage.feature import ORB, match_descriptors, plot_matches
from skimage.transform import ProjectiveTransform, SimilarityTransform, warp
from skimage.measure import ransac

## align images based on the first dapi provided
def align_images(processed_czis):
  aligned_images = []
  for czi in processed_czis:
    print('len a', len(aligned_images))
    if len(aligned_images):
      print('align images')
      orb = ORB(n_keypoints=500, fast_threshold=0.05)

      orb.detect_and_extract(aligned_images[0][-1])
      keypoints1 = orb.keypoints
      descriptors1 = orb.descriptors

      orb.detect_and_extract(czi[-1])
      keypoints2 = orb.keypoints
      descriptors2 = orb.descriptors

      matches12 = match_descriptors(descriptors1, descriptors2, cross_check=True)
      src = keypoints2[matches12[:, 1]][:, ::-1]
      dst = keypoints1[matches12[:, 0]][:, ::-1]

      model_robust, inliers = ransac((src, dst), SimilarityTransform,
                                     min_samples=10, residual_threshold=1, max_trials=300)

      alignedCzi = []

      for channel in czi:
        print('channel size', np.shape(channel))

        image1_ = aligned_images[0][-1]
        output_shape = aligned_images[0][-1].shape

        image2_warp = warp(channel, model_robust.inverse, preserve_range=True,
                       output_shape=output_shape, cval=-1)

        print('image2_ 1', (type(image2_warp)))
        image2_ = np.ma.array(image2_warp, mask=image2_warp==-1)

        print('image2_ 1', (type(image2_)))
        alignedCzi.append(image2_)

      print('transformed channels done')
      aligned_images.append(alignedCzi)

    else:
      aligned_images.append(czi)

  return aligned_images
