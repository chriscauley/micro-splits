import cv2
import numpy as np
from pathlib import Path
import tkinter as tk
from tkinter import simpledialog
import urcv
from unrest.utils import JsonCache
from maptroid.icons import get_icons


BOUNDS_BY_WORLD = {
    'vitality': [9, 0, 121, 14],
    'DEFAULT': [28, 70, 246, 50]
}

MIN_BOUNDS_BY_WORLD = {
    'vitality': [9, 0, 121, 14],
    'DEFAULT': [114, 64, 72, 60]
}

THRESH_BY_WORLD = {
    'vitality': 20,
    'DEFAULT': 92,
}

class TemplateMatcher:
    def __init__(self, video):
        self._current_pink_streak = 0
        self._current_item = None
        self._add_items = False # enable to prompt user for unknown items
        self._root = None
        self.items = []
        self.item_frames = []
        self.false_items = []
        self.false_frames = []

        self.video = video
        world = self.world = video.data.get('world')
        self._dir = Path(f'templates/{world}')
        self._dir.mkdir(exist_ok=True)

        self._originals = self._dir / 'originals'
        self._originals.mkdir(exist_ok=True)

        self._cropped = self._dir / 'cropped'
        self._cropped.mkdir(exist_ok=True)
        self.start_hash = None
        self.item_box_bounds = BOUNDS_BY_WORLD.get('world', BOUNDS_BY_WORLD['DEFAULT'])
        self.thresh = THRESH_BY_WORLD.get('world', THRESH_BY_WORLD['DEFAULT'])

        self.data = JsonCache(self._dir / 'data.json', {
            'item': {},
            'ui': {},
            'coords': {},
        })
        self.cache = {}
        for type_ in ['item', 'ui']:
            for name in self.data[type_].keys():
                self.load_cache(type_, name)


    def load_cache(self, type_, name):
        key = f'{type_}__{name}'
        img = cv2.imread(str(self._originals / f'{key}.png'))
        self.cache[key] = self.prep_image_for_match(img, self.data[type_][name])

    def check_pink(self, image):
        bounds = MIN_BOUNDS_BY_WORLD.get('world', MIN_BOUNDS_BY_WORLD['DEFAULT'])
        item_box = urcv.transform.crop(image, bounds)
        _ret, cymak = cv2.threshold(item_box, self.thresh, 255, cv2.THRESH_BINARY)
        upper = lower = (255, 0, 255)
        magenta = cv2.inRange(cymak, lower, upper)
        # magenta = cymak
        mode = 'off'
        streak = 0
        values = [np.sum(magenta[y]) > 0 for y in range(magenta.shape[0])]
        streaks = []
        i = 0
        while i < len(values):
            # get to first non-empty row
            if values[i]:
                i += 1
            else:
                break
        while i < len(values):
            off_streak = 0
            on_streak = 0
            while i < len(values) and not values[i]:
                # measure time off
                off_streak += 1
                i += 1
            while i < len(values) and values[i]:
                # measure time off
                on_streak += 1
                i += 1
            streaks.append(off_streak)
            streaks.append(on_streak)

        if len(streaks) > 2:
            for i in range(len(streaks) - 2):
                a, b, c = streaks[i:i+3]
                if a >= 8 and b >= 4 and c >= 8:
                    # one line of pink text
                    self._current_pink_streak += 1
                    return self._current_pink_streak > 5

        if len(streaks) > 4:
            for i in range(len(streaks) - 4):
                a, b, c, d, e = streaks[i:i+5]
                if a >= 8 and b >= 4 and c < 4 and d >=4 and e >= 8:
                    # two lines of pink text
                    self._current_pink_streak += 1
                    return self._current_pink_streak > 5

        self._current_pink_streak = 0
        return False

    def get_item_box(self, image):
        return urcv.transform.crop(image, self.item_box_bounds)

    def check_item(self):
        image = self.video.get_game_content()
        if self.check_pink(image):
            if self._current_item:
                # previous item is still on screen
                return
            matched_item = self.get_matched_item(image)
            if self.should_add_item(matched_item):
                matched_item = self.add_item(image)
            if matched_item:
                if not matched_item.startswith('__'):
                    # '__' are used for zone changes in vitality
                    self.items.append([self.video._index, matched_item])
                    self.item_frames.append(self.video._frame_image)
            else:
                self.false_items.append(self.video._index)
                self.false_frames.append(self.video._frame_image)
                self._current_pink_streak = 0
            self._current_item = matched_item
        else:
            self._current_item = None

    def should_add_item(self, matched_item):
        # setting _add_items to an integer forces that item to be added no matter what
        if type(self._add_items) == int:
            return abs(self._add_items - self.video._index) < 100
        return not matched_item and self._add_items

    def prep_image_for_match(self, image, bounds=None):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _ret, mask = cv2.threshold(gray, self.thresh, 255, cv2.THRESH_BINARY)
        threshed = cv2.bitwise_and(gray, gray, mask=mask)

        if bounds is None:
            # templates will supply their own bounds, targets will be cropped to item box bounds
            bounds = self.item_box_bounds

        cropped = urcv.transform.crop(threshed, bounds)
        return cv2.blur(cropped, (3, 3))

    def get_matched_item(self, image):
        gray = self.prep_image_for_match(image)
        max_val = 0
        max_loc = None
        max_item = None
        close_calls = []
        for item_name in self.data['item'].keys():
            template = self.cache[f'item__{item_name}']
            result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            _, val, _, loc = cv2.minMaxLoc(result)
            if val > 0.8 and val < 0.9:
                close_calls.append([item_name, val])
            if val > max_val:
                max_val = val
                max_loc = loc
                max_item = item_name
        if close_calls:
            print('had close calls, went with:', max_item, max_val)
            print(close_calls)
        if max_val > 0.9:
            return max_item
        print('no luck, closest was', max_val, max_item)
        return None

    def add_item(self, image, item_name=None):
        if self.world == 'vitality':
            image = self.get_item_box()
            cropped, bounds = urcv.transform.autocrop_zeros(image, return_bounds=True)
            if urcv.wait_key() != 'c':
                return
        else:
            bounds = urcv.get_scaled_roi(image, 4, "Highlight item")
            _, _, w, h = bounds
            if w * h == 0:
                return
            cropped = urcv.transform.crop(image, bounds)

        item_name = item_name or self.prompt("Enter item name")
        self.data['item'][item_name] = bounds
        cv2.imwrite(str(self._originals / f'item__{item_name}.png'), image)
        cv2.imwrite(str(self._cropped / f'item__{item_name}.png'), cropped)
        self.load_cache('item', item_name)
        cached_4 = urcv.transform.scale(self.cache[f'item__{item_name}'], 4)
        cv2.imshow('image', image)
        cv2.imshow('cropped (c to confirm, other to cancel)', cached_4)
        if urcv.wait_key() == 'x':
            exit()
        self.data._save()
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

    def finalize(self):
        self.video.data['items'] = self.items
        self._save_false_items()
        self._save_item_frames()

    def _save_false_items(self):
        video_name = self.video.data.get('video_name')
        root = Path(f'.data/{video_name}/false_items')
        root.mkdir(exist_ok=True, parents=True)
        for f in root.iterdir():
            if str(f).endswith('png'):
                f.unlink()

        if not self.false_frames:
            return

        stack = []
        for index, frame in zip(self.false_items, self.false_frames):
            frame = frame.copy()
            urcv.text.write(frame, index, pos=(0, 40))
            stack.append(frame)
        chuncks = int(np.ceil(len(stack) / 25))
        for i in range(chuncks):
            start = i * 25
            end = min((i + 1) * 25, len(stack))
            print(start, end)
            cv2.imwrite(str(root / f'{start}-{end}.png'), urcv.stack.many(stack[start:end]))
        self.video.data['false_frames'] = self.false_items

    def _save_item_frames(self):
        icons = {
            **get_icons('items', _cvt=cv2.COLOR_BGRA2BGR, scale=2),
            **get_icons('custom-items', _cvt=cv2.COLOR_BGRA2BGR, scale=2),
        }
        video_name = self.video.file_path.split('/')[-1]
        root = Path(f'.data/{video_name}/items')
        root.mkdir(exist_ok=True, parents=True)
        marked_frames = []
        for (index, item), frame in zip(self.items, self.item_frames):
            frame = frame.copy()
            cv2.imwrite(str(root / f'{index}.png'), frame)
            icon = icons.get(item, icons['beam-combo'])
            urcv.draw.paste(frame, icon, 50, 80)
            urcv.text.write(frame, f'{index} {item}', pos=(0, 40))
            marked_frames.append(frame)
        stacked = urcv.stack.many(marked_frames)
        cv2.imwrite(str(root / '__all__.png'), stacked)
