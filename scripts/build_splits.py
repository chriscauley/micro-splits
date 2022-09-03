import _setup

from collections import defaultdict
import json
import numpy as np
import sys
from pathlib import Path

from models.data import JsonCache

data_dir = Path('.data')
world_slug = sys.argv[1]

class SplitTracker:
    def __init__(self, world):
        Path('.splits').mkdir(exist_ok=True)
        self.data_path = f'.splits/{world}.json'
        self.world = world
        self.data = JsonCache(self.data_path)
        self.video_trackers = {}

    def _record(self, video_name, split):
        item1, item2, duration = split
        if not video_name in self.data or item1 == 'start':
            self.data[video_name] = []
        self.data[video_name].append(split)

    def record(self, video_name, item, ms):
        if not video_name in self.video_trackers:
            self.video_trackers[video_name] = VideoTracker(video_name, self)
        self.active_video = video_name
        tracker = self.video_trackers[video_name]
        tracker.split(item, ms)
        self.data._save()

    def get_results(self):
        golden = defaultdict(lambda: float('inf'))
        all_ = defaultdict(list)
        fastest = None
        fastest_ms = float('inf')
        past_splits = [
            splits for name, splits in self.data.items()
            if name != self.active_video
        ]
        item_map = defaultdict(list)
        for splits in past_splits:
            duration = 0
            for item1, item2, ms in splits:
                item_map[item1].append(item2)
                all_[(item1, item2)].append(ms)
                if ms < golden[(item1, item2)]:
                    golden[(item1, item2)] = ms
                duration += ms
                if item2 == 'end':
                    if duration < fastest_ms:
                        fastest_ms = duration
                        fastest = video_name

        results = []
        for item1, item2, ms in self.data[self.active_video]:
            key = (item1, item2)
            golden_time = golden[key]
            median = np.median(all_[key])
            color = 'red' if ms > median else 'green'
            delta = ms - median
            if ms <= golden_time:
                color = 'yellow'
                delta = ms - golden_time
            results.append({
                'name': item2,
                'color': color,
                'delta': delta,
            })

        for result in results:
            print(result)

class VideoTracker:
    def __init__(self, video_name, split_tracker):
        self.video_name = video_name
        self.split_tracker = split_tracker
        self.inventory = {}
        self.last_item = 'start'
        self.last_ms = self.start_ms = 0

    def split(self, item, ms):
        if item == 'start':
            self.last_item = 'start'
            self.last_ms = ms
            self.start_ms = ms
            return

        if item in self.inventory:
            return
        self.inventory[item] = True
        split = [self.last_item, item, ms - self.last_ms]
        self.split_tracker._record(self.video_name, [self.last_item, item, ms - self.last_ms])
        self.last_ms = ms
        self.last_item = item

        # if item == 'end':
        #     duration = ms - self.start_ms
        #     self.split_tracker.finish(self.video_name, duration)

split_tracker = SplitTracker(world_slug)

for video_dir in data_dir.iterdir():
    data_path = video_dir / 'data.json'
    video_name = video_dir.name

    if not data_path.exists():
        continue
    with open(data_path, 'r') as f:
        data = json.loads(f.read())

    if data.get('world') != world_slug:
        continue

    def index_to_ms(index):
        return int(1000 * index / data['fps'])

    split_tracker.record(video_name, 'start', index_to_ms(data.get('start', 0)))

    for index, item in data.get('items'):
        split_tracker.record(video_name, item, index_to_ms(index))

    if data.get('end'):
        split_tracker.record(video_name, 'end', data.get('end'))

split_tracker.get_results()