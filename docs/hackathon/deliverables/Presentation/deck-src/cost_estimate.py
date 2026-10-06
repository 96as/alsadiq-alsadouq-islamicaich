"""USD cost estimate per session and per month. An ESTIMATE, not a measured cost.

Measured units (from the repository) x the providers' public prices (checked 6 Oct 2026).
Every value that is not measured is marked ASSUMPTION. Run: python cost_estimate.py
Every displayed figure is rounded UP at its display step (up()), so no shown bound is below the computed value.
"""
import math

CHECKED = "6 Oct 2026"

# ---------------------------------------------------------------- prices (public, checked 6 Oct 2026)
# OpenAI, https://platform.openai.com/docs/pricing (standard tier, per 1M tokens)
GPT54MINI_IN = 0.75 / 1e6
GPT54MINI_OUT = 4.50 / 1e6
# OpenAI's own estimate for gpt-4o-mini-transcribe (same page): "$0.003 / minute"
STT_PER_MIN = 0.003
# ElevenLabs, https://elevenlabs.io/pricing/api : Flash / Turbo, $0.04 per 1K characters, every plan
TTS_PER_CHAR = 0.04 / 1000
# LiveKit Cloud, https://livekit.com/pricing : Ship plan overage
LK_PARTICIPANT_MIN = 0.0005
LK_AGENT_SESSION_MIN = 0.01

# ---------------------------------------------------------------- measured units
# docs/hackathon/eval-reports/lead-summary.json, "all", after: the mean per EVAL RUN (90 runs: 94 agent calls and
# 84 judge calls, from "files"). The eval runner adds the judge model's usage to the run's count, so this is the
# agent plus the judge, not the agent's tokens per call. Used as an UPPER BOUND for one agent call. It bounds a
# single-turn call only; late calls in a long session carry more history (AGENT_PROMPT_TOK_FULL below).
# The repository has no agent-only per-call figure (the raw reports do not keep the judge's usage apart).
EVAL_RUN_PROMPT_TOK = 6526
EVAL_RUN_COMPLETION_TOK = 109
# docs/hackathon/latency/LOAD-REHEARSAL.md: greeting + 2 child turns = about 300 ElevenLabs characters and
# about 8 OpenAI chat calls (about 4 in the agent, about 4 in post-session reporting), one STT stream
SHORT = dict(agent_calls=4, report_calls=4, tts_chars=300)

# ---------------------------------------------------------------- assumptions
# Full session: 5 minutes is the demo cap (DEMO_SESSION_MAX_SECONDS=300), about 10 child turns. Family sessions
# may run longer; the 100-family figures assume the same 5-minute cap, so they are not an upper bound for longer sessions.
# 1,500 to 2,500 characters is LOAD-REHEARSAL's own estimate for a full session (not measured); we take 2,500.
FULL = dict(agent_calls=12, report_calls=4, tts_chars=2500)
AGENT_PROMPT_TOK_FULL = 8000          # ASSUMPTION: longer history late in a session (the eval-run bound is 6,526)
REPORT_TOK = {"low": (1000, 200), "high": (6000, 800)}   # ASSUMPTION: input, output tokens per reporting call
LK_MIN = {"low": 1.5, "high": 5.0}    # ASSUMPTION: session length in minutes (short session .. the demo cap)
# ASSUMPTION: billed audio minutes = the session length. STT_REALTIME defaults on (backend/conversation/agent/
# entrypoint.py), so the realtime transcription stream is open for the whole session, not only while the child speaks.
STT_MIN = dict(LK_MIN)
LK_PARTICIPANTS = 2                   # the child's browser and the self-hosted agent
# high side also counts LiveKit agent-session minutes, in case LiveKit bills a self-hosted agent that way


def session(level):
    s = SHORT if level == "low" else FULL
    p_tok = EVAL_RUN_PROMPT_TOK if level == "low" else AGENT_PROMPT_TOK_FULL
    agent = s["agent_calls"] * (p_tok * GPT54MINI_IN + EVAL_RUN_COMPLETION_TOK * GPT54MINI_OUT)
    ri, ro = REPORT_TOK[level]
    report = s["report_calls"] * (ri * GPT54MINI_IN + ro * GPT54MINI_OUT)
    stt = STT_MIN[level] * STT_PER_MIN
    tts = s["tts_chars"] * TTS_PER_CHAR
    lk = LK_PARTICIPANTS * LK_MIN[level] * LK_PARTICIPANT_MIN
    if level == "high":
        lk += LK_MIN[level] * LK_AGENT_SESSION_MIN
    items = {"agent LLM": agent, "reporting LLM": report, "STT": stt, "TTS": tts, "LiveKit": lk}
    return items, sum(items.values())


SCENARIOS = {
    # ASSUMPTION: 30 judges, 2 to 4 sessions each, over the judging window (7 to 22 Oct)
    "30 judges (judging window)": (30 * 2, 30 * 4),
    # ASSUMPTION: 100 families, one child each, 12 to 20 sessions a month (3 to 5 a week), each within the 5-minute cap
    "100 families (per month)": (100 * 12, 100 * 20),
}

# display steps: line items, per session, the judging window, per month
STEP = {"item": 0.001, "session": 0.01, "judges": 1, "families": 10}


def up(x, step):
    """x rounded UP to a multiple of step; the guard keeps exact values (0.015, 0.100) from creeping up a step."""
    return math.ceil(round(x / step, 9)) * step


def fmt(x, step):
    decimals = max(0, -int(math.floor(math.log10(step)))) if step < 1 else 0
    return f"{up(x, step):,.{decimals}f}"


def display():
    """The figures every document shows, all rounded up: {key: (low, high)} as strings."""
    lo_items, lo = session("low")
    hi_items, hi = session("high")
    (j_lo, j_hi), (f_lo, f_hi) = SCENARIOS.values()
    out = {k: (fmt(lo_items[k], STEP["item"]), fmt(hi_items[k], STEP["item"])) for k in lo_items}
    out["session"] = (fmt(lo, STEP["session"]), fmt(hi, STEP["session"]))
    out["judges"] = (fmt(j_lo * lo, STEP["judges"]), fmt(j_hi * hi, STEP["judges"]))
    out["families"] = (fmt(f_lo * lo, STEP["families"]), fmt(f_hi * hi, STEP["families"]))
    return out


if __name__ == "__main__":
    lo_items, lo = session("low")
    hi_items, hi = session("high")
    shown = display()
    print(f"Estimate, prices checked {CHECKED}. Not a measured cost.")
    print(f"{'line item':16s} {'low':>9s} {'high':>9s}   shown (rounded up)")
    for k in lo_items:
        print(f"{k:16s} {lo_items[k]:9.4f} {hi_items[k]:9.4f}   {shown[k][0]} to {shown[k][1]}")
    print(f"{'per session':16s} {lo:9.4f} {hi:9.4f}   ${shown['session'][0]} to ${shown['session'][1]}")
    for (name, (n_lo, n_hi)), key in zip(SCENARIOS.items(), ("judges", "families")):
        print(f"{name}: {n_lo}-{n_hi} sessions -> ${n_lo * lo:,.2f} to ${n_hi * hi:,.2f}"
              f"   shown ${shown[key][0]} to ${shown[key][1]}")
