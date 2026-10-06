# Soft thinking sounds

Seven very short, quiet "hmm" sounds that the agent can play while a slow answer is on its way
(`FILLER_MODE=hum`, see `conversation/agent/filler.py`). They are not part of the spoken reply:
they are never sent to the voice, never saved in the chat and never counted in the
ElevenLabs character budget.

## What they are

| File | Sound sent to the voice | Length |
|---|---|---|
| hum-01.ogg | Hmm. | 0.40 s |
| hum-02.ogg | Mmm. | 0.48 s |
| hum-03.ogg | Hmm, hm. | 0.69 s |
| hum-04.ogg | Mm-hm. | 0.55 s |
| hum-05.ogg | Hmmm. | 0.49 s |
| hum-06.ogg | Mmm, hm. | 0.55 s |
| hum-07.ogg | Hm. | 0.31 s |

All are non-verbal sounds: no words, no scripture. A speech-to-text check heard them as
"hmm", "mhm" and "hm hm".

## How they were made

- Voice: ElevenLabs voice id `pCKbQ4EPGE06zpEPGNvS`, the voice set in the team's working
  `.env` (`ELEVEN_VOICE_ID_AR` and `ELEVEN_VOICE_ID_EN`). It is NOT the code default in
  `tts_factory.py` (`w4LX7bK479eHGM1k15Em`). If the deployed voice changes, render the clips
  again with the new id, or the hum will be a different voice from the replies.
- Model: `eleven_flash_v2_5`. Voice settings: stability 0.6, similarity 0.75, style 0, no
  speaker boost. Each request was a few characters.
- Script: `render_fillers.py` in this folder (run once by a developer, never at runtime):
  `python render_fillers.py --key-file PATH_TO_KEY_FILE`. The key is read from the file and
  used only in the request header; it is not printed or stored.
- Processing in the script: silence trimmed, length capped at 0.75 s, 20 ms fade in and 120 ms
  fade out, loudness set to about -26 dBFS RMS with the peak under -6 dBFS (softer than the
  spoken voice on purpose), then saved as mono 48 kHz Opus in an `.ogg` file (about 2 KB each).

## Licence

Made by the team with the team's own ElevenLabs account through the API, from our own text
(non-verbal sounds only). No third-party recording, sample or sound library is used. Use of
the audio is under the ElevenLabs terms for that account: check that the account's plan allows
commercial use before the clips ship outside the hackathon demo.

## Changing them

Edit the `SOUNDS` table in `render_fillers.py`, run it, listen, and commit the new files. Keep
every clip under 0.8 s. The agent plays whatever `.ogg` or `.mp3` files are in this folder.

A "spoken" filler (real words such as "let me think") is deliberately not built: that is the
content team's decision (see the TODO in `filler.py`).
