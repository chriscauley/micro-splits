import cv2
import numpy as np
import urcv

from maptroid.utils import dhash

def hash_start(image):
    kernel = np.ones((3,3),np.uint8)

    # Threshing a BGR image gives an image where all 3 chanels are either 0 or 255
    _, thresh = cv2.threshold(image, 90, 255, cv2.THRESH_BINARY)

    # Strip out only the pure yellow channel
    mask = cv2.inRange(thresh, (0,255,254), (0,255,255))
    filtered = cv2.bitwise_and(thresh, thresh, mask=mask)
    return cv2.resize(cv2.morphologyEx(filtered, cv2.MORPH_OPEN, kernel), (16, 16))
