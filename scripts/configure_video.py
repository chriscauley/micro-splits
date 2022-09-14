import _setup
import cv2
import numpy as np
import sys
import typer
import urcv

from models import Video

def show(name, image, scale=2, text=None):
    canvas = urcv.transform.scale(image, scale)
    if text:
        urcv.text.write(canvas, text)
    cv2.imshow(name, canvas)

def get_delta(index, values):
    deltas = [v - index for v in values]
    abs_deltas = [abs(v - index) for v in values]
    min_ = min(abs_deltas)
    return deltas[abs_deltas.index(min_)]

def watch_func(video):
    show('hud', video.get_hud_content())
    game = video.get_game_content()
    if video.data.get('game_bounds', video):
        show('raw', video._raw_image)

    game_text = f'f:{video._index}  '
    if video.data.get('manual_items'):
        delta = get_delta(video._index, video.data['manual_items'])
        game_text += f'i:{delta}  '
    if video.data.get('touched_items'):
        delta = get_delta(video._index, video.data['touched_items'])
        game_text += f't:{delta}'

    # This was used to check vitality item box
    # if video.data.get('world') == 'vitality':
    #     item_box = video.matcher.get_item_box(video)
    #     cv2.imshow('item_box', urcv.transform.scale(item_box, 5))
    #     cv2.imshow('thresh_item_box', urcv.transform.scale(item_box, 5))
    #     urcv.text.write(game, np.sum(item_box)/255, pos='bottom')

    show('game', game, text=game_text)

def mark_index(video, list_name):
    index = video._index
    items = video.data.get(list_name, [])

    # remove nearby items
    items = [i for i in items if abs(i-index) > 100]

    # add it to the list
    items.append(video._index)
    video.data[list_name] = items

def pressed_func(video, pressed):
    if pressed in ["?", "h"]:
        print("help")
    elif pressed == 'b':
        video.data['game_bounds'] = urcv.input.get_exact_roi(
            video._raw_image,
            name='Select crop of game area',
        )
    elif pressed == 'c':
        print(urcv.input.get_exact_roi(video._frame_image, name='Print these coords')),
    elif pressed == 's':
        video.data['start'] = video._index
        # if not 'start' in video.matcher.data:
        #     video.get_game_content()
        #     video.matcher.save_start(video._raw_image)
        #     print('saved start for world ' + video.data['world'])
    elif pressed == 'e':
        video.data['end'] = video._index
    elif pressed == 'i':
        mark_index(video, 'manual_items')
    elif pressed == 't':
        mark_index(video, 'touched_items')
    else:
        print('pressed', pressed)

def configure_video(video_path):
    video = Video(video_path)
    print('configuring', video_path)
    if 'world' not in video.data:
        video.data['world'] = input('enter world slug:')
    video.watch(watch_func, pressed_func)

if __name__ == "__main__":
    typer.run(configure_video)