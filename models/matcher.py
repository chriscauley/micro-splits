import cv2
from pathlib import Path
from unrest.utils import JsonCache
import urcv
import tkinter as tk
from tkinter import simpledialog


class EmptyTextError(Exception):
    pass


class Matcher:
    def __init__(self, slug):
        self.slug = slug
        self._dir = Path(f'templates/{slug}')
        self._dir.mkdir(exist_ok=True)

        self._originals = self._dir / 'originals'
        self._originals.mkdir(exist_ok=True)

        self._cropped = self._dir / 'cropped'
        self._cropped.mkdir(exist_ok=True)

        self.data = JsonCache(self._dir / 'data.json', {
            'item': {},
            'ui': {},
        })
        self.cache = {}
        for type_ in ['item', 'ui']:
            for name in self.data[type_].keys():
                self.load_cache(type_, name)
        self._root = None

    def load_cache(self, type_, name):
        key = f'{type_}__{name}'
        img = cv2.imread(str(self._cropped / f'{key}.png'))
        self.cache[key] = self.prep_image(img)

    def prep_image(self, image):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _ret, image = cv2.threshold(image, 10, 255, cv2.THRESH_BINARY)
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
        bounds = urcv.get_scaled_roi(image, 4, "Highlight item")
        _, _, w, h = bounds
        if w * h == 0:
            return
        item_name = self.prompt("Enter item name")
        cropped = urcv.transform.crop(image, bounds)
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
