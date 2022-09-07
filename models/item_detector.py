import cv2
import numpy as np
from pathlib import Path
import urcv

from maptroid.icons import get_icons

WAIT_TIMES = {
    # wait time must be longer for vitality since player can go through doors
    'vidality': 300,
    # y-faster-2-fast has 1/3 second item prompts
    'y-faster-2-fast': 30,
    'y-faster': 30,
}

Y_DUPES = ['wave-beam', 'space-jump', 'spazer-beam', 'x-ray', 'speed-booster', 'grappling-beam', 'plasma-beam', 'varia-suit', 'screw-attack', 'gravity-suit', 'spring-ball', 'hi-jump-boots', 'ice-beam']

class ItemDetector:
    def __init__(self, video):
        self.add_items = False
        self.video = video
        self.items = []
        self.item_frames = []
        self.false_items = []
        self.false_frames = []

    def check(self):
        index = self.video._index

        if index < self.video.data.get('start', 0):
            return

        if index > self.video.data.get('end', 1e15):
            return

        item_index = self._check_current_frame()
        if item_index is None:
            return
        game = self.video.get_game_content()
        matched_item = self.video.matcher.match_item(game.copy())
        if not matched_item and self.can_add_item(item_index):
            matched_item = self.video.matcher.add_item(game.copy())
        if matched_item:
            if not matched_item.startswith('__'):
                # '__' are used for zone changes in vitality
                self.items.append([item_index, matched_item])
                self.item_frames.append(self.video._frame_image)
            wait = WAIT_TIMES.get(self.video.data['world'], 200)
            if self.video.data['world'].startswith('y-faster-2') and matched_item in Y_DUPES:
                print(matched_item, 'is in dupes')
                # some items are on screen longer in y-faster
                wait = 180
            self.video._next_item_check = index + wait
        else:
            self.false_items.append(index)
            self.false_frames.append(self.video._frame_image)
            self.video._next_item_check = index + 10

    def can_add_item(self, index):
        if isinstance(self.add_items, int):
            return abs(self.add_items -index) < 100
        return self.add_items

    def _check_current_frame(self):
        video = self.video
        window = 20
        if self.video.data['world'].startswith('y-faster'):
            window = 6
        index = video._index

        if index < video._next_item_check:
            # last item was too recent
            return None

        std_means = np.std(video.data['means'][index - window:index])
        sums = video.data['sums'][index-1]
        deltas = video.data['deltas'][index-1]

        if video.data['world'] == 'vitality':
            # vitality is a much simpler case since it only displays the item in the top left corner
            item_box = video.matcher.get_item_box()
            _ret, threshed = cv2.threshold(item_box, 92, 255, cv2.THRESH_BINARY)
            np_sum = np.sum(threshed) / 255
            _, _, w, h = video.matcher.data['coords']['item_bounds']
            if np_sum > 100 and np_sum < w * h:
                return index
            return None

        if std_means < 0.15 and sums > 20 and deltas < 20:
            return index - window

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
        cv2.imwrite(str(root / '__processed__.png'), self.video.matcher.prep_image(stacked))
