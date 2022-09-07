import cv2
import numpy as np
from pathlib import Path
from unrest.utils import JsonCache
import urcv
import tkinter as tk
from tkinter import simpledialog

from game.ypx import hash_start

class EmptyTextError(Exception):
    pass

# Taken from y-faster's missiles
ITEM_BOUNDS = [18, 53, 265, 79]


class Matcher:
    def __init__(self, slug, video):
        self.slug = slug
        self.video = video
        self._dir = Path(f'templates/{slug}')
        self._dir.mkdir(exist_ok=True)

        self._originals = self._dir / 'originals'
        self._originals.mkdir(exist_ok=True)

        self._cropped = self._dir / 'cropped'
        self._cropped.mkdir(exist_ok=True)
        self.start_hash = None

        self.data = JsonCache(self._dir / 'data.json', {
            'item': {},
            'ui': {},
            'coords': {},
        })
        self.cache = {}
        for type_ in ['item', 'ui']:
            for name in self.data[type_].keys():
                self.load_cache(type_, name)
        self._root = None
        self._item_box_index = None
        self._item_box = None

    def load_cache(self, type_, name):
        key = f'{type_}__{name}'
        img = cv2.imread(str(self._cropped / f'{key}.png'))
        self.cache[key] = self.prep_image(img)

    def prep_image(self, image):
        if self.slug == 'vitality':
            gray = self.get_item_box()
        else:
            image = urcv.transform.crop(image, ITEM_BOUNDS)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        threshold = 92 if self.slug == 'vitality' else 20
        _ret, image = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)
        image = cv2.blur(image, (3, 3))
        return image

    def match_item(self, image):
        gray = self.prep_image(image)
        max_val = 0
        max_loc = None
        max_item = None
        for item_name in self.data['item'].keys():
            template = self.cache[f'item__{item_name}']
            result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            _, val, _, loc = cv2.minMaxLoc(result)
            if val > 0.90 and val > max_val:
                max_val = val
                max_loc = loc
                max_item = item_name
        return max_item

    def prompt(self, text):
        self._root = self._root or tk.Tk()
        self._root.withdraw()
        prompt = text +"\n(cancel=exit,empty=error)"
        value = simpledialog.askstring(title="Test", prompt=prompt)
        if value is None:
            exit()
        if not value:
            raise EmptyTextError("No text was provided")
        return value

    def add_item(self, image):
        if self.slug == 'vitality':
            image = self.get_item_box()
            cropped, bounds = urcv.transform.autocrop_zeros(image, return_bounds=True)
            cv2.imshow('image', image)
            cv2.imshow('cropped (c to confirm, other to cancel)', cropped)
            if urcv.wait_key() != 'c':
                return
        else:
            bounds = urcv.get_scaled_roi(image, 4, "Highlight item")
            _, _, w, h = bounds
            if w * h == 0:
                return
            cropped = urcv.transform.crop(image, bounds)

        item_name = self.prompt("Enter item name")
        self.data['item'][item_name] = bounds
        cv2.imwrite(str(self._originals / f'item__{item_name}.png'), image)
        cv2.imwrite(str(self._cropped / f'item__{item_name}.png'), cropped)
        self.load_cache('item', item_name)
        cached_4 = urcv.transform.scale(self.cache[f'item__{item_name}'], 4)
        cv2.imshow('cropped 4x scale (x to exit w/o save)', cached_4)
        if urcv.wait_key() == 'x':
            exit()
        self.data._save()
        return item_name

    def get_coords(self, key, image):
        if slug not in self.data['coords']:
            self.data['coords'][key] = urcv.input.get_exact_roi(
                lambda: self.grab(),
                f"Select coords for {key}",
            )
            self.data._save()
        return self.data['coords'][key]

    def save_start(self, image):
        path = f'{self._dir}/start.png'
        self.data['start'] = path
        cv2.imwrite(path, image)

    def detect_start(self, video):
        video.get_game_content()
        image = video._raw_image
        if not 'start' in self.data:
            return False
        if self.start_hash is None:
            world_start = cv2.imread(self.data['start'])
            self.start_hash = hash_start(world_start)
        _hash = hash_start(image)

        return _hash - self.start_hash < 5

    def get_item_box(self):
        # currently used for vitality
        index = self.video._index
        if self._item_box_index != index:
            item_bounds = self.video.matcher.data['coords']['item_bounds']
            item_box = urcv.transform.crop(self.video.get_hud_content(), item_bounds)
            self._item_box = item_box
            self._item_box_index = index
        return self._item_box

    def get_max_item_bounds(self):
        # look at all the item coords and return coords that would contain the all
        # I believe this is just the missile box since it's the biggest
        x1s = []
        y1s = []
        x2s = []
        y2s = []
        for x1, y1, w, h in self.data['item'].values():
            x1s.append(x1)
            y1s.append(y1)
            x2s.append(w)
            y2s.append(h)

        return [min(x1s), min(y1s), max(x2s), max(y2s)]
