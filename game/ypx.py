import cv2
import numpy as np
import urcv

from maptroid.utils import dhash

def hash_start(image):
    kernel = np.ones((3,3),np.uint8)

    # Threshing a BGR image gives an image where all 3 chanels are either 0 or 255
    _, thresh = cv2.threshold(image, 90, 255, cv2.THRESH_BINARY)

    # Strip out only the pure yellow channel
    hsv = cv2.cvtColor(thresh, cv2.COLOR_BGR2HSV)
    filtered = urcv.hsv.filter(hsv, hue=[25,35])
    filtered = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
    return cv2.resize(cv2.morphologyEx(filtered, cv2.MORPH_OPEN, kernel), (16, 16))
