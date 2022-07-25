import _setup
import cv2
import numpy as np
import sys
import typer
import urcv

from models import Video

def show_hues(image, visible_range):
    return spectrum, filtered

def main(
        video_path=typer.Argument(None, help="path to mkv file to analyze."),
        visible_range=typer.Argument('0,360', help="max,min degrees of hue to show."),
):
    video = Video(video_path)
    visible_range = [int(i) for i in visible_range.split(',')]

    while True:
        if not video.seeking:
            game = video.get_game_content()

            # Start by extracting only pixels brighter than a given value
            gray = cv2.cvtColor(game, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 144, 255, cv2.THRESH_BINARY)
            masked = cv2.bitwise_and(game, game, mask=thresh)

            # get the full spectrum
            hsv = cv2.cvtColor(masked, cv2.COLOR_BGR2HSV)
            images, ranges = urcv.hsv.scan_hue(hsv, 36, saturation=[0, 255], value=[0,255])
            spectrum = urcv.stack.many(images, border=[255, 0, 255], text=[str(r) for r in ranges])
            spectrum = cv2.cvtColor(spectrum, cv2.COLOR_HSV2BGR)

            # create a separate image of only the visible range
            filtered = urcv.hsv.filter(hsv, hue=visible_range)
            filtered = cv2.cvtColor(filtered, cv2.COLOR_HSV2BGR)

            # display images
            cv2.imshow('spectrum', spectrum)
            stack = urcv.transform.scale(np.hstack([game, masked, filtered]), 2)
            urcv.text.write(stack, video._index)
            cv2.imshow('game, masked, filtered', stack)

        pressed = video.wait_key()
        if pressed == 'q':
            break

if __name__ == "__main__":
    typer.run(main)