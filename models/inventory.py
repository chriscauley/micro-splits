from collections import defaultdict
import cv2
import math
import numpy as np

import urcv

from maptroid.icons import get_icons


def get_video_inventory_image(video, current_index=None):
    if current_index is None:
        current_index = video._index
    items = [
        item for index, item in video.data['items']
        if index <= current_index
    ]
    return get_inventory_image(items)


def get_inventory_image(items, cols=2, names=[]):
    icons = {
        **get_icons('items'),
        **get_icons('custom-items'),
    }
    gray_icons = {}
    for key, icon in icons.items():
        icon = cv2.cvtColor(icon, cv2.COLOR_BGRA2GRAY)
        icon = cv2.cvtColor(icon, cv2.COLOR_GRAY2BGRA)
        icon = icon * 0.5
        gray_icons[key] = icon
    item_counts = defaultdict(int)

    for name in names:
        # these will be grey if zero
        # will also determine the order
        item_counts[name] = 0

    for item in items:
        item_counts[item] += 1

    rows = math.ceil(len(item_counts) / cols)
    cols = max(cols, 1)
    rows = max(rows, 1)
    scale = 4
    per_icon = 16
    _buffer = 1
    W = (per_icon + _buffer) * cols - _buffer
    H = (per_icon + _buffer) * rows - _buffer
    image = np.zeros((H, W, 4), dtype=np.uint8)
    image[:,:,3] = 255
    counts = []

    for index, (item, count) in enumerate(item_counts.items()):
        x = (index % cols) * (per_icon + _buffer)
        y = (index // cols) * (per_icon + _buffer)
        _icons = icons if count else gray_icons
        urcv.draw.paste(image, _icons.get(item, icons['beam-combo']), x, y)
        if count > 1:
            counts.append([x, y, count])
    image = urcv.transform.scale(image, scale)

    for x, y, count in counts:
        x = (x + per_icon) * scale
        y = (y + per_icon) * scale
        w, h = urcv.text.write(
            image,
            count,
            pos=(x, y),
            align="bottom right",
            bg_color=(0,0,0),
        )

    return image