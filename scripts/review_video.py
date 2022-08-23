import _setup
import cv2
import numpy as np
import sys
import typer
import urcv

from scripts.process_video import process
from models import Video, get_data
from models.inventory import get_video_inventory_image
from utils import show_plot

PLOT_LEN = 1000


def get_next_item(video):
    for item_index, item_name in video.data['items']:
        if item_index > video._index:
            return item_index, item_name
    return 0, None

def watch_func(video):
    last_game = None
    if video._index > 0:
        video._index -= 1
        last_game = video.get_game_content()
        video._index += 1
    game = video.get_game_content().copy()
    summed_game, delta, summed_delta = process(game, last_game)
    # cv2.imshow('game,last_game', urcv.transform.scale(np.vstack([game, last_game]),2))

    index = video._index

    cv2.imshow('inventory', get_video_inventory_image(video))

    i_start = max(0, index - PLOT_LEN)
    deltas = video.data['deltas'][i_start:index+1]
    sums = video.data['sums'][i_start:index+1]
    means = video.data['means'][i_start:index+1]

    game_copy = game.copy()
    max_index = video.get_max_index()
    percent = round(100 * index / max_index, 2)
    urcv.text.write(game_copy, index, pos="bottom")
    urcv.text.write(game_copy, f'{deltas[-1],sums[-1]}')
    urcv.text.write(game_copy, f'{percent}%', pos="bottom right")

    next_index, next_item = get_next_item(video)
    if next_item:
        urcv.text.write(last_game, f'{next_index-index}: {next_item}')
    else:
        max_index = video.get_max_index()
        urcv.text.write(last_game, f'{max_index-index}: end')

    stacked = np.vstack([game_copy, last_game, delta])
    cv2.imshow('game,last_game,delta', urcv.transform.scale(stacked, 1.5))

    summed_delta = np.multiply(255, summed_delta.astype(np.uint8))
    summed_game = np.multiply(255, summed_game.astype(np.uint8))
    # cv2.imshow('sum,delta', urcv.transform.scale(np.vstack([summed_game,summed_delta]), 32))

    datasets = [means, sums, deltas]
    datasets = [d[-PLOT_LEN:] for d in datasets]
    show_plot(datasets, x_max=index, labels=["means", "sums", "deltas"])

def main(video_path=typer.Argument(None, help="path to mkv file to analyze.")):
    video = Video(video_path)
    video.watch(watch_func)

if __name__ == "__main__":
    typer.run(main)