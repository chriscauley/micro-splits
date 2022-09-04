import _setup
import cv2
import numpy as np
from pathlib import Path
import sys
import time
import typer
import urcv

import args
from models import Matcher, Video
from maptroid.icons import get_icons


def check_current_frame(video, items):
    window = 20
    index = video._index
    if index < video._next_item_check:
        # last item was too recent
        return False
    std_means = np.std(video.data['means'][index - window:index])
    sums = video.data['sums'][index-1]
    deltas = video.data['deltas'][index-1]
    if std_means < 0.1 and sums > 20 and deltas < 20:
        return index - window


class ItemDetector:
    def __init__(self, video):
        self.add_items = False # TODO
        self.video = video
        self.items = []
        self.item_frames = []
        self.false_items = []
        self.false_frames = []

    def check(self):
        index = self.video._index

        item_index = check_current_frame(self.video, self.items)
        if item_index:
            game = self.video.get_game_content()
            matched_item = self.video.matcher.match_item(game)
            if not matched_item and self.add_items:
                matched_item = self.video.matcher.add_item(game)
            if matched_item:
                self.items.append([item_index, matched_item])
                self.item_frames.append(self.video.get_game_content())
                self.video._next_item_check = index + 200
            else:
                self.false_items.append(index)
                self.false_frames.append(self.video.get_game_content())
                self.video._next_item_check = index + 10

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

        paths = []
        for index, frame in zip(self.false_items, self.false_frames):
            path = str(root / f'{index}.png')
            paths.append(path)
            cv2.imwrite(path, frame)
        cv2.imwrite(str(root / '__all__.png'), urcv.stack.many(self.false_frames))
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
            urcv.text.write(frame, f'{index} {item}')
            marked_frames.append(frame)
        cv2.imwrite(str(root / '__all__.png'), urcv.stack.many(marked_frames))

def main(
        video_path = args.video_path,
        add_items: bool = args.add_items,
):
    video = Video(video_path)
    video._next_item_check = 0

    detector = ItemDetector(video)

    video.each_frame(detector.check)
    detector.finalize()

    item_count = len(detector.items)
    false_count = len(detector.false_frames)
    print(f'Video has {item_count} items and {false_count} false positives')

if __name__ == "__main__":
    typer.run(main)
