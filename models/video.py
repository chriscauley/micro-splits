import cv2
import functools
import urcv

from .item_detector import ItemDetector
from .matcher import Matcher
from .mixins import WaitKeyMixin, OutOfBoundsError
from .data import JsonCache

GAME_WIDTH = 300
GAME_HEIGHT = 224
GAME_SHAPE = (GAME_HEIGHT, GAME_WIDTH)
HUD_SPLIT = 31

class Video(WaitKeyMixin):
    """
    Class for interacting with a video (mkv, mp4, etc)
    """
    def __init__(self, file_path):
        super().__init__()
        fname = file_path.split("/")[-1]
        self.data_dir = f'.data/{fname}/'
        self.data = JsonCache(self.data_dir + 'data.json')
        self.file_path = file_path
        self.cap = cv2.VideoCapture(file_path)
        self._next_item_check = 0
        self.data.update({
            'video_name': fname,
            'video_path': file_path,
            'fps': self.cap.get(cv2.CAP_PROP_FPS),
        })
        self.data._save()
        self._cached_index = None
        self._index = -1 # foces next line to load frame
        self.get_frame(0)
        self.detector = ItemDetector(self)

    @functools.cached_property
    def matcher(self):
        return Matcher(self.data['world'])

    def get_frame(self, target_index=None, safe=False):
        if target_index == None:
            target_index = self._index
        self._index = int(target_index)
        if self._cached_index != self._index:
            if self._index == 0:
                # opencv is 1 indexed, so we'll just return the first frame
                # this means the first and second frames are going to be the same
                self._index = 1
            self._cached_index = self._index

            if self.cap.get(cv2.CAP_PROP_POS_FRAMES) + 1 != self._index:
                # manually setting the position is much slower than going to the next frame
                # only do this when necessary
                print('seeking')
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, self._index)

            ret, self._frame_image = self.cap.read()
            self._raw_image = self._frame_image
            if self._frame_image is None:
                now = self._index
                end = self.get_max_index()
                print(f"The video has ended on frame {now}/{end}")
                if safe:
                    self.data['last_index'] = self._index -1
                    return None
                raise OutOfBoundsError(f"The video has ended on frame {now}/{end}")

            # game bounds remove the stream content, etc
            game_bounds = self.data.get('game_bounds')
            if game_bounds:
                self._frame_image = urcv.transform.crop(self._frame_image, game_bounds)

            current_shape = self._frame_image.shape
            if current_shape[:2] != GAME_SHAPE:
                self._frame_image = cv2.resize(
                    self._frame_image,
                    GAME_SHAPE[::-1],
                    interpolation=cv2.INTER_NEAREST
                )
            if not ret:
                raise NotImplementedError("Video is not loaded")
        return self._frame_image

    def get_hud_content(self):
        return self.get_frame()[:HUD_SPLIT]

    def get_game_content(self):
        return self.get_frame()[HUD_SPLIT:]

    def get_current_time(self):
        return self.cap.get(cv2.CAP_PROP_POS_MSEC)

    def get_max_index(self):
        return self.data.get('last_index') or self.cap.get(cv2.CAP_PROP_FRAME_COUNT)

    def increase_goto_by(self, amount):
        if amount < 0:
            self._index += amount
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self._index)
        else:
            super().increase_goto_by(amount)
