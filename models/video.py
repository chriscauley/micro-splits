import cv2

from .mixins import WaitKeyMixin

GAME_WIDTH = 300
GAME_HEIGHT = 224
GAME_SHAPE = (GAME_WIDTH, GAME_HEIGHT)
HUD_SPLIT = 31

class Video(WaitKeyMixin):
    """
    Class for interacting with a video (mkv, mp4, etc)
    """
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.cap = cv2.VideoCapture(file_path)
        self._index = -1 # foces next line to load frame
        self._cached_index = None
        self.get_frame(0)

    def get_frame(self, target_index=None):
        if target_index == None:
            target_index = self._index
        if self._cached_index != target_index:
            if target_index == 0:
                # opencv is 1 indexed, so we'll just return the first frame
                # this means the first and second frames are going to be the same
                target_index = 1
            self._cached_index = target_index

            self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_index)
            ret, self._frame_image = self.cap.read()
            self._raw_image = self._frame_image
            current_shape = self._frame_image.shape
            if current_shape[:2] != GAME_SHAPE:
                self._frame_image = cv2.resize(
                    self._frame_image,
                    GAME_SHAPE,
                    interpolation=cv2.INTER_NEAREST
                )
            if not ret:
                raise NotImplementedError("Video is not loaded")
        self._index = int(target_index)
        return self._frame_image

    def get_hud_content(self):
        return self.get_frame()[:HUD_SPLIT]

    def get_game_content(self):
        return self.get_frame()[HUD_SPLIT:]

    def get_current_time(self):
        return self.cap.get(cv2.CAP_PROP_POS_MSEC)

    def get_max_index(self):
        return self.cap.get(cv2.CAP_PROP_FRAME_COUNT)

    def increase_goto_by(self, amount):
        if amount < 0:
            self._index += amount
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self._index)
        else:
            super().increase_goto_by(amount)
