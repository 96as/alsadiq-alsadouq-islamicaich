#!/usr/bin/env python3
"""Voice audition: synthesize original lines with the candidate ElevenLabs voices.

Calls the ElevenLabs REST API directly (no LiveKit needed). For every candidate voice
and model it writes <voice>_<model>_lineNN.mp3 into the output folder, an index.html to
play them side by side, and results.csv with time-to-first-byte per request.

Before synthesizing it asks the account which candidate voices it can use
(GET /v1/voices; Voice Library voices may need adding to the account or a paid plan)
and what the character quota is (GET /v1/user/subscription).

The lines are original text. They contain NO Quran verse and NO hadith text; the
citation lines only name a book ("narrated by Al-Bukhari"). Verses are always played
as recitation audio, never synthesized.

Usage:
  python scripts/voice/audition.py --dry-run            # plan + character count, no API calls
  python scripts/voice/audition.py                      # full run (needs ELEVEN_API_KEY)
  python scripts/voice/audition.py --voices habibah,anas --models eleven_flash_v2_5 --lines ar:1-3

The key comes from ELEVEN_API_KEY, else from the key file next to the worktrees
(ELEVEN_KEY_FILE overrides the path). It is never printed or written anywhere.
Quota: the full grid is about 9.5k characters with the two default models, so check the
quota line first. A run that needs more than the remaining quota is refused unless
--force; --max-chars sets your own cap.

Models: eleven_v4_turbo is deliberately NOT offered. Plugin 1.5.1 does not know it and it
is not usable through the streaming socket the agent uses, so an audition of it would
not predict the live voice (docs/hackathon/handoffs/07-elevenlabs-facts.md).
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _common as common

# Candidate Arabic (MSA) voices from docs/hackathon/tasks/07-elevenlabs-voice.md.
# The IDs come from a third-party directory; the account check below confirms them.
CANDIDATE_VOICES = [
    ("habibah", "Habibah (warm, storytelling, female)", "w4LX7bK479eHGM1k15Em"),
    ("asmaa", "Asmaa (gentle, female)", "qi4PkV9c01kb869Vh7Su"),
    ("anas", "Anas (calm, male)", "R6nda3uM038xEEKi7GFl"),
    ("ashraf", "Ashraf (clear, male)", "t8atLZaWuCcW6gENDwwa"),
]
BASE_MODELS = ["eleven_flash_v2_5", "eleven_multilingual_v2"]
LANGUAGE_HINT_MODELS = {"eleven_flash_v2_5", "eleven_turbo_v2_5"}

# (id, kind, text). Original lines; numbers are written as words (Flash does not normalise).
LINES_AR = [
    ("greeting", "السلام عليكم يا صديقي! أنا الصديق الصدوق، وأنا سعيد جدًا بلقائك اليوم."),
    ("greeting", "وعليكم السلام! كيف كان يومك في المدرسة؟ هل تعلّمت شيئًا جديدًا؟"),
    ("story", "في قرية صغيرة قرب البحر، كان يعيش ولد اسمه سالم، وكان يحب أن يساعد جيرانه كل صباح."),
    ("story", "وفي يوم من الأيام، وجد سالم محفظة صغيرة على الطريق، فوقف يفكر ماذا يفعل."),
    ("story", "أخذ سالم المحفظة وركض إلى صاحبها، فابتسم الرجل وشكره من قلبه."),
    ("praise", "أحسنت يا بطل! لقد قلت الصدق حتى عندما كان الأمر صعبًا، وهذا يجعلني فخورًا بك."),
    ("praise", "ما شاء الله، إجابتك رائعة! استمر هكذا، فأنت تتعلم بسرعة."),
    ("redirect", "أفهم أنك متحمس، لكن دعنا نتحدث بهدوء ولطف، ثم نكمل معًا من حيث توقفنا."),
    ("redirect", "هذا سؤال جميل، لكن أهلك أو معلمك أحق بالإجابة عنه، فهل تسألهم وتخبرني بما قالوا؟"),
    ("citation", "وقد رواه البخاري، وتجد الحديث كاملًا في كتاب الحديث مع والديك."),
]
LINES_EN = [
    ("greeting", "Assalamu alaikum, my friend! I am Al-Sadiq Al-Sadouq, and I am so happy to see you today."),
    ("story", "Once upon a time, in a small village by the sea, there lived a boy named Salim who loved to help his neighbors."),
    ("praise", "Well done! You told the truth even when it was hard, and that makes me very proud of you."),
    ("redirect", "I can tell you are excited, so let us take a slow breath together and then keep going, step by step."),
    ("citation", "This saying was narrated by Imam Al-Bukhari, and you can read it with your parents in a book of hadith."),
]


def build_lines():
    """Return [{n, lang, kind, text}] with global numbering line01..line15 (Arabic first)."""
    out = []
    for lang, rows in (("ar", LINES_AR), ("en", LINES_EN)):
        for kind, text in rows:
            out.append({"n": len(out) + 1, "lang": lang, "kind": kind, "text": text})
    return out


def parse_line_filter(spec: str | None, lines):
    """--lines ar:1-3,en:2 selects by per-language position; default is all."""
    if not spec:
        return lines
    wanted: set[tuple[str, int]] = set()
    for part in spec.split(","):
        lang, _, rng = part.partition(":")
        lang = lang.strip().lower()
        lo, _, hi = rng.partition("-")
        lo_i, hi_i = int(lo), int(hi or lo)
        wanted.update((lang, i) for i in range(lo_i, hi_i + 1))
    counters = {"ar": 0, "en": 0}
    kept = []
    for line in lines:
        counters[line["lang"]] += 1
        if (line["lang"], counters[line["lang"]]) in wanted:
            kept.append(line)
    return kept


def voice_settings():
    """Same calm defaults as the live agent (conversation/agent/tts_factory.py)."""
    try:
        f = common.import_backend_module("conversation.agent.tts_factory")
        return {"stability": f.DEFAULT_STABILITY, "similarity_boost": f.DEFAULT_SIMILARITY,
                "style": f.DEFAULT_STYLE, "use_speaker_boost": f.DEFAULT_SPEAKER_BOOST,
                "speed": f.DEFAULT_SPEED}
    except Exception:  # noqa: BLE001 - keep the tool usable on its own
        return {"stability": 0.65, "similarity_boost": 0.75, "style": 0.0,
                "use_speaker_boost": True, "speed": 0.92}


def plan_report(lines, voices, models):
    n_chars = sum(len(line["text"]) for line in lines)
    n_ar = sum(len(line["text"]) for line in lines if line["lang"] == "ar")
    n_requests = len(lines) * len(voices) * len(models)
    total = n_chars * len(voices) * len(models)
    print(f"Lines: {len(lines)} ({sum(1 for x in lines if x['lang'] == 'ar')} Arabic, "
          f"{sum(1 for x in lines if x['lang'] == 'en')} English), {n_chars} characters per pass "
          f"({n_ar} Arabic)")
    print(f"Voices ({len(voices)}): " + ", ".join(f"{v[0]}={v[2]}" for v in voices))
    print(f"Models ({len(models)}): " + ", ".join(models))
    print(f"Requests: {n_requests}")
    print(f"Characters to be billed: {total}")
    return total


def run_dry(args, lines, voices, models):
    print("DRY RUN: no API calls will be made.\n")
    print(f"Output folder: {args.out}")
    print(f"Key available: {'yes' if common.load_eleven_key() else 'no'} ({common.key_source()})")
    print(f"Voice settings: {voice_settings()}\n")
    plan_report(lines, voices, models)
    print("\nLines:")
    for line in lines:
        print(f"  line{line['n']:02d} [{line['lang']}/{line['kind']}] ({len(line['text'])} chars) {line['text']}")
    print("\nFile names, for example: "
          f"{voices[0][0]}_{models[0]}_line01.mp3 ... {voices[-1][0]}_{models[-1]}_line{lines[-1]['n']:02d}.mp3")
    print("Also written on a real run: index.html, results.csv, voices_report.json")
    return 0


def account_report(key, voices):
    """Print quota + which candidate voices the account lists. Returns (usable ids set, remaining chars)."""
    remaining = None
    try:
        sub = common.get_json("/v1/user/subscription", key)
        used, limit = sub.get("character_count"), sub.get("character_limit")
        remaining = (limit - used) if isinstance(used, int) and isinstance(limit, int) else None
        print(f"Account: tier={sub.get('tier')}, characters used {used} of {limit}"
              + (f" ({remaining} remaining)" if remaining is not None else ""))
    except common.ApiError as err:
        print(f"Account quota unavailable ({err}). The key may lack the user_read permission.")
    listed = {}
    try:
        for v in common.get_json("/v1/voices", key).get("voices", []):
            listed[v["voice_id"]] = v
        print(f"Account lists {len(listed)} voices.")
    except common.ApiError as err:
        print(f"Voice list unavailable ({err}). Will try each candidate directly.")
    report = []
    for vid_slug, label, vid in voices:
        v = listed.get(vid)
        status = f"in account ({v.get('category', '?')})" if v else "NOT in account (will try anyway)"
        print(f"  {vid_slug:8s} {vid}  {status}")
        report.append({"slug": vid_slug, "voice_id": vid, "in_account": bool(v),
                       "category": (v or {}).get("category")})
    return set(listed), remaining, report


def synthesize(key, voice_id, model, line, settings, fmt):
    body = {"text": line["text"], "model_id": model, "voice_settings": settings}
    if model in LANGUAGE_HINT_MODELS:
        body["language_code"] = line["lang"]
    _, ttfb, total, audio = common.request(
        "POST",
        f"{common.ELEVEN_BASE}/v1/text-to-speech/{voice_id}/stream?output_format={fmt}",
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
        body=json.dumps(body).encode("utf-8"),
        timeout=90,
    )
    return ttfb, total, audio


def write_index(out: Path, lines, columns, results, summary_rows):
    """columns: [(voice_slug, voice_label, model)]; results keyed (voice, model, n)."""
    head = "".join(f"<th>{html.escape(label)}<br><small>{html.escape(model)}</small></th>"
                   for _, label, model in columns)
    body = []
    for line in lines:
        cells = []
        for vslug, _, model in columns:
            r = results.get((vslug, model, line["n"]))
            if r and r["status"] == "ok":
                cells.append(f'<td><audio controls preload="none" src="{html.escape(r["file"])}"></audio>'
                             f'<br><small>first byte {r["ttfb_ms"]} ms</small></td>')
            else:
                cells.append(f'<td class="bad">{html.escape((r or {}).get("status", "not run"))}</td>')
        direction = "rtl" if line["lang"] == "ar" else "ltr"
        body.append(f'<tr><th class="line">line{line["n"]:02d} <small>{line["lang"]}/{line["kind"]}</small>'
                    f'<div dir="{direction}">{html.escape(line["text"])}</div></th>{"".join(cells)}</tr>')
    summary = "".join(
        f"<tr><td>{html.escape(v)}</td><td>{html.escape(m)}</td><td>{n}</td><td>{med}</td><td>{p90}</td></tr>"
        for v, m, n, med, p90 in summary_rows)
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Voice audition</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{ font: 15px/1.5 system-ui, sans-serif; margin: 16px; background: #fbfaf7; color: #1c1c1a; }}
table {{ border-collapse: collapse; }} th, td {{ border: 1px solid #d6d2c8; padding: 6px 8px; vertical-align: top; }}
th.line {{ text-align: start; min-width: 260px; max-width: 340px; font-weight: 400; background: #f1eee6; }}
th.line div {{ font-size: 17px; margin-top: 4px; }} audio {{ width: 220px; }} .bad {{ color: #9a2a2a; }}
.wrap {{ overflow-x: auto; }}
</style></head><body>
<h1>Voice audition</h1>
<p>Generated {datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")}. Original lines only: no verse or hadith text.
Listen across a row to compare voices and models on the same line.</p>
<h2>Time to first byte (ms)</h2>
<table><tr><th>Voice</th><th>Model</th><th>Requests</th><th>Median</th><th>Slowest decile</th></tr>{summary}</table>
<h2>Lines</h2>
<div class="wrap"><table><tr><th>Line</th>{head}</tr>{"".join(body)}</table></div>
</body></html>"""
    (out / "index.html").write_text(page, encoding="utf-8")


def run_live(args, lines, voices, models):
    key = common.load_eleven_key()
    if not key:
        print(f"No ElevenLabs key found ({common.key_source()}). Set ELEVEN_API_KEY or create the key file, "
              "or run with --dry-run.", file=sys.stderr)
        return 2
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    _, remaining, voices_report = account_report(key, voices)
    total = plan_report(lines, voices, models)
    budget = args.max_chars if args.max_chars is not None else remaining
    if budget is not None and total > budget and not args.force:
        print(f"\nThis run needs {total} characters but only {budget} are available. "
              "Narrow it (--voices, --models, --lines ar:1-3) or pass --max-chars / --force.", file=sys.stderr)
        return 3

    settings = voice_settings()
    results, rows, dead = {}, [], {}
    columns = []
    for vslug, label, vid in voices:
        for model in models:
            columns.append((vslug, label, model))
            for line in lines:
                name = f"{vslug}_{model}_line{line['n']:02d}.mp3"
                row = {"voice": vslug, "voice_id": vid, "model": model, "line": f"line{line['n']:02d}",
                       "lang": line["lang"], "chars": len(line["text"]), "status": "ok",
                       "ttfb_ms": "", "total_ms": "", "bytes": "", "file": name}
                if vslug in dead:
                    row.update(status=f"skipped: {dead[vslug]}", file="")
                else:
                    try:
                        ttfb, tot, audio = synthesize(key, vid, model, line, settings, args.format)
                        (out / name).write_bytes(audio)
                        row.update(ttfb_ms=round(ttfb * 1000), total_ms=round(tot * 1000), bytes=len(audio))
                        print(f"  {name}  first byte {row['ttfb_ms']} ms, {len(audio)} bytes")
                    except common.ApiError as err:
                        row.update(status=f"error {err.status}: {err.detail}", file="")
                        print(f"  {name}  FAILED {err}")
                        if err.status == 401:
                            print("The key was rejected. Stopping.", file=sys.stderr)
                            _write_csv(out, rows + [row])
                            return 4
                        if err.status in (402, 403, 404, 422):
                            dead[vslug] = f"voice not usable ({err.status})"
                results[(vslug, model, line["n"])] = row
                rows.append(row)

    _write_csv(out, rows)
    summary = []
    for vslug, label, model in columns:
        vals = sorted(r["ttfb_ms"] for r in rows
                      if r["voice"] == vslug and r["model"] == model and r["status"] == "ok")
        if vals:
            p90 = vals[min(len(vals) - 1, int(len(vals) * 0.9))]
            summary.append((vslug, model, len(vals), round(statistics.median(vals)), p90))
    write_index(out, lines, columns, results, summary)
    (out / "voices_report.json").write_text(json.dumps(
        {"voices": voices_report, "unusable_during_run": dead, "models": models}, indent=2), encoding="utf-8")
    ok = sum(1 for r in rows if r["status"] == "ok")
    print(f"\nDone: {ok}/{len(rows)} files. Open {out / 'index.html'} to listen; TTFB is in {out / 'results.csv'}.")
    if dead:
        print("Voices that could not be used: " + ", ".join(f"{k} ({v})" for k, v in dead.items()))
    return 0 if ok else 1


def _write_csv(out: Path, rows):
    fields = ["voice", "voice_id", "model", "line", "lang", "chars", "status", "ttfb_ms",
              "total_ms", "bytes", "file"]
    with (out / "results.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None) -> int:
    common.use_utf8_output()
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--dry-run", action="store_true", help="print the plan and character count, no API calls")
    p.add_argument("--out", default=str(common.REPO_ROOT.parent / "audition-out"), help="output folder")
    p.add_argument("--voices", help="comma list of: " + ",".join(v[0] for v in CANDIDATE_VOICES))
    p.add_argument("--models", help="comma list of model ids (default: flash_v2_5 and multilingual_v2)")
    p.add_argument("--lines", help="subset, per language position, e.g. ar:1-3,en:1")
    p.add_argument("--format", default="mp3_44100_128", help="ElevenLabs output_format")
    p.add_argument("--max-chars", type=int, help="refuse to run if the plan needs more characters")
    p.add_argument("--force", action="store_true", help="run even if the plan exceeds the quota")
    args = p.parse_args(argv)

    voices = CANDIDATE_VOICES
    if args.voices:
        want = [w.strip().lower() for w in args.voices.split(",") if w.strip()]
        unknown = [w for w in want if w not in {v[0] for v in CANDIDATE_VOICES}]
        if unknown:
            p.error(f"unknown voice(s): {', '.join(unknown)}")
        voices = [v for v in CANDIDATE_VOICES if v[0] in want]
    models = [m.strip() for m in args.models.split(",")] if args.models else list(BASE_MODELS)
    lines = parse_line_filter(args.lines, build_lines())
    if not lines:
        p.error("--lines selected nothing")
    return run_dry(args, lines, voices, models) if args.dry_run else run_live(args, lines, voices, models)


if __name__ == "__main__":
    sys.exit(main())
