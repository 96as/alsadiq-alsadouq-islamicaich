"""Render the soft "hmm" clips used by FILLER_MODE=hum (task 08).

Run once by a developer, never at runtime. The clips it writes are committed.

    python render_fillers.py --key-file PATH_TO_KEY_FILE

What it does for each short non-verbal sound:
  1. asks ElevenLabs (voice and model below) for the sound as an mp3,
  2. decodes it with PyAV (the same library livekit uses to play the clip),
  3. trims leading and trailing silence, caps the length at MAX_SECONDS with a fade out,
  4. normalises the loudness to a soft, even level,
  5. writes a small mono 48 kHz Opus file in an .ogg container next to this script.

The API key is read from the file (or the ELEVEN_API_KEY variable) and used only for the
request header. It is never printed or written anywhere. No scripture or spoken sentences:
only the sounds in SOUNDS, a few characters each.

Needs: av, numpy (both come with livekit-agents). No ffmpeg program is needed.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

import av
import numpy as np

# The voice in the team's working .env (ELEVEN_VOICE_ID_AR/EN), not the tts_factory.py code
# default. Render again with the deployed voice id if that changes (see README.md).
VOICE_ID = "pCKbQ4EPGE06zpEPGNvS"
MODEL_ID = "eleven_flash_v2_5"
SAMPLE_RATE = 48000
MAX_SECONDS = 0.75          # hard cap, the task asks for under 0.8 s
FADE_IN_S = 0.02
FADE_OUT_S = 0.12
TARGET_RMS_DBFS = -26.0     # soft: quieter than the spoken voice on purpose
PEAK_LIMIT_DBFS = -6.0
SILENCE_DBFS = -42.0        # below this (relative to full scale) counts as silence when trimming

# File name stem -> the sound sent to the voice. Short and non-verbal.
SOUNDS = {
    "hum-01": "Hmm.",
    "hum-02": "Mmm.",
    "hum-03": "Hmm, hm.",
    "hum-04": "Mm-hm.",
    "hum-05": "Hmmm.",
    "hum-06": "Mmm, hm.",
    "hum-07": "Hm.",
}

HERE = Path(__file__).resolve().parent


def read_key(path: str | None) -> str:
    key = ""
    if path:
        key = Path(path).read_text(encoding="utf-8").strip()
    key = key or os.getenv("ELEVEN_API_KEY", "").strip()
    if not key:
        sys.exit("No ElevenLabs key: pass --key-file or set ELEVEN_API_KEY.")
    return key


def synthesize(text: str, key: str) -> bytes:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}?output_format=mp3_44100_128"
    body = json.dumps({
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {"stability": 0.6, "similarity_boost": 0.75, "style": 0.0,
                           "use_speaker_boost": False},
    }).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST", headers={
        "xi-api-key": key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
        "User-Agent": "alsadiq-filler-render/1.0",
    })
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        # Status only: the response body could echo request details.
        sys.exit(f"ElevenLabs returned HTTP {exc.code} for {text!r}.")


def decode(mp3_bytes: bytes) -> np.ndarray:
    """mp3 bytes -> float32 mono samples at SAMPLE_RATE in [-1, 1]."""
    resampler = av.AudioResampler(format="flt", layout="mono", rate=SAMPLE_RATE)
    chunks = []
    with av.open(io.BytesIO(mp3_bytes)) as container:
        for frame in container.decode(audio=0):
            for out in resampler.resample(frame):
                chunks.append(out.to_ndarray().reshape(-1))
    for out in resampler.resample(None):
        chunks.append(out.to_ndarray().reshape(-1))
    return np.concatenate(chunks).astype(np.float32)


def trim_silence(samples: np.ndarray) -> np.ndarray:
    threshold = 10 ** (SILENCE_DBFS / 20)
    loud = np.flatnonzero(np.abs(samples) > threshold)
    if loud.size == 0:
        return samples
    pad = int(0.015 * SAMPLE_RATE)
    return samples[max(0, loud[0] - pad): min(samples.size, loud[-1] + pad)]


def shape(samples: np.ndarray) -> np.ndarray:
    """Cap the length, add the fades, normalise the loudness."""
    samples = samples[: int(MAX_SECONDS * SAMPLE_RATE)].copy()
    fade_in = min(samples.size, int(FADE_IN_S * SAMPLE_RATE))
    fade_out = min(samples.size, int(FADE_OUT_S * SAMPLE_RATE))
    if fade_in:
        samples[:fade_in] *= np.linspace(0.0, 1.0, fade_in, dtype=np.float32)
    if fade_out:
        samples[-fade_out:] *= np.linspace(1.0, 0.0, fade_out, dtype=np.float32)
    rms = float(np.sqrt(np.mean(np.square(samples)))) or 1e-9
    gain = 10 ** (TARGET_RMS_DBFS / 20) / rms
    peak = float(np.max(np.abs(samples))) * gain
    limit = 10 ** (PEAK_LIMIT_DBFS / 20)
    if peak > limit:
        gain *= limit / peak
    return np.clip(samples * gain, -1.0, 1.0)


def dbfs(value: float) -> float:
    return 20 * math.log10(max(value, 1e-9))


def encode_opus(samples: np.ndarray, path: Path) -> None:
    pcm = (samples * 32767).astype(np.int16).reshape(1, -1)
    frame = av.AudioFrame.from_ndarray(pcm, format="s16", layout="mono")
    frame.sample_rate = SAMPLE_RATE
    resampler = av.AudioResampler(format="s16", layout="mono", rate=SAMPLE_RATE, frame_size=960)
    with av.open(str(path), "w", format="ogg") as container:
        stream = container.add_stream("libopus", rate=SAMPLE_RATE)
        stream.layout = "mono"
        stream.bit_rate = 32000
        for out in [*resampler.resample(frame), *resampler.resample(None)]:
            for packet in stream.encode(out):
                container.mux(packet)
        for packet in stream.encode(None):
            container.mux(packet)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--key-file", help="file that holds the ElevenLabs key")
    parser.add_argument("--out", default=str(HERE), help="folder for the .ogg files")
    args = parser.parse_args()
    key = read_key(args.key_file)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for stem, text in SOUNDS.items():
        samples = shape(trim_silence(decode(synthesize(text, key))))
        target = out_dir / f"{stem}.ogg"
        encode_opus(samples, target)
        rms = float(np.sqrt(np.mean(np.square(samples))))
        print(f"{target.name}: {text!r:14} {samples.size / SAMPLE_RATE:.2f} s  "
              f"rms {dbfs(rms):.1f} dBFS  peak {dbfs(float(np.max(np.abs(samples)))):.1f} dBFS  "
              f"{target.stat().st_size} bytes")


if __name__ == "__main__":
    main()
