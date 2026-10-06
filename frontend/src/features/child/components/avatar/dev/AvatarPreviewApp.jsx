// Dev only: the page behind frontend/avatar-component-preview.html. Mounts the real Avatar and adds a
// state switcher, a clip list (loops to hold, one-shots to play) and a "speak audition clip" button.
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Avatar from '../Avatar.jsx';
import { CLIP, LOOPS, ONE_SHOTS } from '../avatarConfig.js';
import { WALK, createWalk, replayWalk } from '../walkIn.js';
import { BASE_URL, SHOWCASE } from '../../../../../utils/assetUrl.js';
import useAuditionVoice, { AUDITION_CLIPS, DEFAULT_CLIP } from './useAuditionVoice.js';
import useSignalSimulator from './useSignalSimulator.js'; // 06-avatar-context
import SignalSimulatorPanel from './SignalSimulatorPanel.jsx'; // 06-avatar-context
import { isLowTier } from '../hologram/hologramConfig.js'; // 06-avatar-context
// look-dev: ?framing=meadow stands him on the painted meadow exactly like VoiceMode does (the real MeadowImage).
import MeadowImage from '../../MeadowImage.jsx';

const STATES = ['idle', 'listening', 'thinking', 'speaking'];
const params = new URLSearchParams(window.location.search);
const FRAMING = params.get('framing') === 'meadow' ? 'meadow' : undefined; // look-dev
const HIDE_BARS = params.get('bars') === '0'; // look-dev: clean frames for the shots
if (FRAMING) import('../../../../../index.css'); // look-dev: MeadowImage is styled with Tailwind classes

// A fake voice: syllable-rate bursts with pauses, shaped like the RMS of real speech.
const syntheticLevel = () => {
  const t = performance.now() / 1000;
  const syllable = Math.max(0, Math.sin(t * 9.5)) ** 1.5;
  const phrase = Math.sin(t * 1.1) > -0.35 ? 1 : 0.05;
  const wobble = 0.65 + 0.35 * Math.sin(t * 3.7 + 1);
  return 0.13 * syllable * phrase * wobble;
};

// 06-avatar-context: the three rows stack in one fixed column, so a row that wraps on a narrow screen pushes
// the next one down instead of sitting on top of it.
const stack = { position: 'fixed', top: 10, left: 10, right: 10, zIndex: 5, display: 'flex', flexDirection: 'column', gap: 6, pointerEvents: 'none' };
const bar = () => ({
  display: 'flex',
  flexWrap: 'wrap',
  gap: 6,
  alignItems: 'center',
  pointerEvents: 'auto',
});
const btn = (on) => ({
  padding: '6px 10px',
  border: '1px solid #5b6b8c',
  borderRadius: 6,
  cursor: 'pointer',
  font: '13px system-ui, sans-serif',
  background: on ? '#2a3a5c' : '#fff',
  color: on ? '#fff' : '#111',
});

export default function AvatarPreviewApp() {
  const [state, setState] = useState(params.get('state') || 'idle');
  const [legacy, setLegacy] = useState(params.get('speaking') === '1');
  const [held, setHeld] = useState('');
  const [info, setInfo] = useState('');
  const [clipName, setClipName] = useState(
    AUDITION_CLIPS.find((c) => c.name === params.get('clip'))?.name ?? DEFAULT_CLIP?.name ?? '',
  );
  const control = useRef(null);
  // ?timeline=0 plays the clips with the mouth following the audio alone (the old behaviour).
  const voice = useAuditionVoice({ timeline: params.get('timeline') !== '0' });

  const walkParam = params.get('walk');
  const walk = useMemo(() => {
    if (!walkParam) return null;
    const w = createWalk(walkParam === 'hop' ? 'hop' : 'walk');
    w.armed = true;
    if (walkParam === 'treadmill') {
      w.distance = 1e6;
      w.distanceLocked = true;
    }
    return w;
  }, [walkParam]);

  // WP4: "speaking" plays the default Arabic clip with real lip sync when dev-audio has clips.
  // ?level=synthetic (or none) keeps the old fake voice.
  const levelMode = params.get('level') || (DEFAULT_CLIP ? 'clip' : 'synthetic');
  const clipMode = levelMode === 'clip' && Boolean(DEFAULT_CLIP);
  const getAudioLevel = levelMode === 'none' || clipMode ? undefined : syntheticLevel;
  const speakRef = useRef(voice.speak);
  const stopRef = useRef(voice.stop);
  useEffect(() => {
    speakRef.current = voice.speak;
    stopRef.current = voice.stop;
  }, [voice.speak, voice.stop]);

  useEffect(() => {
    window.__setState = (next) => {
      setState(next);
      setLegacy(false);
      if (next === 'speaking' && clipMode) speakRef.current(DEFAULT_CLIP);
      else if (clipMode) stopRef.current();
    };
    window.__control = control;
    window.__voice = voice;
    if (walk) {
      window.__walk = walk;
      window.__WALK = WALK;
      window.__replayWalk = () => replayWalk(walk);
    }
    window.__mouthMetrics = {
      start: async () => (await control.current.metrics()).start(),
      stop: async () => (await control.current.metrics()).stop(),
    };
  }, [walk, voice, clipMode]);

  useEffect(() => {
    const id = window.setInterval(() => {
      const c = control.current;
      setInfo(c?.info ? JSON.stringify({ mode: c.mode, ...c.info, jaw: +c.info.jaw.toFixed(2) }) : (c?.mode ?? ''));
    }, 250);
    return () => window.clearInterval(id);
  }, []);

  const hold = useCallback(
    (name) => {
      const next = held === name ? '' : name;
      setHeld(next);
      control.current?.hold(next);
    },
    [held],
  );

  // 06-avatar-context: the fake agent (al.* signals, transcript, events) and the hologram tier switch.
  const { sim, getContext, lang } = useSignalSimulator({
    initialLang: params.get('lang') === 'ar' ? 'ar' : 'en',
    onInterrupt: () => window.__setState?.('listening'),
  });
  const [tierPick, setTierPick] = useState(() => {
    const q = params.get('holotier');
    return q === 'low' || q === 'high' ? q : null;
  });
  const tier = tierPick ?? (isLowTier() ? 'low' : 'high');
  const showSim = params.get('sim') !== '0';

  const speakState = voice.playing ? 'speaking' : clipMode && state === 'speaking' ? 'listening' : state; // WP4: the clip ended
  const modelUrl = params.get('model') || undefined;
  const ctxProps = { getAvatarContext: getContext, lang, lowTier: tier === 'low' }; // 06-avatar-context
  const props = legacy
    ? { isSpeaking: true, walk, controlRef: control, modelUrl, framing: FRAMING, ...ctxProps }
    : {
        modelUrl,
        isSpeaking: speakState === 'speaking',
        agentState: speakState,
        getAudioLevel: voice.playing ? undefined : getAudioLevel,
        getLipsync: voice.getLipsync,
        walk,
        controlRef: control,
        ...ctxProps,
        framing: FRAMING,
      };

  return (
    <>
      {FRAMING === 'meadow' && (
        <div style={{ position: 'fixed', inset: 0 }}>
          <MeadowImage anchored />
        </div>
      )}
      <div style={{ display: HIDE_BARS ? 'none' : 'contents' }}>
      <div style={stack}>
      <div style={bar()} role="group" aria-label="Agent state">
        {STATES.map((name) => (
          <button key={name} data-state={name} style={btn(!legacy && state === name)} onClick={() => window.__setState(name)}>
            {name}
          </button>
        ))}
        {walk ? (
          <button data-replay-walk="" style={btn(false)} onClick={() => window.__replayWalk()}>
            replay walk
          </button>
        ) : null}
        {SHOWCASE ? (
          <a href={BASE_URL} style={{ ...btn(false), textDecoration: 'none' }}>
            Showcase
          </a>
        ) : null}
      </div>
      <div style={bar()} role="group" aria-label="Clips">
        {LOOPS.map((name) => (
          <button key={name} data-hold={name} style={btn(held === name)} onClick={() => hold(name)}>
            hold {name}
          </button>
        ))}
        {[...ONE_SHOTS, CLIP.blink].map((name) => (
          <button key={name} data-play={name} style={btn(false)} onClick={() => control.current?.play(name)}>
            play {name}
          </button>
        ))}
        <button data-nod="" style={btn(false)} onClick={() => control.current?.nod?.()}>
          nod
        </button>
      </div>
      {SHOWCASE && AUDITION_CLIPS.length === 0 ? null : (
      <div style={bar()} role="group" aria-label="Voice">
        <select
          data-audition-select=""
          value={clipName}
          onChange={(e) => setClipName(e.target.value)}
          style={{ font: '13px system-ui', maxWidth: 260, padding: 5 }}
        >
          {AUDITION_CLIPS.map((c) => (
            <option key={c.name} value={c.name}>
              {c.name}
            </option>
          ))}
        </select>
        <button
          data-speak=""
          style={btn(Boolean(voice.playing))}
          onClick={() => (voice.playing ? voice.stop() : voice.speak(AUDITION_CLIPS.find((c) => c.name === clipName)))}
        >
          {voice.playing ? 'stop audition' : 'speak audition clip'}
        </button>
        <label style={{ font: '13px system-ui', display: 'inline-flex', gap: 4, alignItems: 'center' }}>
          <input
            type="checkbox"
            data-timeline-toggle=""
            checked={voice.timelineOn}
            onChange={(e) => voice.setTimelineOn(e.target.checked)}
          />
          text timing
        </label>
        {AUDITION_CLIPS.length === 0 ? (
          <span style={{ font: '12px system-ui', color: '#7a2a2a' }}>no clips in frontend/dev-audio/ (Arabic ones in dev-audio/eval-ar/)</span>
        ) : null}
      </div>
      )}
      </div>
      </div>
      <div data-readout="" style={{ display: HIDE_BARS ? 'none' : 'block', position: 'fixed', bottom: 8, left: 10, zIndex: 5, font: '12px system-ui, sans-serif', color: '#2a3a5c' }}>
        {info}
      </div>
      {showSim && !HIDE_BARS ? <SignalSimulatorPanel sim={sim} lang={lang} tier={tier} onTier={setTierPick} /> : null}
      <div style={{ position: 'fixed', inset: 0 }}>
        <Avatar key={tier} {...props} />
      </div>
    </>
  );
}
