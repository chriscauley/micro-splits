import _setup
import cv2
import numpy as np
import sys
import time
import typer
import urcv

from models import Video, get_data

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

def main(video_path=typer.Argument(None, help="path to mkv file to analyze.")):
    last_game = None
    means = []
    sums = []
    deltas = []
    start = time.time()

    video = Video(video_path)
    cap = video.cap
    while True:
        if video._index % 1000 == 0:
            print(video._index, '/', video.get_max_index(), int(time.time() - start))
        if video._index >= video.get_max_index():
            break
        hud = video.get_hud_content()
        game = video.get_game_content()
        video._index += 1

        summed_game, delta, summed_delta = process(game, last_game)

        means.append(game.mean())
        sums.append(np.sum(summed_game))
        deltas.append(np.sum(summed_delta))
        last_game = game


    data = get_data(video_path)
    data['sums'] = sums
    data['means'] = means
    data['deltas'] = deltas

if __name__ == "__main__":
    typer.run(main)