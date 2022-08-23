import _setup
import cv2
import numpy as np
import sys
import time
import typer
import urcv

from models import Matcher, Video

def sumcells(img, size=16):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.dilate(img, np.ones((5, 5), np.uint8))

    H = int(img.shape[0] / size)
    W = int(img.shape[1] / size)

    return cv2.resize(img,(W,H)) > 5

def process(game, last_game):
    if last_game is None:
        # first frame has no last_frame, use first frame
        last_game = game

    summed_game = sumcells(game)
    delta = cv2.add(
        cv2.subtract(game, last_game),
        cv2.subtract(last_game, game)
    )
    summed_delta = sumcells(delta)
    return summed_game, delta, summed_delta

def detect_item(video, means, items):
    index = video._index
    if index < video.data['start']:
        # video hasn't started yet
        return False

    if index - video._last_item < 300:
        # last item was too recent
        return False
    if np.std(means[index - 10:index]) < 0.005 and video.data['sums'][index] > 20:
        return True

def main(video_path=typer.Argument(None, help="path to mkv file to analyze.")):
    last_game = None
    means = []
    sums = []
    deltas = []
    items = []
    start = time.time()

    video = Video(video_path)
    false_items = video.data.get('false_items', [])[:]
    video._last_item = 0
    if 'start' not in video.data or 'world' not in video.data:
        raise ValueError("no start+world detected, run configure")
    matcher = Matcher(video.data['world'])
    cap = video.cap
    while True:
        if video._index % 1000 == 0:
            print(video._index, '/', video.get_max_index(), f'{round(time.time() - start, 2)}s')
        if video._index >= video.get_max_index():
            break
        if video.get_frame(safe=True) is None:
            break
        hud = video.get_hud_content()
        game = video.get_game_content()

        summed_game, delta, summed_delta = process(game, last_game)

        means.append(game.mean())
        sums.append(np.sum(summed_game))
        deltas.append(np.sum(summed_delta))
        if detect_item(video, means, items) and video._index not in false_items:
            matched_item = matcher.match_item(game)
            if not matched_item:
                matched_item = matcher.add_item(game)
            if matched_item:
                items.append(matched_item)
            if matched_item:
                items.append([video._index, matched_item])
            else:
                false_items.append(video._index)
            video._last_item = video._index

        last_game = game
        video._index += 1



    video.data['sums'] = sums
    video.data['means'] = means
    video.data['deltas'] = deltas


if __name__ == "__main__":
    typer.run(main)