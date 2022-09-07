import cv2
import numpy as np
import urcv

from maptroid.utils import ahash

def hash_start(image):
    cropped = urcv.transform.crop(image, (0,20,74,10))
    return ahash(cropped)
