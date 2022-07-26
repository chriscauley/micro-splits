import numpy as np
import time

import urcv


class WaitKeyMixin:
    def __init__(self, *args, **kwargs):
        self._index = 0
        self.goto = None
        self._goto_delta = None
        self._last_tick = time.time()

    def increase_goto_by(self, amount):
        self.goto_sign = np.sign(amount)
        self.goto = self._index + amount
        self.goto = self.goto % self.get_max_index()

    @property
    def seeking(self):
        return self.goto != None

    def wait_key(self):
        if self.goto is not None:
            delta = self.goto - self._index
            if not self._goto_delta:
                self._goto_delta = delta
                self._goto_start = time.time()
            if abs(delta) > 10 and self._index % 100 == 99:
                self._last_tick = time.time()
            self._index += self.goto_sign
            if self.goto == self._index:
                self.goto = None
                ms = int(1000 * (time.time() - self._goto_start))
                if ms > 1:
                    # TODO whether or not to print should be controled by a flag
                    print(f'{self._goto_delta} frames took {ms}ms')
                self._goto_delta = None
            self._index = self._index % self.get_max_index()
            return
        key = urcv.wait_key()
        if key == 'right':
            self._index += 1
        elif key == 'left':
            self._index -= 1
        elif key == 'down':
            self.increase_goto_by(-10)
        elif key == 'up':
            self.increase_goto_by(10)
        elif key == ',':
            self.increase_goto_by(-100)
        elif key == '.':
            self.increase_goto_by(100)
        elif key == '<':
            self.increase_goto_by(-1000)
        elif key == '>':
            self.increase_goto_by(1000)
        elif key == '0':
            self._index = 0
        elif key == '/':
            self.increase_goto_by(self.get_max_index() - self._index - 1)
            print("Goint to end:", self.goto)
        elif key == 'g':
            while True:
                s = input("Go to what index?")
                if s.isdigit():
                    self.increase_goto_by(int(s) - self._index)
                    break
        else:
            return key
        self._index = self._index % self.get_max_index()

    def get_max_index(self):
        raise NotImplementedError()

    def watch(self, watch_func, pressed_func):
        while True:
            if not self.seeking:
                watch_func(self)
            pressed = self.wait_key()
            if pressed == 'q':
                break
            if pressed and pressed_func:
                pressed_func(pressed)