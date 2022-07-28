import _setup
import cv2
import numpy as np
import sys
import typer
import urcv

from scripts.process_video import process
from models import Video, get_data
from utils import show_plot

PLOT_LEN = 1000

def watch_func(video):
    last_game = None
    if video._index > 0:
        video._index -= 1
        last_game = video.get_game_content()
        video._index += 1
    game = video.get_game_content().copy()
    summed_game, delta, summed_delta = process(game, last_game)
    cv2.imshow('game,last_game', urcv.transform.scale(np.vstack([game, last_game]),2))

    index = video._index
    max_index = video.get_max_index()
    urcv.text.write(game, index, pos="bottom")
    percent = round(100 * index / max_index, 2)

    i_start = max(0, index - PLOT_LEN)
    deltas = video.data['deltas'][i_start:index]
    sums = video.data['sums'][i_start:index]
    means = video.data['means'][i_start:index]
    urcv.text.write(game, f'{deltas[-1],sums[-1]}')
    urcv.text.write(game, f'{percent}%', pos="bottom right")

    cv2.imshow('game,delta', urcv.transform.scale(np.vstack([game, delta]),2))

    summed_delta = np.multiply(255, summed_delta.astype(np.uint8))
    summed_game = np.multiply(255, summed_game.astype(np.uint8))
    cv2.imshow('sum,delta', urcv.transform.scale(np.vstack([summed_game,summed_delta]), 32))

    datasets = [sums, deltas, means]
    datasets = [d[-PLOT_LEN:] for d in datasets]
    show_plot(datasets)

def main(video_path=typer.Argument(None, help="path to mkv file to analyze.")):
    video = Video(video_path)
    video.data = get_data(video_path)
    video.watch(watch_func)

if __name__ == "__main__":
    typer.run(main)