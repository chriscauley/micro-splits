import _setup
import cv2
import sys
import typer
import urcv

from models import Video


def main(video_path):
    video = Video(video_path)
    while True:

        if not video.seeking:
            cv2.imshow('hud', video.get_hud_content())
            cv2.imshow('game', video.get_game_content())
            game = video.get_game_content()
        pressed = video.wait_key()
        if pressed == 'q':
            break

if __name__ == "__main__":
    typer.run(main)