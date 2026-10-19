"""Muxes a scripts/mouth-capture.py recording into an MP4 with the audio exactly where it started.

  PYTHONUTF8=1 python scripts/mouth-mux.py ../tmp-out/cap-after-1000 ../tmp-out/speak-after-1000.mp4 [--ffmpeg <path>]

Reads <cap>.webm and <cap>.json. The capture lit a white square (top-left, 28 px) on the media
element's `playing` event; the first dark-to-bright change of that square is the moment the audio
started in the video. The audio is delayed to that moment plus the output latency the capture
measured (the sound leaves the speakers that long after `playing`), the square is painted out
(delogo) and the video is cut to start 1 s before the speech. Output is 30 fps H.264 + AAC.

Prints {"markerS": ..., "audioAtS": ..., "startS": ...}. The marker is read from 25 fps screencast
frames, so it is good to within one frame (40 ms), early by 20 ms on average.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('cap', help='path of the capture without extension (.webm and .json)')
ap.add_argument('out', help='output mp4')
ap.add_argument('--ffmpeg', default=os.environ.get('FFMPEG', 'ffmpeg'))
ap.add_argument('--audio', default='', help='audio file; default is frontend/<url from the json>')
ap.add_argument('--preroll', type=float, default=1.0, help='seconds of video kept before the audio starts')
args = ap.parse_args()

meta = json.load(open(args.cap + '.json', encoding='utf8'))
webm = args.cap + '.webm'
here = os.path.dirname(os.path.abspath(__file__))
audio = args.audio or os.path.join(os.path.dirname(here), meta['url'].lstrip('/').replace('/', os.sep))
if not os.path.exists(audio):
    sys.exit(f'audio not found: {audio}')

# 1. find the marker in the video, resampled to a steady 100 fps. The page is white before it loads
# and the square is black until `playing`: the marker is the first dark-to-bright change after the
# square has been seen dark.
RATE = 100
raw = subprocess.run(
    [args.ffmpeg, '-hide_banner', '-loglevel', 'error', '-i', webm, '-vf', f'fps={RATE},crop=20:20:8:8,format=gray', '-f', 'rawvideo', '-'],
    capture_output=True,
).stdout
frames = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 20, 20)
bright = frames.mean(axis=(1, 2)) > 128
edges = np.where(bright[1:] & ~bright[:-1])[0] + 1
if not len(edges):
    sys.exit('no sync marker found in the video')
mark = float(edges[0]) / RATE
lat = float(meta.get('outputLatencyS', 0.0))
audio_at = mark + lat
start = max(0.0, mark - args.preroll)
delay_ms = int(round((audio_at - start) * 1000))

# 2. cut, paint out the marker, delay the audio into place
cmd = [
    args.ffmpeg, '-hide_banner', '-loglevel', 'error', '-y',
    '-ss', f'{start:.3f}', '-i', webm, '-i', audio,
    '-filter_complex', f'[0:v]delogo=x=2:y=2:w=34:h=34,fps=30,format=yuv420p[v];[1:a]adelay={delay_ms}|{delay_ms},apad[a]',
    '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-c:a', 'aac', '-b:a', '128k',
    '-shortest', args.out,
]
subprocess.run(cmd, check=True)
print(json.dumps({'markerS': round(mark, 3), 'audioAtS': round(audio_at, 3), 'startS': round(start, 3), 'outputLatencyS': lat, 'out': args.out}))
