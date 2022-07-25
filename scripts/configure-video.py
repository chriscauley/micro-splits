import _setup
import cv2
import sys
import typer
import urcv

from models import Video


def show_hues(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    images, ranges = urcv.hsv.scan_hue(hsv, 48, saturation=[0, 255], value=[0,255])

    result = urcv.stack.many(images, border=[255, 0, 255], text=[str(r) for r in ranges])
    result = cv2.cvtColor(result, cv2.COLOR_HSV2BGR)
    result2 = urcv.hsv.filter(hsv, hue=[11,48])
    result2 = cv2.cvtColor(result2, cv2.COLOR_HSV2BGR)
    result2 = urcv.transform.scale(result2, 4)
    cv2.imshow('result', result)
    cv2.imshow('result2', result2)

def main(video_path):
    video = Video(video_path)
    while True:

        if not video.busy:
            cv2.imshow('hud', video.get_hud_content())
            cv2.imshow('game', video.get_game_content())
            game = video.get_game_content()
            gray = cv2.cvtColor(game, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
            cv2.imshow('thresh', thresh)
            masked = cv2.bitwise_and(game, game, mask=thresh)
            show_hues(masked)
        pressed = video.wait_key()
        if pressed == 'q':
            break

if __name__ == "__main__":
    typer.run(main)