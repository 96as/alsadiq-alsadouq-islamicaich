"""Measure what the compliance guards add per reply chunk on the TTS path.

No network, no Django, no livekit: it times the pure-Python layers the voice path runs
between the LLM and the TTS:

  1. speech cleaner (tts_text.TTSTextStream), without and with the scripture-mark pass
  2. tts_node guards (scripture_guard: attribution check + scripture filter)

Replies are placeholder prose (no scripture). Chunk sizes mimic LLM token streaming.

Run from backend/:  PYTHONUTF8=1 python ../scripts/guard_latency_bench.py
"""
from __future__ import annotations

import asyncio
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

from conversation.agent import scripture_guard  # noqa: E402
from conversation.agent.tts_text import TTSTextStream  # noqa: E402

EN = (
    "Hello my friend, that sounds like a really fun day at school. I am glad you told me about "
    "your cat and the little test on Tuesday. Tell me more about what happened with 12 of your "
    "classmates, and how did it feel when the teacher said well done? "
) * 3
AR = (
    "أهلا يا صديقي، "
    "يبدو أن يومك كان "
    "ممتعا جدا في المدرسة. "
) * 8


def chunks(text: str, size: int) -> list[str]:
    return [text[i:i + size] for i in range(0, len(text), size)]


def time_cleaner(text: str, size: int, with_scripture: bool, runs: int) -> list[float]:
    """Seconds per chunk (feed) for each chunk of each run."""
    samples: list[float] = []
    for _ in range(runs):
        s = TTSTextStream("en" if text is EN else "ar")
        if not with_scripture:
            s._scripture_pass = lambda cleaned: cleaned  # type: ignore[method-assign]
            s._scripture_flush = lambda: ""  # type: ignore[method-assign]
        for c in chunks(text, size):
            t0 = time.perf_counter()
            s.feed(c)
            samples.append(time.perf_counter() - t0)
        s.flush()
    return samples


async def _agen(parts):
    for p in parts:
        yield p


async def time_tts_node_guards(text: str, size: int, runs: int) -> list[float]:
    """Seconds spent in the guards per chunk (time between chunk in and chunk out)."""
    samples: list[float] = []
    lic = lambda: frozenset()  # noqa: E731
    for _ in range(runs):
        parts = chunks(text, size)
        stream = scripture_guard.filter_scripture_stream(
            scripture_guard.guard_attribution_stream(
                _agen(parts), lic, "en", count=False), count=False)
        t_total0 = time.perf_counter()
        n_out = 0
        async for _out in stream:
            n_out += 1
        samples.append((time.perf_counter() - t_total0) / max(len(parts), 1))
    return samples


async def words_held_before_first_output(text: str, size: int) -> tuple[int, int]:
    """How much text the tts_node guards take in before the first piece comes out.

    The attribution check holds back a short tail of words that could still turn into a
    trigger phrase. This is the real cost on time-to-first-audio: it is waiting for the
    next few LLM tokens, not CPU time. Returns (chars, words) fed before the first output.
    """
    fed = 0
    parts = chunks(text, size)
    seen: list[str] = []

    async def source():
        nonlocal fed
        for part in parts:
            fed += len(part)
            seen.append(part)
            yield part

    stream = scripture_guard.filter_scripture_stream(
        scripture_guard.guard_attribution_stream(source(), lambda: frozenset(), "en", count=False),
        count=False)
    async for _first in stream:
        break
    return fed, len("".join(seen).split())


def us(values: list[float]) -> str:
    v = sorted(values)
    p99 = v[min(len(v) - 1, int(len(v) * 0.99))]
    return f"mean {statistics.mean(v) * 1e6:7.1f} us   p50 {statistics.median(v) * 1e6:7.1f} us   p99 {p99 * 1e6:8.1f} us"


def main() -> None:
    runs = 200
    print(f"python {sys.version.split()[0]}  runs per case: {runs}")
    for label, text in (("English", EN), ("Arabic", AR)):
        print(f"\n{label} reply, {len(text)} chars")
        for size in (4, 12, 40):
            base = time_cleaner(text, size, False, runs)
            full = time_cleaner(text, size, True, runs)
            guards = asyncio.run(time_tts_node_guards(text, size, runs))
            extra = statistics.mean(full) - statistics.mean(base)
            print(f"  chunk {size:>2} chars")
            print(f"    cleaner without scripture pass : {us(base)}")
            print(f"    cleaner with scripture pass    : {us(full)}")
            print(f"    added by the scripture pass    : {extra * 1e6:7.1f} us per chunk")
            print(f"    tts_node guards (per chunk)    : {us(guards)}")
            chars, words = asyncio.run(words_held_before_first_output(text, size))
            print(f"    text taken in before 1st output: {chars} chars (~{words} words)")


if __name__ == "__main__":
    main()
