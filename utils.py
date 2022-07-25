import cv2
import json
import numpy as np

def div0( a, b, fill=0 ):
    """ a / b, divide by 0 -> `fill`
        div0( [-1, 0, 1], 0, fill=np.nan) -> [nan nan nan]
        div0( 1, 0, fill=np.inf ) -> inf
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        c = np.true_divide( a, b )
    if np.isscalar( c ):
        return c if np.isfinite( c ) else fill
    else:
        c[ ~ np.isfinite( c )] = fill
        return c

def compare26(img1, img2):
    w = 18
    h = 16
    H, W = img1.shape[:2]
    for ix in range(int(W/w)):
        for iy in range(int(H/h)):
            pass


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        return json.JSONEncoder.default(self, obj)

def moving_average(x, w=10):
    return np.convolve(x, np.ones(w), 'valid') / w