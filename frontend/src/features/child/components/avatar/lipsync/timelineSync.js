// Keeps the text timeline of the reply that is being spoken in step with the audio that is
// actually playing (PLAN.md section 5.4). No DOM, no audio: it is fed messages (push), the audio
// gate each frame (onFrame) and asked where in the reply the sound is (position).
//
// The text times are exact relative to each other but their start on this machine's clock is not
// known: the data message and the audio travel apart. So the clock is latched to the audio:
//   - the audio gate opening after a silence is the first sound of the reply; it is set equal to
//     the first expected onset of the text (letter start plus a small offset for stops);
//   - a late `go` or late data still latches if that onset was not more than retroMs ago;
//   - after every pause longer than reanchorSilenceMs the clock is set again at the next onset,
//     snapped to the nearest expected onset within reanchorWindowMs;
//   - when the audio stops while the text says speech (a network stall) the clock is held, and the
//     next sound continues from where it stopped;
//   - a timeline never shown on its own: it needs its `go`, and a newer `go` drops older timelines
//     that never got one.
//
// Messages (JSON, from the agent on topic lk.lipsync):
//   {"v":1,"sp":"<speech id>","seq":0,"lang":"ar","t":[["م",0,139],...]}   characters, ms from the
//                                                                            first sample of the speech
//   {"v":1,"sp":"<id>","go":1}       speech starts
//   {"v":1,"sp":"<id>","stop":1}     speech interrupted or over

import { TIMELINE } from './lipsyncConfig.js';
import { KIND, buildTrack } from './arabicText.js';

const T = TIMELINE;

export const PHASE = Object.freeze({ IDLE: 0, ARMED: 1, LOCKED: 2, STALLED: 3, AUDIO: 4 });

const MAX_ITEMS = 2000;
const MAX_LINES = 6;
const NEVER = -1e12;

/** The expected onset (ms in the track) nearest to `ms`. */
function nearestOnset(track, ms) {
  let best = ms;
  let bestD = Infinity;
  for (const o of track.onsets) {
    const d = Math.abs(o - ms);
    if (d < bestD) {
      bestD = d;
      best = o;
    }
  }
  return best;
}

export class TimelineSync {
  constructor() {
    this.lines = new Map(); // speech id -> { items, lang, goAt, track, dirty, createdAt }
    this.reset();
  }

  reset() {
    this.cur = null; // the line being spoken
    this.phase = PHASE.IDLE;
    this.offset = 0; // position(now) = now - offset
    this.gate = false;
    this.closedAt = NEVER;
    this.closePos = -1;
    this.holdPos = -1; // where a stall holds the clock (the end of a pause that ran long, else closePos)
    this.closedMinRms = 1; // the quietest frame since the gate shut
    this.lastOnsetMs = NEVER;
    this.leftAt = -1; // when the agent left "speaking" (-1 while it is speaking or unknown)
  }

  /** The track being followed, or null. */
  get track() {
    return this.cur ? this.cur.track : null;
  }

  /** Forget the timeline being followed (the speech ended). Timelines not yet started stay. */
  clear() {
    if (this.cur) {
      for (const [k, v] of this.lines) if (v === this.cur) this.lines.delete(k);
    }
    this.cur = null;
    this.phase = PHASE.IDLE;
    this.leftAt = -1;
  }

  /** The agent state changed. A speech is over once it has not been speaking for endStateMs. */
  agentState(speaking, nowMs) {
    if (speaking) this.leftAt = -1;
    else if (this.leftAt < 0) this.leftAt = nowMs;
  }

  /** @param {object|string} msg one lk.lipsync message @param {number} nowMs */
  push(msg, nowMs) {
    if (typeof msg === 'string') {
      try {
        msg = JSON.parse(msg);
      } catch {
        return;
      }
    }
    if (!msg || typeof msg !== 'object' || msg.v !== 1) return;
    const sp = msg.sp === undefined || msg.sp === null ? '?' : String(msg.sp);

    if (msg.stop) {
      if (this.cur && (this.cur.sp === sp || sp === '?')) this.clear();
      else this.lines.delete(sp);
      return;
    }
    if (Array.isArray(msg.t)) {
      let line = this.lines.get(sp);
      // More packets of an unnamed ('?') timeline that a go has already taken over (see go()).
      if (!line && sp === '?' && msg.seq > 0 && this.cur && this.cur.unnamed) line = this.cur;
      if (!line || msg.seq === 0 || msg.seq === undefined) {
        // A new timeline replaces an old one of the same id (and a '?' one always starts afresh).
        if (line && line === this.cur) this.cur = null;
        line = { sp, items: [], lang: 'ar', goAt: -1, track: null, dirty: true, createdAt: nowMs };
        this.lines.set(sp, line);
        this.prune();
      }
      if (msg.lang) line.lang = msg.lang === 'en' ? 'en' : 'ar';
      for (const it of msg.t) {
        if (!Array.isArray(it) || line.items.length >= MAX_ITEMS) continue;
        const ch = it[0];
        const a = +it[1];
        const d = +it[2];
        if (typeof ch !== 'string' || !Number.isFinite(a) || !Number.isFinite(d)) continue;
        line.items.push([ch, a, d]);
      }
      line.dirty = true;
      if (this.cur === line) {
        this.rebuild(line);
        this.tryLatch(nowMs);
      }
    }
    if (msg.go) this.go(sp, nowMs);
  }

  go(sp, nowMs) {
    let line = this.lines.get(sp);
    const unnamed = this.lines.get('?');
    if (!line && unnamed && unnamed.goAt < 0) {
      // The agent could not name the speech its characters belong to (it sent them as '?'): the
      // newest such timeline that has not started is this speech's.
      this.lines.delete('?');
      unnamed.sp = sp;
      unnamed.unnamed = true;
      this.lines.set(sp, unnamed);
      line = unnamed;
    }
    if (!line) {
      // The data has not arrived yet: it will latch when it does.
      line = { sp, items: [], lang: 'ar', goAt: -1, track: null, dirty: true, createdAt: nowMs };
      this.lines.set(sp, line);
    }
    if (this.cur === line && line.goAt >= 0) return; // a repeated go
    // A newer go drops the timelines that never got one.
    for (const [k, v] of this.lines) if (v !== line && v.goAt < 0 && v.createdAt <= nowMs) this.lines.delete(k);
    line.goAt = nowMs;
    this.cur = line;
    this.leftAt = -1;
    this.phase = PHASE.ARMED;
    this.offset = 0;
    this.rebuild(line);
    this.tryLatch(nowMs);
  }

  prune() {
    while (this.lines.size > MAX_LINES) {
      const first = this.lines.keys().next().value;
      if (this.lines.get(first) === this.cur) break;
      this.lines.delete(first);
    }
  }

  rebuild(line) {
    if (!line.dirty && line.track) return;
    line.track = line.items.length ? buildTrack(line.items, { lang: line.lang }) : null;
    line.dirty = false;
  }

  /** Called when a go or data arrives while armed: latch to an onset that has already happened. */
  tryLatch(nowMs) {
    const line = this.cur;
    if (!line || !line.track || !line.track.onsets.length) return;
    if (this.phase !== PHASE.ARMED) return;
    if (this.gate) {
      if (nowMs - this.lastOnsetMs <= T.retroMs) this.lock(this.lastOnsetMs, line.track.onsets[0]);
      else this.phase = PHASE.AUDIO; // too late: audio-only until the next pause
    }
  }

  lock(audioMs, expectedMs) {
    this.offset = audioMs - (expectedMs + T.latchOffsetMs);
    this.phase = PHASE.LOCKED;
  }

  /**
   * Call once per frame, before position().
   * @param {boolean} gateActive the audio is above the voice gate
   * @param {number} nowMs
   * @param {number} [rms] loudness of this frame; a gap of exact silence is told from a gate dropout
   */
  onFrame(gateActive, nowMs, rms = 0) {
    if (!gateActive && this.gate) this.closedMinRms = rms;
    else if (!gateActive && rms < this.closedMinRms) this.closedMinRms = rms;
    if (gateActive && !this.gate) {
      const silence = nowMs - this.closedAt;
      this.onOnset(nowMs, silence);
    } else if (!gateActive && this.gate) {
      this.closedAt = nowMs;
      this.closePos = this.phase === PHASE.LOCKED ? nowMs - this.offset : -1;
    }
    this.gate = gateActive;
    if (!this.cur) return;

    if (this.leftAt >= 0 && nowMs - this.leftAt > T.endStateMs) {
      this.clear();
      return;
    }
    const track = this.cur.track;
    if (this.phase === PHASE.LOCKED && track) {
      const pos = nowMs - this.offset;
      if (pos > track.endMs + T.endAfterMs) {
        this.clear();
        return;
      }
      // The audio stopped while the text says speech: hold the clock. If the silence belongs to a
      // pause of the text and outlasted it, the hold is at the end of that pause.
      const span = nowMs - this.closedAt;
      if (!gateActive && span > T.stallMs && !this.silenceExpected(track, this.closePos, span)) {
        this.phase = PHASE.STALLED;
        this.holdPos = Math.max(this.closePos, this.pauseEnd(track, this.closePos, span));
      }
    }
  }

  onOnset(nowMs, silence) {
    if (silence >= T.gateSilenceMs) this.lastOnsetMs = nowMs;
    const line = this.cur;
    const track = line ? line.track : null;
    if (!track) return;
    switch (this.phase) {
      case PHASE.ARMED:
        if (silence >= T.gateSilenceMs && track.onsets.length) this.lock(nowMs, track.onsets[0]);
        break;
      case PHASE.STALLED:
        // The sound resumed: carry on from where it stopped, or, when the silence was a pause of the
        // text that ran long, from the onset after that pause.
        if (this.holdPos > this.closePos) this.lock(nowMs, nearestOnset(track, this.holdPos));
        else this.offset = nowMs - this.closePos;
        this.phase = PHASE.LOCKED;
        break;
      case PHASE.AUDIO:
        if (silence >= T.gateSilenceMs) this.snap(track, nowMs, nowMs - line.goAt, false);
        break;
      case PHASE.LOCKED:
        if (silence >= T.reanchorSilenceMs) {
          // Between reanchorSilenceMs and stallMs the gate also drops out inside a quiet vowel (more at 48 kHz),
          // so only digital silence counts as a stall there.
          const stalled = silence >= T.stallMs || this.closedMinRms < T.hardSilenceRms;
          if (stalled && this.closePos >= 0 && !this.silenceExpected(track, this.closePos, silence)) {
            // A stall: hold the clock over it, from the end of the pause it ran past if there is one.
            const end = this.pauseEnd(track, this.closePos, silence);
            if (end > this.closePos) this.lock(nowMs, nearestOnset(track, end));
            else this.offset = nowMs - this.closePos;
          } else if (!T.reanchorPausesOnly || this.closePos < 0 || this.pauseEnd(track, this.closePos, silence) >= 0) {
            // Re-anchor only after a pause of the text: a gap inside a word (a stop, a voiceless
            // consonant) has no expected onset of its own, and snapping it to the onset after the
            // next pause would move the clock the wrong way.
            this.snap(track, nowMs, nowMs - this.offset, true);
          }
        }
        break;
      default:
        break;
    }
  }

  /** Set the clock at the expected onset nearest to `predicted` (ms in the track), if close enough. */
  snap(track, nowMs, predicted, keepIfFar) {
    let best = -1;
    let bestD = 1e9;
    for (const o of track.onsets) {
      const d = Math.abs(o + T.latchOffsetMs - predicted);
      if (d < bestD) {
        bestD = d;
        best = o;
      }
    }
    if (best >= 0 && bestD <= T.reanchorWindowMs) {
      if (keepIfFar) {
        // Locked and re-anchoring: the clock only drifts a little, so a large correction is the gate
        // onset jittering (it moves with the sample rate and the window), not the reply moving.
        const before = this.offset;
        this.lock(nowMs, best);
        const step = this.offset - before;
        if (Math.abs(step) > T.reanchorMaxStepMs) this.offset = before + Math.sign(step) * T.reanchorMaxStepMs;
      } else {
        this.lock(nowMs, best);
      }
    } else if (!keepIfFar) this.phase = PHASE.AUDIO;
  }

  /**
   * The end of the pause of the text that a silence of the audio at [pos, pos + span] belongs to, or
   * -1 when it belongs to none. It belongs to a pause it overlaps, and to a pause that starts at most
   * pauseAheadMs after the sound stopped: the voice often stops a little before the pause the
   * alignment gives (a silent final letter, a fading final consonant, an English silent e). That
   * second rule is off for digital silence (exact zeros): a TTS pause is never that quiet, a network
   * stall is.
   */
  pauseEnd(track, pos, span) {
    if (pos < 0) return -1;
    const ahead = this.closedMinRms >= T.hardSilenceRms;
    const a = pos - 60;
    const b = Math.max(pos + span, pos + T.pauseAheadMs) + 60;
    for (const s of track.segs) {
      if (s.t0 > b) break;
      if (s.kind !== KIND.SIL || s.t1 < a) continue;
      // Overlapping: the silence must really overlap the pause of the text, not just lie next to it.
      const ov = Math.min(s.t1, pos + span) - Math.max(s.t0, pos);
      if (ov >= Math.min(T.pauseOverlapMs, 0.5 * Math.min(span, s.t1 - s.t0))) return s.t1;
      if (ahead && s.t0 >= pos && s.t0 - pos <= T.pauseAheadMs) return s.t1;
    }
    return -1;
  }

  /**
   * Is the silence in the audio at [pos, pos + span] one the text explains? A pause of the text
   * explains it (pauseEnd) until the silence outlasts that pause by pauseOverrunMs; so does the end
   * of the reply. A silence inside speech is explained only if the text has less than stallVowelMs of
   * vowel in it (0 turns that off: any silence of stallMs inside speech is a stall).
   */
  silenceExpected(track, pos, span) {
    if (pos < 0) return true;
    const endAhead = this.closedMinRms >= T.hardSilenceRms ? T.pauseAheadMs : 20;
    if (pos + span < track.startMs || pos > track.endMs - endAhead) return true;
    const end = this.pauseEnd(track, pos, span);
    if (end >= 0) return pos + span <= end + T.pauseOverrunMs;
    const b = pos + span + 60;
    let vowel = 0;
    const va = pos + 10;
    const vb = pos + span - 10;
    for (const s of track.segs) {
      if (s.t0 > b) break;
      if (s.kind === KIND.VOWEL && s.t1 > va && s.t0 < vb) vowel += Math.min(s.t1, vb) - Math.max(s.t0, va);
    }
    return vowel < T.stallVowelMs;
  }

  /** Where in the reply the sound is now, in ms from its first sample, or -1 for no text timing. */
  position(nowMs) {
    return this.phase === PHASE.LOCKED ? nowMs - this.offset : -1;
  }
}
