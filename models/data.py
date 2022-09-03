import json
import numpy as np
from pathlib import Path
from unrest.utils import JsonCache

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        return json.JSONEncoder.default(self, obj)


class JsonCache(JsonCache):
    def __init__(self, path, *args, **kwargs):
        kwargs['__encoder__'] = NumpyEncoder
        Path(path).parent.mkdir(exist_ok=True)
        return super().__init__(path, *args, **kwargs)
