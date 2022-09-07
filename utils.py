import cv2
import io
import json
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import numpy as np
import urcv

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

def moving_average(x, w=10):
    return np.convolve(x, np.ones(w), 'valid') / w

figure(figsize=(8, 6), dpi=80)
fig, ax = plt.subplots()

def show_plot(datasets, title='plot', cap=0, x_max=None, labels=None):
    if cap:
        datasets = [
            [min(i, cap) for i in dataset]
            for dataset in datasets
        ]

    xs = range(len(datasets[0]))
    if x_max is not None:
        xs = range(x_max - len(datasets[0]), x_max)
    for i, dataset in enumerate(datasets):
        label = None
        if labels:
            label = labels[i]
        plt.plot(xs, dataset, label=label)
    if labels:
        plt.legend()
    with io.BytesIO() as buff:
        fig.savefig(buff, format='raw')
        buff.seek(0)
        data = np.frombuffer(buff.getvalue(), dtype=np.uint8)
    w, h = fig.canvas.get_width_height()
    plt.clf()
    cv2.imshow(title, urcv.transform.scale(data.reshape((int(h), int(w), -1)), 2))


def extract_cymak(image, upper, lower):
    _, thresh = cv2.threshold(image.copy(), 128, 255, cv2.THRESH_BINARY)
    mask = cv2.inRange(thresh, lower, upper)
    return cv2.bitwise_and(thresh, thresh, mask=mask)


def _gray(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def pink_check(game):
    bounds = [110, 75, 80, 42] # bounds were taken from y-faster-2-fast
    cropped_item = urcv.transform.crop(game, bounds)
    upper = np.array([255, 0, 255])
    lower = np.array([0, 0, 255])
    pink_item = _gray(extract_cymak(cropped_item, upper, lower))
    _, thresh = cv2.threshold(pink_item.copy(), 60, 255, cv2.THRESH_BINARY)

    zeros = 0
    ones = 0
    last = 0

    values = np.sum(thresh, axis=1)
    series = [int(v > 2500) for v in values]
    match = [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    for i in range(len(series)-len(match)):
        if series[i:i+len(match)] == match:
            return True

    return False