import _setup
import cv2
import sys
import typer
import urcv

from models import Video


def watch_func(video):
    cv2.imshow('hud', video.get_hud_content())
    cv2.imshow('game', video.get_game_content())


def main(video_path):
    video = Video(video_path)

    video.watch(watch_func)

if __name__ == "__main__":
    typer.run(main)