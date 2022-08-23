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
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        self.cache[key] = img

    def match_item(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        for item_name in self.data['item'].keys():
            template = self.cache[f'item__{item_name}']
            coords = list(urcv.template.match(gray, template))
            if coords:
                return item_name


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
        bounds = urcv.get_scaled_roi(image, 2, "Highlight item")
        _, _, w, h = bounds
        if w * h == 0:
            return
        item_name = self.prompt("Enter item name")
        cropped = urcv.transform.crop(image, bounds)
        self.data['item'][item_name] = bounds
        cv2.imwrite(str(self._originals / f'item__{item_name}.png'), image)
        cv2.imwrite(str(self._cropped / f'item__{item_name}.png'), cropped)
        self.load_cache('item', item_name)
        cv2.imshow('cropped (x to exit w/ save)', self.cache[f'item__{item_name}'])
        if urcv.wait_key() == 'x':
            exit()
        self.data._save()
        return item_name
