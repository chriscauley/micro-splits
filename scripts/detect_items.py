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
    if index < video.data['start']:
        # video hasn't started yet
        return False

    if index < video._next_item_check:
        # last item was too recent
        return False

    if index >= len(video.data['sums']):
        # TODO sometimes sums is one index too short... why?
        return False
    std_means = np.std(video.data['means'][index - window:index])
    sums = video.data['sums'][index]
    deltas = video.data['deltas'][index]
    if std_means < 0.1 and sums > 20 and deltas < 20:
        return index - window


def save_false_items(video, false_items, false_frames):
    video_name = video.file_path.split('/')[-1]
    root = Path(f'.data/{video_name}/')
    root.mkdir(exist_ok=True, parents=True)
    for f in root.iterdir():
        if str(f).endswith('png'):
            f.unlink()

    if not false_frames:
        return

    paths = []
    for index, frame in zip(false_items, false_frames):
        path = str(root / f'false_item_{index}.png')
        paths.append(path)
        cv2.imwrite(path, frame)
    cv2.imwrite(str(root / 'all_false_items.png'), urcv.stack.many(false_frames))
    video.data['false_frames'] = paths


def save_item_frames(video, items, item_frames):
    icons = {
        **get_icons('items', _cvt=cv2.COLOR_BGRA2BGR, scale=2),
        **get_icons('custom-items', _cvt=cv2.COLOR_BGRA2BGR, scale=2),
    }
    video_name = video.file_path.split('/')[-1]
    root = Path(f'.data/{video_name}/')
    root.mkdir(exist_ok=True, parents=True)
    marked_frames = []
    for (index, item), frame in zip(items, item_frames):
        frame = frame.copy()
        icon = icons.get(item, icons['beam-combo'])
        urcv.draw.paste(frame, icon, 50, 80)
        urcv.text.write(frame, f'{index} {item}')
        marked_frames.append(frame)
    cv2.imwrite(str(root / 'all_items.png'), urcv.stack.many(marked_frames))


def detect_items(video_path, add_items=False):
    video = Video(video_path)
    video._next_item_check = 0
    video.matcher = Matcher(video.data['world'])

    items = []
    item_frames = []
    false_items = []
    false_frames = []

    def each_func():
        index = video._index

        item_index = check_current_frame(video, items)
        if item_index:
            game = video.get_game_content()
            matched_item = video.matcher.match_item(game)
            if not matched_item and add_items:
                matched_item = video.matcher.add_item(game)
            if matched_item:
                items.append([item_index, matched_item])
                item_frames.append(video.get_game_content())
                video._next_item_check = index + 200
            else:
                false_items.append(index)
                false_frames.append(video.get_game_content())
                video._next_item_check = index + 10

    video.each_frame(each_func)
    video.data['items'] = items
    save_false_items(video, false_items, false_frames)
    save_item_frames(video, items, item_frames)
    print(f'Video has {len(items)} items and {len(false_frames)} false positives')


def main(
        video_path = args.video_path,
        add_items: bool = args.add_items,
):
    detect_items(video_path, add_items)

if __name__ == "__main__":
    typer.run(main)
