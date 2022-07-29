import json
import numpy as np
from pathlib import Path
from unrest.utils import JsonCache

from .video import Video

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        return json.JSONEncoder.default(self, obj)


def get_data(video_path):
    Path('.data').mkdir(exist_ok=True)
    data = JsonCache(f'.data/{video_path.split("/")[-1]}.json', __encoder__=NumpyEncoder)
    return data