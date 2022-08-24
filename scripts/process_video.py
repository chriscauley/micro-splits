import _setup
import cv2
import numpy as np
import sys
import time
import typer
import urcv

import args
from configure_video import configure_video
from detect_items import detect_items
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

def main(video_path=args.video_path):
    video = Video(video_path)

    while 'start' not in video.data or 'world' not in video.data:
        print("Video not configured. Please specify (s)tart, game (b)ounds, and specify world.")
        configure_video(video_path)
        video = Video(video_path)
        cv2.destroyAllWindows()

    video._last_item = 0
    video._last_game = None
    means = []
    sums = []
    deltas = []

    start = time.time()
    matcher = Matcher(video.data['world'])
    cap = video.cap
    def each_func():
        hud = video.get_hud_content()
        game = video.get_game_content()
        index = video._index

        summed_game, delta, summed_delta = process(game, video._last_game)

        means.append(game.mean())
        sums.append(np.sum(summed_game))
        deltas.append(np.sum(summed_delta))
        video._last_game = game

    video.each_frame(each_func)

    video.data['sums'] = sums
    video.data['means'] = means
    video.data['deltas'] = deltas
    detect_items(video_path)

if __name__ == "__main__":
    typer.run(main)