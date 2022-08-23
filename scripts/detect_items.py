import _setup
import cv2
import numpy as np
import sys
import time
import typer
import urcv

import args
from models import Matcher, Video

def detect_item(video, items):
    window = 20
    index = video._index
    if index < video.data['start']:
        # video hasn't started yet
        return False

    if index - video._last_item < 200:
        # last item was too recent
        return False

    if index >= len(video.data['sums']):
        # TODO sometimes sums is one index too short... why?
        return False
    std_means = np.std(video.data['means'][index - window:index])
    sums = video.data['sums'][index]
    deltas = video.data['deltas'][index]
    if std_means < 0.005 and sums > 20 and deltas < 20:
        return index - window

def main(video_path=args.video_path):
    video = Video(video_path)
    video._last_item = 0
    video.matcher = Matcher(video.data['world'])

    items = []
    false_items = []

    def each_func():
        index = video._index

        # TODO this was previously used to skip over false items rather than prompting the user
        # if index in false_items:
        #     video._last_item = index
        #     item_index = None
        # else:

        item_index = detect_item(video, items)
        if item_index:
            game = video.get_game_content()
            matched_item = video.matcher.match_item(game)
            if not matched_item:
                matched_item = video.matcher.add_item(game)
            if matched_item:
                items.append([item_index, matched_item])
            else:
                false_items.append(index)
            video._last_item = index

    video.each_frame(each_func)
    video.data['false_items'] = false_items
    video.data['items'] = items

if __name__ == "__main__":
    typer.run(main)
