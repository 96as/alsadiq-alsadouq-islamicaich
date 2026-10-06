import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import ForestStage from './ForestStage';
import { TIMES, TIME_LABELS } from './timeOfDay';
import { CLIP, LOOPS, ONE_SHOTS } from '../avatar/avatarConfig';
import NatureDevPanel from './NatureDevPanel';
import useAuditionVoice, { AUDITION_CLIPS, DEFAULT_CLIP } from '../avatar/dev/useAuditionVoice';
import useSignalSimulator from '../avatar/dev/useSignalSimulator'; // 06-avatar-context
import SignalSimulatorPanel from '../avatar/dev/SignalSimulatorPanel'; // 06-avatar-context
import { isLowTier } from '../avatar/hologram/hologramConfig'; // 06-avatar-context

// Fake voice level so the audio-driven jaw can be checked without a live agent.
const previewLevel = () => 0.04 + 0.1 * Math.abs(Math.sin(performance.now() / 110));

const AGENT_STATES = ['initializing', 'listening', 'thinking', 'speaking'];

/**
 * Dev-only page (route /dev/forest, only mounted when import.meta.env.DEV).
 * Shows the forest with the avatar, a time-of-day switcher and a start/stop
 * session button that triggers the camera glide. Also: an agent-state switcher, the avatar's
 * clips (hold a loop, play a one-shot) and a "speak audition clip" button that lip-syncs the
 * avatar to a clip from frontend/dev-audio/ (gitignored). URL options for test runs:
 *   ?t=morning|noon|maghrib|night   start on that time of day
 *   ?phase=talk                     start in the talking shot
 *   ?walk=off|hop                   skip the walk-in, or play the fallback hop and wave
 *   ?panel=0                        hide the control panel (clean screenshots)
 */
export default function ForestPreviewPage() {
  const [params] = useSearchParams();
  const initialTime = TIMES.includes(params.get('t')) ? params.get('t') : null;
  const [time, setTime] = useState(initialTime);
  const [talking, setTalking] = useState(params.get('phase') === 'talk');
  const [speaking, setSpeaking] = useState(false);
  const [agentState, setAgentState] = useState('');
  const [held, setHeld] = useState('');
  const [clipName, setClipName] = useState(DEFAULT_CLIP?.name ?? '');
  const [lastClick, setLastClick] = useState('');
  const walkControl = useRef(null);
  const avatarControl = useRef(null);
  const voice = useAuditionVoice();
  useEffect(() => {
    window.__control = avatarControl; // dev handle, as on the avatar preview page
  }, []);
  const showPanel = params.get('panel') !== '0';
  // 06-avatar-context: the fake agent for the avatar's session signals (?sim=0 hides its buttons).
  const { sim, getContext, lang } = useSignalSimulator({
    initialLang: params.get('lang') === 'ar' ? 'ar' : 'en',
    onInterrupt: () => setAgentState('listening'),
  });
  const showSim = params.get('sim') !== '0' && showPanel;

  const chip = (active) =>
    `min-h-11 rounded-xl px-4 text-sm font-semibold transition-colors ${
      active ? 'bg-white text-slate-900' : 'bg-black/45 text-white hover:bg-black/60'
    }`;

  const hold = useCallback(
    (name) => {
      const next = held === name ? '' : name;
      setHeld(next);
      avatarControl.current?.hold(next);
    },
    [held],
  );

  // The state the avatar shows: a picked state wins, then the audition voice, then the old buttons.
  const derived = !talking ? 'initializing' : speaking || voice.playing ? 'speaking' : 'listening';
  // WP4 (MOTION-BIBLE 6.8): a picked "speaking" plays the Arabic clip; when it ends he listens again
  // instead of flapping to the fake voice.
  const clipSpeaking = agentState === 'speaking' && Boolean(DEFAULT_CLIP);
  const shown = clipSpeaking ? (voice.playing ? 'speaking' : 'listening') : agentState || derived;

  return (
    <div className="fixed inset-0 flex flex-col bg-black">
      {import.meta.env.VITE_SHOWCASE === '1' ? (
        <Link
          to="/"
          className="fixed left-3 top-3 z-50 inline-flex min-h-11 items-center rounded-xl bg-black/45 px-4 text-sm font-semibold text-white hover:bg-black/60"
        >
          Showcase
        </Link>
      ) : null}
      <ForestStage
        phase={talking ? 'talk' : 'wide'}
        timeOfDay={time || undefined}
        avatarSpeaking={shown === 'speaking'}
        agentState={shown}
        getAudioLevel={shown === 'speaking' && !voice.playing ? previewLevel : undefined}
        getLipsync={voice.getLipsync}
        getAvatarContext={getContext} // 06-avatar-context
        lang={lang} // 06-avatar-context
        onClickTarget={setLastClick}
        walkControlRef={walkControl}
        avatarControlRef={avatarControl}
      >
        {showSim ? <SignalSimulatorPanel sim={sim} lang={lang} tier={isLowTier() ? 'low' : 'high'} /> : null}
        {showPanel ? <NatureDevPanel /> : null}
        {showPanel ? (
          <div className="mt-auto flex flex-col gap-2 p-3 pb-5">
            {lastClick ? <p className="rounded-lg bg-black/50 px-3 py-1 text-xs text-white">Clicked: {lastClick}</p> : null}
            <div className="flex flex-wrap gap-2" role="group" aria-label="Time of day">
              <button type="button" className={chip(time === null)} onClick={() => setTime(null)}>
                Device clock
              </button>
              {TIMES.map((t) => (
                <button key={t} type="button" data-time-button={t} className={chip(time === t)} onClick={() => setTime(t)}>
                  {TIME_LABELS[t]}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap gap-2" role="group" aria-label="Agent state">
              <button type="button" className={chip(agentState === '')} onClick={() => setAgentState('')}>
                State: auto
              </button>
              {AGENT_STATES.map((s) => (
                <button
                  key={s}
                  type="button"
                  data-agent-state={s}
                  className={chip(agentState === s)}
                  onClick={() => {
                    setAgentState(s);
                    // WP4: "speaking" plays the default Arabic clip with real lip sync; any other state stops it.
                    if (s === 'speaking' && DEFAULT_CLIP) voice.speak(DEFAULT_CLIP);
                    else if (voice.playing) voice.stop();
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap gap-2" role="group" aria-label="Avatar clips">
              {LOOPS.map((name) => (
                <button key={name} type="button" data-hold={name} className={chip(held === name)} onClick={() => hold(name)}>
                  hold {name}
                </button>
              ))}
              {[...ONE_SHOTS, CLIP.blink].map((name) => (
                <button key={name} type="button" data-play={name} className={chip(false)} onClick={() => avatarControl.current?.play(name)}>
                  play {name}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="button" data-session-button="" className={chip(talking)} onClick={() => setTalking((v) => !v)}>
                {talking ? 'Stop session' : 'Start session'}
              </button>
              <button
                type="button"
                data-replay-walk=""
                className={chip(false)}
                onClick={() => {
                  setTalking(false);
                  walkControl.current?.replay();
                }}
              >
                Replay walk
              </button>
              <button
                type="button"
                data-speak-default=""
                className={chip(speaking || Boolean(voice.playing))}
                onClick={() => {
                  // WP4: Speak plays the default Arabic clip with real lip sync (the fake voice only without dev-audio).
                  if (voice.playing) voice.stop();
                  else if (DEFAULT_CLIP && !speaking) voice.speak(DEFAULT_CLIP);
                  else setSpeaking((v) => !v);
                }}
              >
                {speaking || voice.playing ? 'Stop speaking' : 'Speak'}
              </button>
              {import.meta.env.VITE_SHOWCASE === '1' && AUDITION_CLIPS.length === 0 ? null : (
              <>
              <select
                data-audition-select=""
                value={clipName}
                onChange={(e) => setClipName(e.target.value)}
                className="min-h-11 max-w-[14rem] rounded-xl bg-black/45 px-2 text-sm text-white"
              >
                {AUDITION_CLIPS.map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.name}
                  </option>
                ))}
              </select>
              <button
                type="button"
                data-speak=""
                className={chip(Boolean(voice.playing))}
                onClick={() => (voice.playing ? voice.stop() : voice.speak(AUDITION_CLIPS.find((c) => c.name === clipName)))}
              >
                {voice.playing ? 'Stop audition' : 'Speak audition clip'}
              </button>
              </>
              )}
            </div>
          </div>
        ) : null}
      </ForestStage>
    </div>
  );
}
