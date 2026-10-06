#!/usr/bin/env python3
"""STT comparison: OpenAI gpt-4o-mini-transcribe vs ElevenLabs Scribe on short Arabic clips.

CHILDREN'S DATA: use ONLY synthetic clips (for example text-to-speech or an adult
imitating a child) or clips that were recorded with documented consent and then
anonymised (no names, no identifying content). Never run real children's recordings
from the live app through this script. Outputs contain transcripts, so keep them out of git.

Reads a folder of short clips (wav, mp3, m4a, webm, ogg, flac). If a clip has a reference
transcript next to it (clip.txt, same name), word error rate (WER) is computed for each
engine; otherwise you compare by eye in the HTML side-by-side.

ElevenLabs gets keyterms: the value names from the knowledge bank
(backend/session_moral_context/fixtures/islamic_knowledge_base.json, theme names) plus
their Arabic spellings (backend/conversation/agent/stt_factory.py). Keyterms apply to
Scribe batch models (scribe_v2), so this script calls the batch endpoint. Pass
--openai-prompt to give OpenAI the same terms as a prompt for a fair comparison.

Usage:
  python scripts/voice/stt_compare.py CLIPS_DIR --dry-run     # plan only, no API calls
  python scripts/voice/stt_compare.py CLIPS_DIR --out out/    # needs OPENAI_API_KEY and ELEVEN_API_KEY

Keys: OPENAI_API_KEY from the environment; ElevenLabs key from ELEVEN_API_KEY or the key
file next to the worktrees. Keys are never printed or written. An engine whose key is
missing is skipped and its column says so.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import mimetypes
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as common

AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac", ".mp4", ".mpeg", ".mpga"}
OPENAI_URL = "https://api.openai.com/v1/audio/transcriptions"
OPENAI_MODEL = "gpt-4o-mini-transcribe"
SCRIBE_MODEL = "scribe_v2"
FIXTURE = common.BACKEND_DIR / "session_moral_context" / "fixtures" / "islamic_knowledge_base.json"
MAX_CLIP_BYTES = 24 * 1024 * 1024  # OpenAI's upload limit is 25 MB


def list_clips(folder: Path):
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTS)


def theme_names() -> list[str]:
    try:
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        return [entry["theme"].strip() for entry in data if entry.get("theme")]
    except (OSError, ValueError, KeyError, TypeError):
        return []


def keyterms() -> list[str]:
    return common.import_backend_module("conversation.agent.stt_factory").build_keyterms("ar", theme_names())


def normalize_ar(text: str) -> list[str]:
    """Word list for WER: drop diacritics, tatweel and punctuation; unify alef/ya/ta-marbuta forms."""
    text = re.sub(r"[ً-ٰٟـ]", "", text or "")
    text = re.sub("[أإآٱ]", "ا", text).replace("ى", "ي").replace("ة", "ه")
    text = re.sub(r"[^\w\s]", " ", text.lower())
    return text.split()


def wer(reference: str, hypothesis: str) -> float | None:
    ref, hyp = normalize_ar(reference), normalize_ar(hypothesis)
    if not ref:
        return None
    prev = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        cur = [i]
        for j, h in enumerate(hyp, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (r != h)))
        prev = cur
    return round(prev[-1] / len(ref), 3)


def transcribe_openai(clip: Path, key: str, prompt: str | None) -> str:
    fields = [("model", OPENAI_MODEL), ("language", "ar"), ("response_format", "json")]
    if prompt:
        fields.append(("prompt", prompt))
    ctype = mimetypes.guess_type(clip.name)[0] or "application/octet-stream"
    body, content_type = common.multipart(fields, [("file", clip.name, clip.read_bytes(), ctype)])
    _, _, _, data = common.request(
        "POST", OPENAI_URL, headers={"Authorization": f"Bearer {key}", "Content-Type": content_type},
        body=body, timeout=120)
    return json.loads(data).get("text", "")


def transcribe_scribe(clip: Path, key: str, terms: list[str]) -> str:
    fields = [("model_id", SCRIBE_MODEL), ("language_code", "ar"), ("tag_audio_events", "false")]
    fields += [("keyterms", t) for t in terms]
    ctype = mimetypes.guess_type(clip.name)[0] or "application/octet-stream"
    body, content_type = common.multipart(fields, [("file", clip.name, clip.read_bytes(), ctype)])
    _, _, _, data = common.request(
        "POST", f"{common.ELEVEN_BASE}/v1/speech-to-text",
        headers={"xi-api-key": key, "Content-Type": content_type}, body=body, timeout=120)
    return json.loads(data).get("text", "")


def write_html(out: Path, rows, mean_wer):
    def cell(r, name):
        text, w = r[name], r.get(f"{name}_wer")
        extra = f"<br><small>WER {w}</small>" if w is not None else ""
        return f'<td dir="rtl" lang="ar">{html.escape(text)}{extra}</td>'

    body = "".join(
        f"<tr><th>{html.escape(r['clip'])}</th><td dir=\"rtl\" lang=\"ar\">{html.escape(r['reference'])}</td>"
        f"{cell(r, 'openai')}{cell(r, 'scribe')}</tr>" for r in rows)
    means = ", ".join(f"{k}: {v}" for k, v in mean_wer.items() if v is not None) or "no references given"
    (out / "stt_compare.html").write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>STT comparison</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{ font: 16px/1.6 system-ui, sans-serif; margin: 16px; background: #fbfaf7; color: #1c1c1a; }}
table {{ border-collapse: collapse; width: 100%; }} th, td {{ border: 1px solid #d6d2c8; padding: 8px; vertical-align: top; }}
td {{ font-size: 18px; }} .wrap {{ overflow-x: auto; }}
</style></head><body>
<h1>STT comparison</h1>
<p>Synthetic or consented, anonymised clips only. Mean WER (lower is better): {html.escape(means)}.</p>
<div class="wrap"><table><tr><th>Clip</th><th>Reference</th><th>OpenAI {OPENAI_MODEL}</th>
<th>ElevenLabs {SCRIBE_MODEL} + keyterms</th></tr>{body}</table></div></body></html>""", encoding="utf-8")


def main(argv=None) -> int:
    common.use_utf8_output()
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("clips", type=Path, help="folder of short Arabic clips")
    p.add_argument("--out", type=Path, default=common.REPO_ROOT.parent / "stt-compare-out")
    p.add_argument("--dry-run", action="store_true", help="show the plan only, no API calls")
    p.add_argument("--openai-prompt", action="store_true", help="give OpenAI the keyterms as a prompt")
    args = p.parse_args(argv)

    if not args.clips.is_dir():
        p.error(f"not a folder: {args.clips}")
    clips = list_clips(args.clips)
    terms = keyterms()
    openai_key = (os.environ.get("OPENAI_API_KEY") or "").strip() or None
    eleven_key = common.load_eleven_key()
    prompt = ", ".join(terms) if args.openai_prompt else None

    print("DRY RUN: no API calls will be made.\n" if args.dry_run else "STT comparison\n")
    print(f"Clips: {len(clips)} in {args.clips}")
    with_ref = sum(1 for c in clips if c.with_suffix(".txt").is_file())
    print(f"Reference transcripts (clip.txt) found: {with_ref}")
    print(f"Engines: OpenAI {OPENAI_MODEL} (key: {'yes' if openai_key else 'no'}), "
          f"ElevenLabs {SCRIBE_MODEL} (key: {'yes' if eleven_key else 'no'}, {common.key_source()})")
    print(f"Keyterms ({len(terms)}): {', '.join(terms)}")
    print(f"OpenAI prompt: {'keyterms' if prompt else 'none'}")
    print(f"Output folder: {args.out}  (stt_compare.csv, stt_compare.html)")
    if args.dry_run:
        for c in clips:
            print(f"  {c.name}  {c.stat().st_size} bytes")
        oversize = [c.name for c in clips if c.stat().st_size > MAX_CLIP_BYTES]
        if oversize:
            print("Too large for upload: " + ", ".join(oversize))
        return 0
    if not clips:
        print("No clips found.", file=sys.stderr)
        return 2

    args.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for clip in clips:
        ref_path = clip.with_suffix(".txt")
        reference = ref_path.read_text(encoding="utf-8").strip() if ref_path.is_file() else ""
        row = {"clip": clip.name, "reference": reference}
        for name, key, fn in (
            ("openai", openai_key, lambda k, c=clip: transcribe_openai(c, k, prompt)),
            ("scribe", eleven_key, lambda k, c=clip: transcribe_scribe(c, k, terms)),
        ):
            if clip.stat().st_size > MAX_CLIP_BYTES:
                row[name] = "[skipped: file too large]"
            elif not key:
                row[name] = "[skipped: no API key]"
            else:
                try:
                    row[name] = fn(key)
                except common.ApiError as err:
                    row[name] = f"[error {err.status}: {err.detail}]"
            row[f"{name}_wer"] = wer(reference, row[name]) if reference and not row[name].startswith("[") else None
        print(f"  {clip.name} done")
        rows.append(row)

    fields = ["clip", "reference", "openai", "openai_wer", "scribe", "scribe_wer"]
    with (args.out / "stt_compare.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    mean = {}
    for name in ("openai", "scribe"):
        vals = [r[f"{name}_wer"] for r in rows if r[f"{name}_wer"] is not None]
        mean[name] = round(sum(vals) / len(vals), 3) if vals else None
    write_html(args.out, rows, mean)
    print(f"\nMean WER: {mean}\nWrote {args.out / 'stt_compare.csv'} and {args.out / 'stt_compare.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
