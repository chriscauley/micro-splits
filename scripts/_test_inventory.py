import _setup

import cv2
import urcv

from models.inventory import get_inventory_image

image = get_inventory_image(
    ['missile', 'missile', 'energy-tank', 'missile'],
    names=["energy-tank", "super-missile", "speed-booster", "spring-ball", "reserve-tank"],
)

cv2.imshow('image', image)
urcv.wait_key()