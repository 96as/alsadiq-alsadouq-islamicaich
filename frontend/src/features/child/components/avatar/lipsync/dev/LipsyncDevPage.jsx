import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import Avatar from '../../Avatar';
import { BlinkScheduler } from '../blinkScheduler.js';
import { analyseBuffer } from '../lipsyncEngine.js';
import { createVisemeDriver } from '../visemeDriver.js';
import { VISEMES } from '../visemes.js';
import Mouth from './Mouth.jsx';
import {
  DEFAULT_EVAL_CLIP,
  EVAL_CLIPS,
  loadAlignment,
  newTimelineSink,
  replayEvents,
  replayTimeline,
  stopTimeline,
} from './evalClips.js';

// Audition clips live in frontend/dev-audio/ (gitignored, never committed). Vite serves them
// from the project root in dev; this page is only mounted when import.meta.env.DEV.
const CLIP_URLS = import.meta.glob('/dev-audio/*.mp3', { query: '?url', import: 'default', eager: true });
const LINE_FILES = import.meta.glob('/dev-audio/lines.json', { eager: true, import: 'default' });
const LINES = Object.values(LINE_FILES)[0] ?? {};

const MP3_CLIPS = Object.entries(CLIP_URLS)
  .map(([path, url]) => {
    const name = path.split('/').pop().replace(/\.mp3$/, '');
    const lineKey = name.match(/line\d+$/)?.[0];
    return {
      name,
      url,
      text: LINES[lineKey]?.text ?? '',
      kind: LINES[lineKey]?.kind ?? '',
      lang: /_ar_|abdullah/.test(name) ? 'ar' : 'en',
    };
  })
  .sort((a, b) => a.name.localeCompare(b.name));
// The evaluation clips (dev-audio/eval-ar/ and eval-en/, with their alignments) come first.
const CLIPS = [...EVAL_CLIPS, ...MP3_CLIPS];

const COLORS = VISEMES.map((_, i) => `hsl(${Math.round((i * 360) / VISEMES.length)} 70% ${i === 0 ? 85 : 52}%)`);

/** Run-length list of the dominant viseme per frame, short runs dropped. */
function dominantRuns(frames, minWeight = 0.25, minFrames = 3) {
  const runs = [];
  for (const f of frames) {
    let best = 0;
    for (let i = 1; i < f.weights.length; i++) if (f.weights[i] > f.weights[best]) best = i;
    const name = f.weights[best] >= minWeight ? VISEMES[best] : 'sil';
    const last = runs[runs.length - 1];
    if (last && last.name === name) last.frames++;
    else runs.push({ name, frames: 1, t: f.t });
  }
  const kept = runs.filter((r) => r.frames >= minFrames);
  // Merge neighbours that became equal after dropping the short runs.
  return kept.reduce((acc, r) => {
    const last = acc[acc.length - 1];
    if (last && last.name === r.name) last.frames += r.frames;
    else acc.push({ ...r });
    return acc;
  }, []);
}

async function decodeToMono(arrayBuffer) {
  const Ctor = window.AudioContext || window.webkitAudioContext;
  const ctx = new Ctor();
  try {
    const audio = await ctx.decodeAudioData(arrayBuffer);
    const mono = new Float32Array(audio.length);
    for (let c = 0; c < audio.numberOfChannels; c++) {
      const data = audio.getChannelData(c);
      for (let i = 0; i < mono.length; i++) mono[i] += data[i] / audio.numberOfChannels;
    }
    return { pcm: mono, sampleRate: audio.sampleRate };
  } finally {
    ctx.close().catch(() => {});
  }
}

async function analyseUrl(url, opts) {
  const res = await fetch(url);
  const { pcm, sampleRate } = await decodeToMono(await res.arrayBuffer());
  return analyseBuffer(pcm, sampleRate, opts);
}

function Eyes({ blink }) {
  const lid = 1 - blink; // 1 open, 0 closed
  return (
    <svg viewBox="0 0 200 60" width={160} height={48} role="img" aria-label="eyes">
      {[55, 145].map((x) => (
        <g key={x}>
          <ellipse cx={x} cy={30} rx={22} ry={Math.max(1.5, 16 * lid)} fill="#fff" stroke="#3b2a20" strokeWidth={3} />
          <circle cx={x} cy={30} r={Math.max(0, 8 * lid)} fill="#3b2a20" />
        </g>
      ))}
    </svg>
  );
}

/** The live panel owns the per-frame state, so the avatar canvas next to it never re-renders. */
function LivePanel({ getLipsync, reduced }) {
  const [view, setView] = useState(null);
  const blinker = useMemo(() => new BlinkScheduler(), []);

  useEffect(() => {
    let raf = 0;
    let last = performance.now();
    let lastPhraseEnds = 0;
    const tick = (now) => {
      const dt = Math.min(0.1, (now - last) / 1000);
      last = now;
      const r = getLipsync();
      if (r && r.phraseEnds !== lastPhraseEnds) {
        lastPhraseEnds = r.phraseEnds;
        blinker.notifyPhraseEnd();
      }
      const blink = blinker.update(dt, { stress: r ? r.stress : 0, reduced });
      setView({
        weights: r ? Float32Array.from(r.weights) : null,
        level: r ? r.level : 0,
        stress: r ? r.stress : 0,
        active: r ? r.active : false,
        rms: r ? r.features.rms : 0,
        voicing: r ? r.features.voicing : 0,
        f1: r ? r.features.f1 : 0,
        f2: r ? r.features.f2 : 0,
        blink,
        blinks: blinker.blinks,
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [getLipsync, blinker, reduced]);

  const w = view?.weights ?? null;
  const rest = useMemo(() => {
    const a = new Float32Array(VISEMES.length);
    a[0] = 1;
    return a;
  }, []);
  return (
    <div className="flex flex-col gap-3" data-live-panel="">
      <div className="flex flex-wrap items-end gap-4">
        <Mouth weights={w ?? rest} size={220} label="live mouth" />
        <Eyes blink={view?.blink ?? 0} />
        <div className="text-xs leading-5 text-slate-300">
          <div>{w ? 'analysing' : 'no audio context yet (tap Play)'}</div>
          <div>level {view ? view.level.toFixed(2) : '0.00'} · stress {view ? view.stress.toFixed(2) : '0.00'}</div>
          <div>
            rms {view ? view.rms.toFixed(3) : '0'} · voicing {view ? view.voicing.toFixed(2) : '0'} · f1/f2{' '}
            {view ? `${view.f1.toFixed(0)}/${view.f2.toFixed(0)}` : '0/0'}
          </div>
          <div>blinks {view ? view.blinks : 0}</div>
        </div>
      </div>
      <div className="flex h-28 items-end gap-1" role="img" aria-label="viseme weights">
        {VISEMES.map((name, i) => (
          <div key={name} className="flex w-9 flex-col items-center justify-end gap-1">
            <div
              className="w-full rounded-t"
              style={{ height: `${Math.round((w ? w[i] : i === 0 ? 1 : 0) * 80)}px`, background: COLORS[i] }}
              data-viseme-bar={name}
            />
            <span className="text-[10px] text-slate-300">{name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Timeline({ analysis, audioRef, onSeek }) {
  const canvasRef = useRef(null);
  const cursorRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !analysis) return;
    const ctx = canvas.getContext('2d');
    const { width, height } = canvas;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, width, height);
    const n = analysis.frames.length;
    const colW = Math.max(1, width / n);
    const plotH = height - 40;
    // Stacked weights.
    analysis.frames.forEach((f, k) => {
      let y = plotH;
      for (let i = VISEMES.length - 1; i >= 1; i--) {
        const h = f.weights[i] * plotH;
        if (h < 0.5) continue;
        y -= h;
        ctx.fillStyle = COLORS[i];
        ctx.fillRect((k / n) * width, y, colW + 0.5, h);
      }
    });
    // Loudness, stress and blink-relevant marks underneath.
    ctx.fillStyle = '#94a3b8';
    analysis.frames.forEach((f, k) => {
      const h = Math.min(1, f.rms * 6) * 30;
      ctx.fillRect((k / n) * width, height - h, colW + 0.5, h);
    });
    ctx.fillStyle = '#fbbf24';
    analysis.frames.forEach((f, k) => {
      if (f.stress > 0.5) ctx.fillRect((k / n) * width, plotH + 2, colW + 0.5, 3);
    });
    ctx.fillStyle = '#e2e8f0';
    for (let s = 0; s < analysis.duration; s += 0.5) {
      ctx.fillRect((s / analysis.duration) * width, plotH, 1, s % 1 === 0 ? 8 : 4);
    }
  }, [analysis]);

  useEffect(() => {
    let raf = 0;
    const tick = () => {
      const a = audioRef.current;
      const el = cursorRef.current;
      if (a && el && analysis) el.style.left = `${(a.currentTime / analysis.duration) * 100}%`;
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [analysis, audioRef]);

  return (
    <div
      className="relative w-full cursor-pointer overflow-hidden rounded-lg"
      onClick={(e) => {
        if (!analysis) return;
        const r = e.currentTarget.getBoundingClientRect();
        onSeek(((e.clientX - r.left) / r.width) * analysis.duration);
      }}
    >
      <canvas ref={canvasRef} width={1200} height={180} className="block h-44 w-full" data-timeline="" />
      <div ref={cursorRef} className="pointer-events-none absolute inset-y-0 w-0.5 bg-white" />
    </div>
  );
}

/**
 * Dev-only page (route /dev/lipsync, only mounted when import.meta.env.DEV). Plays a clip through
 * the live Web Audio driver and shows the 14 viseme weights, a flat mouth, blinking eyes, an
 * offline timeline of the same clip, a strip of mouths over a time window, and optionally the
 * real avatar. URL options: ?clip=<name>  ?avatar=1  ?start=<seconds for the strip>
 */
export default function LipsyncDevPage() {
  const [params] = useSearchParams();
  const audioRef = useRef(null);
  const driverRef = useRef(null);
  const [clip, setClip] = useState(
    CLIPS.find((c) => c.name === params.get('clip')) ?? DEFAULT_EVAL_CLIP ?? CLIPS[0] ?? null,
  );
  // The text timing: the clip's alignment is delivered as the agent would (lk.lipsync). Off, the
  // mouth follows the audio alone. ?timeline=0 starts with it off.
  const [timelineOn, setTimelineOn] = useState(params.get('timeline') !== '0');
  const [aligned, setAligned] = useState({ name: '', data: null });
  const sink = useMemo(() => newTimelineSink(), []);
  const spRef = useRef('');
  const playCount = useRef(0);
  // Scrub: show the offline analysis at a fixed time instead of the live audio (screenshots, strips).
  const [scrubT, setScrubT] = useState(null);
  const analysisRef = useRef(null);
  const scrubRef = useRef(null);
  const scrubResult = useRef({
    weights: null,
    stress: 0,
    level: 0,
    speaking: true,
    active: true,
    phraseEnds: 0,
    features: { rms: 0, voicing: 0, f1: 0, f2: 0 },
  });
  const lang = clip?.lang ?? 'en';
  const alignment = clip && aligned.name === clip.name ? aligned.data : null;
  const [src, setSrc] = useState(clip?.url ?? '');
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState('');
  const [playing, setPlaying] = useState(false);
  const [showAvatar, setShowAvatar] = useState(params.get('avatar') === '1');
  const [stripStart, setStripStart] = useState(Number(params.get('start')) || 0);
  const [reduced, setReduced] = useState(
    () => typeof window !== 'undefined' && Boolean(window.matchMedia?.('(prefers-reduced-motion: reduce)').matches),
  );

  // One driver for the page's single audio element (an element can feed Web Audio once). It is
  // made again when the language changes (the vowel mode is chosen when it is made).
  useEffect(() => {
    const el = audioRef.current;
    if (!el) return undefined;
    const driver = createVisemeDriver({ source: el, lang, timeline: sink });
    driverRef.current = driver;
    return () => {
      driverRef.current = null;
      driver?.dispose();
    };
  }, [lang, sink]);

  // What the avatar and the panel read: the live driver, or the offline frame at the scrub time.
  const getLipsync = useCallback(() => {
    const t = scrubRef.current;
    const a = analysisRef.current;
    if (t !== null && a) {
      const f = a.frames[Math.max(0, Math.min(a.frames.length - 1, Math.round(t * a.fps) - 1))];
      const r = scrubResult.current;
      r.weights = f.weights;
      r.stress = f.stress;
      r.level = f.level;
      r.active = f.active;
      r.features.rms = f.rms;
      r.features.voicing = f.voicing;
      r.features.f1 = f.f1;
      r.features.f2 = f.f2;
      return r;
    }
    return driverRef.current?.read() ?? null;
  }, []);
  const getLevel = useCallback(() => {
    const r = getLipsync();
    return r ? r.features.rms : -1;
  }, [getLipsync]);

  useEffect(() => {
    let cancelled = false;
    if (clip?.alignPath) loadAlignment(clip).then((a) => !cancelled && setAligned({ name: clip.name, data: a }));
    return () => {
      cancelled = true;
    };
  }, [clip]);

  // The offline analysis of the clip: with the text timing when the clip has an alignment.
  useEffect(() => {
    if (!src) return undefined;
    if (clip?.alignPath && aligned.name !== clip.name) return undefined; // wait for the alignment
    let cancelled = false;
    const events = timelineOn && alignment ? replayEvents(alignment, clip.name, lang) : null;
    analyseUrl(src, { lang, timeline: events })
      .then((a) => {
        if (!cancelled) {
          analysisRef.current = a;
          setAnalysis(a);
          setError('');
        }
      })
      .catch((e) => {
        if (!cancelled) setError(String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [src, clip, lang, alignment, aligned.name, timelineOn]);

  // A hook for browser tests: window.__lipsyncDev.analyse('<clip name>') returns the offline analysis.
  useEffect(() => {
    window.__lipsyncDev = {
      clips: CLIPS.map((c) => c.name),
      // Show the offline analysis at t seconds (null: back to the live audio). The avatar and the
      // live panel then render that frame, so a shot of any moment is exact.
      scrub: (t) => {
        scrubRef.current = t;
        setScrubT(t);
      },
      setTimeline: (on) => setTimelineOn(Boolean(on)),
      choose: (name) => {
        const c = CLIPS.find((x) => x.name === name);
        if (!c) throw new Error(`no clip ${name}`);
        analysisRef.current = null;
        scrubRef.current = null;
        setClip(c);
        setSrc(c.url);
        setStripStart(0);
        setPlaying(false);
        setScrubT(null);
      },
      ready: () => Boolean(analysisRef.current),
      alignment: async (name) => {
        const c = CLIPS.find((x) => x.name === name);
        return c ? loadAlignment(c) : null;
      },
      // The live driver: `timed` is on while the mouth follows the text, `phase` is the sync phase.
      live: () => {
        const d = driverRef.current;
        return d ? { timed: d.engine.timed, phase: sink.phase } : null;
      },
      // What the mouth shows now (the same read the avatar makes), with the audio clock: for
      // recording a live play frame by frame (jitter, closures, lag on the real browser path).
      sample: () => {
        const r = getLipsync();
        const d = driverRef.current;
        return {
          at: audioRef.current ? audioRef.current.currentTime : -1,
          w: r ? Array.from(r.weights, (v) => +v.toFixed(3)) : null,
          level: r ? +r.level.toFixed(3) : 0,
          timed: d ? d.engine.timed : false,
          phase: sink.phase,
          ctxRate: d ? d.context.sampleRate : 0,
          outLatMs: d ? +((d.context.outputLatency || 0) * 1000).toFixed(1) : 0,
          leadMs: d ? d.engine.sampler.leadMs : 0,
          pos: sink.position(performance.now()),
        };
      },
      // Decoded mono samples as base64 float32 (for offline tuning in node: scripts/lipsync-clips.mjs).
      pcm: async (name) => {
        const c = CLIPS.find((x) => x.name === name);
        if (!c) throw new Error(`no clip ${name}`);
        const res = await fetch(c.url);
        const { pcm, sampleRate } = await decodeToMono(await res.arrayBuffer());
        let bin = '';
        const bytes = new Uint8Array(pcm.buffer);
        for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
        return { sampleRate, base64: btoa(bin) };
      },
      analyse: async (name, { timeline = false } = {}) => {
        const c = CLIPS.find((x) => x.name === name);
        if (!c) throw new Error(`no clip ${name}`);
        const al = timeline ? await loadAlignment(c) : null;
        const a = await analyseUrl(c.url, { lang: c.lang ?? 'en', timeline: al ? replayEvents(al, c.name, c.lang) : null });
        return {
          duration: a.duration,
          fps: a.fps,
          runs: dominantRuns(a.frames),
          frames: a.frames.map((f) => ({
            t: +f.t.toFixed(3),
            timed: f.timed ? 1 : 0,
            w: Array.from(f.weights, (v) => +v.toFixed(3)),
            rms: +f.rms.toFixed(4),
            voicing: +f.voicing.toFixed(2),
            f1: Math.round(f.f1),
            f2: Math.round(f.f2),
            f3: Math.round(f.f3),
            centroid: Math.round(f.centroid),
            stress: +f.stress.toFixed(2),
          })),
        };
      },
    };
    return () => {
      delete window.__lipsyncDev;
    };
  }, [sink, getLipsync]);

  const play = async () => {
    const el = audioRef.current;
    if (!el) return;
    await driverRef.current?.resume();
    el.currentTime = 0;
    scrubRef.current = null;
    setScrubT(null);
    // Every play is a new speech. The agent sends the text and `go` as it starts to speak.
    sink.clear();
    const sp = `${clip?.name ?? 'file'}#${++playCount.current}`;
    spRef.current = sp;
    if (timelineOn && alignment) replayTimeline(sink, alignment, sp, performance.now(), lang);
    try {
      await el.play();
    } catch (e) {
      setError(String(e));
    }
  };

  const choose = (c) => {
    setClip(c);
    setSrc(c.url);
    setStripStart(0);
    setPlaying(false);
    setScrubT(null);
  };

  const onFile = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setClip({ name: file.name, url: '', text: '', kind: 'file', lang: 'en' });
    setSrc(URL.createObjectURL(file));
    setStripStart(0);
  };

  const runs = useMemo(() => (analysis ? dominantRuns(analysis.frames) : []), [analysis]);
  const stripFrames = useMemo(() => {
    if (!analysis) return [];
    const out = [];
    for (let k = 0; k < 16; k++) {
      const t = stripStart + k * 0.1;
      const idx = Math.min(analysis.frames.length - 1, Math.round(t * analysis.fps));
      out.push({ t, frame: analysis.frames[idx] });
    }
    return out;
  }, [analysis, stripStart]);

  const dominant = (w) => {
    let b = 0;
    for (let i = 1; i < w.length; i++) if (w[i] > w[b]) b = i;
    return VISEMES[b];
  };

  const btn = (active) =>
    `min-h-11 rounded-xl px-4 text-sm font-semibold ${active ? 'bg-white text-slate-900' : 'bg-slate-700 text-white hover:bg-slate-600'}`;

  return (
    <div className="min-h-screen bg-slate-900 p-4 text-white" data-lipsync-dev="">
      <h1 className="mb-1 text-lg font-bold">Lip-sync lab (dev only)</h1>
      <p className="mb-4 text-xs text-slate-400">
        Audition clips come from frontend/dev-audio/ (gitignored). With Text timing on (the eval lines, which have an
        alignment) the mouth is timed by the text and coloured by the audio, as in a session with LIPSYNC_TIMELINE=1
        (English lines: the lip closures only); with it off, or on a clip with no alignment, it follows what the voice
        sounds like.
      </p>

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <button type="button" className={btn(playing)} data-play="" onClick={play}>
          {playing ? 'Playing' : 'Play'}
        </button>
        <button
          type="button"
          className={btn(false)}
          onClick={() => {
            audioRef.current?.pause();
            stopTimeline(sink, spRef.current, performance.now());
          }}
        >
          Stop
        </button>
        <button
          type="button"
          className={btn(timelineOn)}
          data-toggle-timeline=""
          aria-pressed={timelineOn}
          onClick={() => setTimelineOn((v) => !v)}
        >
          Text timing: {timelineOn ? 'on' : 'off'}
        </button>
        <button type="button" className={btn(showAvatar)} data-toggle-avatar="" onClick={() => setShowAvatar((v) => !v)}>
          {showAvatar ? 'Hide avatar' : 'Show avatar'}
        </button>
        <button type="button" className={btn(reduced)} onClick={() => setReduced((v) => !v)}>
          Reduced motion: {reduced ? 'on' : 'off'}
        </button>
        <label className="text-xs text-slate-300">
          Own file <input type="file" accept="audio/*" onChange={onFile} className="ml-1 text-xs" />
        </label>
      </div>

      <audio
        ref={audioRef}
        src={src}
        controls
        className="mb-4 w-full max-w-xl"
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
      />
      {error ? <p className="mb-2 text-sm text-red-300">{error}</p> : null}

      <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-slate-300">
        <label>
          Eval line{' '}
          <select
            data-eval-select=""
            value={EVAL_CLIPS.some((c) => c.name === clip?.name) ? clip.name : ''}
            onChange={(e) => {
              const c = EVAL_CLIPS.find((x) => x.name === e.target.value);
              if (c) choose(c);
            }}
            className="rounded bg-slate-700 px-2 py-1 text-white"
          >
            <option value="">(pick one)</option>
            {EVAL_CLIPS.map((c) => (
              <option key={c.name} value={c.name}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <span>
          {clip?.alignPath
            ? alignment
              ? 'alignment loaded'
              : 'loading the alignment'
            : 'no alignment for this clip: audio only'}
        </span>
      </div>

      <div className="mb-4 flex flex-wrap gap-1" role="group" aria-label="Clips">
        {MP3_CLIPS.map((c) => (
          <button
            key={c.name}
            type="button"
            data-clip={c.name}
            className={`rounded-lg px-2 py-1 text-xs ${clip?.name === c.name ? 'bg-white text-slate-900' : 'bg-slate-700'}`}
            onClick={() => choose(c)}
          >
            {c.name.replace('abdullah_', 'a_').replace('eleven_', '')}
          </button>
        ))}
        {CLIPS.length === 0 ? <span className="text-xs text-amber-300">No clips in frontend/dev-audio/.</span> : null}
      </div>
      {clip?.text || alignment?.text ? (
        <p className="mb-4 max-w-3xl text-sm" dir="auto" data-clip-text="">
          {clip.text || alignment.text}
        </p>
      ) : null}

      <div className="flex flex-wrap gap-6">
        <div className="min-w-[320px] flex-1">
          <LivePanel getLipsync={getLipsync} reduced={reduced} />
        </div>
        {showAvatar ? (
          <div className="h-[420px] w-[320px] overflow-hidden rounded-xl bg-[#b7d9dc]" data-avatar-box="">
            <Suspense fallback={null}>
              <Avatar
                agentState={playing || scrubT !== null ? 'speaking' : 'listening'}
                getAudioLevel={getLevel}
                getLipsync={getLipsync}
              />
            </Suspense>
          </div>
        ) : null}
      </div>

      <h2 className="mb-1 mt-6 text-sm font-bold">Offline timeline (same pipeline, 60 fps)</h2>
      <Timeline
        analysis={analysis}
        audioRef={audioRef}
        onSeek={(t) => {
          if (audioRef.current) audioRef.current.currentTime = t;
          setStripStart(Math.max(0, Math.min(t, (analysis?.duration ?? 2) - 1.6)));
        }}
      />
      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-slate-300">
        {VISEMES.slice(1).map((v, i) => (
          <span key={v} className="inline-flex items-center gap-1">
            <i className="inline-block h-2 w-2 rounded-sm" style={{ background: COLORS[i + 1] }} />
            {v}
          </span>
        ))}
        <span>grey = loudness, amber = stressed syllable</span>
      </div>

      <h2 className="mb-1 mt-6 text-sm font-bold">Dominant shapes in order</h2>
      <p className="max-w-4xl break-words font-mono text-xs leading-6 text-slate-200" data-runs="">
        {runs.map((r) => `${r.name}${r.frames >= 8 ? '·' : ''}`).join(' ')}
      </p>

      <h2 className="mb-1 mt-6 text-sm font-bold">
        Mouth strip from {stripStart.toFixed(2)} s (every 0.1 s)
      </h2>
      <input
        type="range"
        min={0}
        max={Math.max(0, (analysis?.duration ?? 2) - 1.6)}
        step={0.05}
        value={stripStart}
        onChange={(e) => setStripStart(Number(e.target.value))}
        className="mb-2 w-full max-w-3xl"
        aria-label="Strip start"
      />
      <div className="grid max-w-5xl grid-cols-4 gap-2 sm:grid-cols-8" data-strip="">
        {stripFrames.map(({ t, frame }) => (
          <figure key={t.toFixed(2)} className="m-0 text-center">
            <Mouth weights={frame.weights} size={110} label={`mouth at ${t.toFixed(2)} s`} />
            <figcaption className="text-[10px] text-slate-300">
              {t.toFixed(1)} s · {dominant(frame.weights)}
            </figcaption>
          </figure>
        ))}
      </div>
    </div>
  );
}
