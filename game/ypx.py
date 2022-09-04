import cv2
import numpy as np
import urcv

from maptroid.utils import dhash

def hash_start(image):
    kernel = np.ones((3,3),np.uint8)
    cropped = urcv.transform.crop(image, (0,20,74,10))
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    return cropped
