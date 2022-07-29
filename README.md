# Micro Splits

## Getting started

First clone repo and install requirements to a virtual environment. Then download some videos from the google drive. Make sure everything is working by running the following

`python scripts/process_video.py path/to/video.mkv`

This will print progress as it goes and should take about 40s per hour of video. Next run the review script. Look at the contents of `models/mixins.py` to see which keys to use to advance the video.

`python scripts/review_video.py path/to/video.mkv`

## Notes

This repo currently consists of several scripts:

* `scripts/process_video.py` - Analyzes a video and writes the videos means, sums, and deltas to a data file.

* `scripts/review_video.py` - Loads the video and the datasets and let's you step through them.

* `scripts/hue_scan.py` - Steps through a video displaying a thresholded spectrum of the video (any pixels brighter than 144 and split by hue angle).
