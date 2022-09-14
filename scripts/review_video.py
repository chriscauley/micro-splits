import _setup
import cv2
import numpy as np
import sys
import typer
import urcv

from scripts.process_video import process
from models import Video
from models.inventory import get_video_inventory_image
from utils import show_plot

PLOT_LEN = 50


def get_next_item(video):
    for item_index, item_name in video.data['items']:
        if item_index > video._index:
            return item_index, item_name
    return 0, None

def watch_func(video):
    if video._index > 0:
        video._index -= 1
        video._index += 1
    game = video.get_game_content().copy()

    index = video._index

    cv2.imshow('inventory', get_video_inventory_image(video))

    i_start = max(0, index - PLOT_LEN)

    game_copy = game.copy()
    max_index = video.get_max_index()
    percent = round(100 * index / max_index, 2)
    urcv.text.write(game_copy, index, pos="bottom")
    urcv.text.write(game_copy, f'{percent}%', pos="bottom right")

    next_index, next_item = get_next_item(video)
    frame = urcv.transform.scale(video._frame_image, 2)
    if next_item:
        urcv.text.write(frame, f'{next_index-index}: {next_item}')
    else:
        max_index = video.get_max_index()
        urcv.text.write(frame, f'{max_index-index}: end')

    cv2.imshow('frame', frame)


def pressed_func(video, key):
    if key == 'i':
        video.template_matcher.add_item(video.get_game_content())


def main(video_path=typer.Argument(None, help="path to mkv file to analyze.")):
    video = Video(video_path)
    video.watch(watch_func, pressed_func)

if __name__ == "__main__":
    typer.run(main)