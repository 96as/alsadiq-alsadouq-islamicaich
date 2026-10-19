import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ArrowLeft, ChevronDown, Mic, Volume2, VolumeX } from 'lucide-react';
import AuroraBackground from '../components/AuroraBackground';
import VoiceMode from '../features/child/components/VoiceMode';
import LevelCard from '../features/child/components/LevelCard';
import GlassIconButton from '../features/child/components/GlassIconButton';
import { CLIP, DIRECTOR } from '../features/child/components/avatar/avatarConfig';
import { createFakeSpeech } from '../features/child/components/avatar/dev/fakeSpeech';
import useSignalSimulator from '../features/child/components/avatar/dev/useSignalSimulator';
import useShowcaseVoice from './useShowcaseVoice';

/**
 * Showcase page: the animated Al-Sadiq on the lead's meadow background, framed like the real
 * child voice screen (same shell, header, VoiceMode, avatar canvas and controls). Nothing talks to
 * a server.
 *
 * integrate-1: "Speak" plays a real Arabic (or English) clip with text-timed lip sync and sound
 * (useShowcaseVoice; the clips are added by the showcase build, see scripts/showcase-audio.mjs).
 * The context chips (listening style, talking style, search, greet, goodbye, celebrate, happy) go
 * through the signal simulator into the real avatar context store and director, so the avatar
 * does exactly what it would for an agent's session signals.
 *
 * hotfix-2: Speak (Arabic) is the primary control and plays a real clip from inside the tap (Safari
 * safe, see useShowcaseVoice); the silent made-up voice is the secondary "Mouth test (no sound)"
 * chip; the speaker button mutes the real clip while the lips keep moving; if the browser refuses
 * the sound the page says so and offers a "Tap to turn on sound" button.
 */
const STATES = [
  { id: 'idle', en: 'Idle', ar: 'هادئ' },
  { id: 'listening', en: 'Listening', ar: 'يصغي' },
  { id: 'thinking', en: 'Thinking', ar: 'يفكّر' },
  { id: 'speaking', en: 'Mouth test (no sound)', ar: 'تجربة الفم بلا صوت' }, // hotfix-2: silent made-up voice, never "Speak"
];
const MAIN_STATES = STATES.filter((s) => s.id !== 'speaking'); // hotfix-2
const ACTIONS = [
  { id: 'wave', clip: CLIP.wave, en: 'Wave', ar: 'تلويح' },
  { id: 'look', clip: CLIP.lookAround, en: 'Look around', ar: 'ينظر حوله' },
  { id: 'blink', clip: CLIP.blink, en: 'Blink', ar: 'رمشة' },
];
// The chips use the child-facing names; `sim` is the value of the al.* signal behind each one.
const LISTEN = [
  { id: 'attentive', sim: 'neutral', en: 'Attentive', ar: 'منتبه' },
  { id: 'curious', sim: 'curious', en: 'Curious', ar: 'فضولي' },
  { id: 'empathetic', sim: 'sad', en: 'Empathetic', ar: 'متعاطف' },
  { id: 'excited', sim: 'excited', en: 'Excited', ar: 'متحمس' },
];
const TALK = [
  { id: 'explain', sim: 'explain', en: 'Explain', ar: 'يشرح' },
  { id: 'story', sim: 'story', en: 'Story', ar: 'قصة' },
  { id: 'praise', sim: 'praise', en: 'Praise', ar: 'مدح' },
  { id: 'ask', sim: 'question', en: 'Ask', ar: 'يسأل' },
  { id: 'gentle', sim: 'gentle', en: 'Gentle', ar: 'بلطف' },
];
const KINDS = [
  { id: 'library', en: 'Library', ar: 'المكتبة' },
  { id: 'folders', en: 'Folders', ar: 'المجلدات' },
  { id: 'web', en: 'Web', ar: 'الويب' },
];
const OUTCOMES = [
  { id: 'found', en: 'Found', ar: 'وجد' },
  { id: 'none', en: 'None', ar: 'لا شيء' },
];
const MOMENTS = [
  { id: 'greet', en: 'Greet', ar: 'سلام' },
  { id: 'goodbye', en: 'Goodbye', ar: 'وداعًا' },
  { id: 'celebrate', en: 'Celebrate', ar: 'احتفال' },
  { id: 'happy', en: 'Happy', ar: 'سعيد' },
];
const TABS = [
  { id: 'speak', en: 'Speak', ar: 'تكلم' },
  { id: 'style', en: 'Style', ar: 'أسلوب' },
  { id: 'search', en: 'Search', ar: 'بحث' },
  { id: 'moments', en: 'Moments', ar: 'لحظات' },
  { id: 'basics', en: 'Basics', ar: 'أساسي' },
];
const SEARCH_MS = 3500;
const WEB_MS = 9000; // w3: how long the held web page reads before it finds the card
// w3: "Search the web" chips. The query is a kid-safe sample, the results are invented fixtures (fixtures.js).
// w3 review: a found chip shows the query alone; "Search the web: ..." overflowed its pill (nowrap) at 390 px.
const WEB_SAMPLES = [
  { id: 'sky-found', name: 'sky', outcome: 'found', en: 'Search the web', ar: 'ابحث في الويب', sub: { en: 'Why is the sky blue?', ar: 'لماذا السماء زرقاء' } },
  { id: 'bees-found', name: 'bees', outcome: 'found', en: 'Search the web', ar: 'ابحث في الويب', sub: { en: 'How bees make honey', ar: 'كيف يصنع النحل العسل' } },
  { id: 'sky-none', name: 'sky', outcome: 'none', en: 'Web, no results', ar: 'الويب، بلا نتائج' },
  { id: 'sky-grownup', name: 'sky', outcome: 'grownup', en: 'Web, ask a grown-up', ar: 'الويب، اسأل كبيرًا' },
];
const GREET_TEXT = { ar: 'السلام عليكم يا صديقي!', en: 'As-salamu alaykum, my friend!' };
const BYE_TEXT = { ar: 'مع السلامة يا صديقي، نشوفك بكرة!', en: 'Goodbye, see you tomorrow!' };

// Chips sit in fixed grids so the panel keeps the same shape on every tab and the stage above it
// keeps most of the screen, framed like the real child screen.
const chipClass = (active) =>
  `inline-flex min-h-11 min-w-0 flex-col items-center justify-center rounded-full px-1 py-1 text-[13px] font-semibold leading-tight whitespace-nowrap transition-all active:scale-[0.97] ${
    active ? 'bg-white text-slate-900 shadow-lg' : 'glass-button text-white/92 hover:bg-white/15'
  }`;

function Chip({ en, ar, active, busy, onClick, className = '', ...rest }) {
  return (
    <button
      type="button"
      aria-pressed={!!active}
      aria-busy={busy}
      className={`${chipClass(active || busy)} ${className}`}
      onClick={onClick}
      {...rest}
    >
      <span>{en}</span>
      <span lang="ar" dir="rtl" className="text-xs opacity-80">{ar}</span>
    </button>
  );
}

const Label = ({ en, ar }) => (
  <p className="mb-1 mt-0.5 flex items-baseline justify-between px-1 text-[11px] font-bold uppercase tracking-wide text-white/70">
    <span>{en}</span>
    <span lang="ar" dir="rtl" className="text-xs normal-case tracking-normal">{ar}</span>
  </p>
);

export default function MeadowShowcase() {
  const [params] = useSearchParams();
  const initial = STATES.some((s) => s.id === params.get('state')) ? params.get('state') : 'idle';
  const [state, setState] = useState(initial);
  const [micMuted, setMicMuted] = useState(false);
  const [speakerMuted, setSpeakerMuted] = useState(false);
  const [tab, setTab] = useState('speak');
  const [open, setOpen] = useState(() => {
    try {
      return window.matchMedia('(min-width: 1024px)').matches;
    } catch {
      return true;
    }
  });
  const [picked, setPicked] = useState({}); // the chip each group last pressed, while it is "live"
  const control = useRef(null);
  const meter = useRef(null);
  const speech = useMemo(() => createFakeSpeech(), []);

  // The real voice and the context simulator. The simulator is the dev fake agent: it feeds the same
  // store functions a live session feeds, and the avatar's context director reads that store.
  const { sim, getContext, lang } = useSignalSimulator({ initialLang: 'ar' });
  const voice = useShowcaseVoice({
    onStart: (clip) => {
      sim.lang(clip.lang);
      sim.talk(clip.talk);
      setPicked((p) => ({ ...p, talk: '' }));
      setState('speaking');
    },
    onEnd: () => setState((s) => (s === 'speaking' ? 'idle' : s)),
  });
  // hotfix-2: the speaker button silences what is heard; the lips keep moving (a gain after the analyser).
  const { setMuted: setVoiceMuted } = voice;
  useEffect(() => {
    setVoiceMuted(speakerMuted);
  }, [speakerMuted, setVoiceMuted]);
  // The real voice while a clip plays, the made-up one otherwise (the Mouth test chip, the moments).
  const voiceRef = useRef(voice);
  useEffect(() => {
    voiceRef.current = voice;
  });
  const getLipsync = useCallback(() => (voiceRef.current.isLive() ? voiceRef.current.getLipsync() : speech.getLipsync()), [speech]);
  const getLevel = useCallback(() => (voiceRef.current.isLive() ? voiceRef.current.getLevel() : speech.getLevel()), [speech]);

  // One timer for "go back to idle in a moment" so a new press replaces the old one.
  const auto = useRef(0);
  const flashes = useRef(new Map());
  const later = (fn, ms) => {
    window.clearTimeout(auto.current);
    auto.current = window.setTimeout(fn, ms);
  };
  const flash = (group, id, ms) => {
    window.clearTimeout(flashes.current.get(group));
    setPicked((p) => ({ ...p, [group]: id }));
    flashes.current.set(
      group,
      window.setTimeout(() => setPicked((p) => ({ ...p, [group]: '' })), ms),
    );
  };
  useEffect(
    () => () => {
      window.clearTimeout(auto.current);
      for (const t of flashes.current.values()) window.clearTimeout(t);
    },
    [],
  );

  // A state press (or any context press) takes over from a clip that is playing.
  const choose = (next) => {
    if (voice.isLive()) voice.stop();
    window.clearTimeout(auto.current);
    setState(next);
  };

  // The avatar plays one gesture at a time, so a press during another gesture (an idle glance, a
  // wave) waits for its turn instead of being dropped.
  const pending = useRef(0);
  const [queued, setQueued] = useState('');
  const play = (action) => {
    window.clearInterval(pending.current);
    let tries = 0;
    const attempt = () => {
      const ok = control.current?.play(action.clip);
      if (ok || ++tries > 80) {
        window.clearInterval(pending.current);
        setQueued('');
      }
    };
    pending.current = window.setInterval(attempt, 100);
    setQueued(action.id); // shows as pressed until it gets its turn
    attempt();
  };
  useEffect(() => () => window.clearInterval(pending.current), []);

  const listen = (c) => {
    choose('listening');
    sim.listen(c.sim);
    setPicked((p) => ({ ...p, listen: c.id }));
  };
  const talk = (c, e) => {
    // hotfix-2: a talking style plays a REAL clip in that style (sound, text-timed lips); only a build
    // without clips falls back to the made-up voice.
    const clip = voice.clips.find((k) => k.talk === c.sim) ?? voice.clips.find((k) => k.lang === 'ar');
    if (clip) {
      voice.speak({ ...clip, talk: c.sim }, { at: e?.timeStamp });
      window.clearTimeout(auto.current);
      setPicked((p) => ({ ...p, talk: c.id }));
      return;
    }
    choose('speaking');
    sim.talk(c.sim);
    setPicked((p) => ({ ...p, talk: c.id }));
    later(() => setState((s) => (s === 'speaking' ? 'idle' : s)), 6500);
  };
  const search = (kind, outcome) => {
    choose('thinking');
    sim.search(kind, outcome, SEARCH_MS);
    flash('search', `${kind}-${outcome}`, SEARCH_MS + 2500);
    later(() => setState((s) => (s === 'thinking' ? 'idle' : s)), SEARCH_MS + 600);
  };
  // w3: the held web page: a kid-safe sample query, fixture results (invented text), in the page's language
  const searchWeb = (name, outcome) => {
    choose('thinking');
    sim.searchWeb(name, { outcome, lang: lang === 'en' ? 'en' : 'ar', foundMs: WEB_MS });
    flash('search', `webpage-${name}-${outcome}`, WEB_MS + 6500);
    later(() => setState((s) => (s === 'thinking' ? 'idle' : s)), WEB_MS + 600);
  };
  const moment = (id) => {
    const l = lang === 'en' ? 'en' : 'ar';
    if (id === 'greet' || id === 'goodbye') {
      // Greet and goodbye are once-per-session cues of the transcript: start a fresh session, then
      // let the agent "say" the line, with the made-up voice moving the mouth.
      sim.newSession();
      sim.say(id === 'greet' ? GREET_TEXT[l] : BYE_TEXT[l]);
      choose('speaking');
      later(() => setState((s) => (s === 'speaking' ? 'idle' : s)), 3200);
    } else {
      sim.gam(id);
    }
    flash('moment', id, 2600);
  };

  // hotfix-2: voice.speak() is the first thing the tap does (it calls el.play() before any await).
  const speak = (clip, e) => {
    if (voice.playing === clip.id) voice.stop();
    else voice.speak(clip, { at: e?.timeStamp });
    window.clearTimeout(auto.current);
  };

  // integrate-1: in a session the hologram waits 8 s after one closes before a new tool call opens
  // another (DIRECTOR.holo.toolGap), so a quick second Search press here showed nothing. Each press
  // on this panel is a request to see it, so the page shortens the gaps while it is open.
  useEffect(() => {
    const h = DIRECTOR.holo;
    const prev = { toolGap: h.toolGap, quickGap: h.quickGap };
    h.toolGap = 0.3;
    h.quickGap = 0.3;
    return () => {
      h.toolGap = prev.toolGap;
      h.quickGap = prev.quickGap;
    };
  }, []);

  useEffect(() => {
    const prev = document.title;
    document.title = 'Al-Sadiq on the meadow';
    return () => {
      document.title = prev;
    };
  }, []);

  // Test and debug hooks, like the other preview pages.
  useEffect(() => {
    window.__setState = setState;
    window.__control = control;
  }, []);

  // The level meter shows the speaking level (the real clip, or the made-up voice) while speaking.
  useEffect(() => {
    let raf = 0;
    const tick = () => {
      if (meter.current) {
        const v = state === 'speaking' ? Math.min(1, getLevel() / 0.13) : 0;
        meter.current.style.transform = `scaleX(${v.toFixed(3)})`;
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [state, getLevel]);

  const arClips = voice.clips.filter((c) => c.lang === 'ar');
  const enClips = voice.clips.filter((c) => c.lang !== 'ar');
  const nowClip = voice.clips.find((c) => c.id === voice.playing);
  const firstAr = arClips[0];

  const speakButton = (c, extra = '') => (
    <button
      key={c.id}
      type="button"
      data-speak={c.id}
      aria-pressed={voice.playing === c.id}
      title={c.text}
      className={`${chipClass(voice.playing === c.id)} ${extra}`}
      onClick={(e) => speak(c, e)}
    >
      <span>{c.lang === 'ar' ? 'Speak (Arabic)' : 'Speak (English)'}</span>
      <span className="text-xs opacity-80">
        {c.en} · <span lang="ar" dir="rtl">{c.ar}</span>
      </span>
    </button>
  );

  return (
    <div
      className="app-theme-shell relative flex h-dvh max-h-dvh min-h-0 flex-col overflow-hidden text-white antialiased"
      data-theme="child"
      data-view="immersive"
      data-state={state}
      style={{ fontFamily: 'Manrope, ui-sans-serif, system-ui, -apple-system, sans-serif' }}
    >
      <AuroraBackground />

      <div className="relative z-10 flex min-h-0 flex-1 flex-col">
        <div className="relative flex min-h-0 flex-1 flex-col">
          <header className="absolute inset-x-0 top-0 z-30 shrink-0 px-4 pb-2 pt-8">
            <div className="flex items-center justify-between gap-3">
              <Link
                to="/"
                aria-label="Back to the showcase"
                className="glass-button relative grid h-11 w-11 shrink-0 place-items-center rounded-full"
              >
                <ArrowLeft className="h-5 w-5 text-white/90" strokeWidth={1.5} />
              </Link>
              <LevelCard title="Level 3 Explorer" progress={45} />
              <div className="h-11 w-11 shrink-0" aria-hidden="true" />
            </div>
          </header>

          {/* The same section the child voice screen uses: meadow image, avatar canvas, controls. */}
          <VoiceMode
            agentSpeaking={state === 'speaking'}
            agentState={state}
            getAudioLevel={getLevel}
            getLipsync={getLipsync}
            controlRef={control}
            getAvatarContext={getContext}
            lang={lang}
          >
            <GlassIconButton
              icon={speakerMuted ? VolumeX : Volume2} // hotfix-2: the icon, the label and aria-pressed show the state
              onClick={() => setSpeakerMuted((v) => !v)}
              ariaLabel={speakerMuted ? 'Unmute speaker' : 'Mute speaker'}
              pressed={speakerMuted}
              title={speakerMuted ? 'Sound off (the lips still move). Tap for sound.' : 'Sound on. Tap to mute.'}
              dataToggle="speaker"
              className={speakerMuted ? 'bg-white/25 ring-2 ring-white/70' : ''}
            />
            <button
              type="button"
              onClick={() => setMicMuted((v) => !v)}
              className={`glass-button grid h-16 w-16 min-h-14 min-w-14 place-items-center rounded-full transition-all duration-150 ${micMuted ? 'opacity-70' : ''}`}
              aria-label={micMuted ? 'Unmute microphone' : 'Mute microphone'}
            >
              <Mic className="h-7 w-7 text-white/90" strokeWidth={1.5} />
            </button>
            <div className="h-11 w-11" aria-hidden="true" />
          </VoiceMode>

          {/* hotfix-2: the browser refused the sound (Safari, iOS). Say so, and let the next tap retry. */}
          {voice.blocked && (
            <div
              role="alert"
              data-sound-blocked={voice.blocked.reason}
              className="pointer-events-none absolute inset-x-0 bottom-24 z-40 flex justify-center px-4"
            >
              <button
                type="button"
                data-sound-retry=""
                className="pointer-events-auto flex min-h-14 items-center gap-3 rounded-full bg-white px-5 py-2 text-slate-900 shadow-2xl ring-2 ring-white/60"
                onClick={(e) => voice.retry({ at: e.timeStamp })}
              >
                <Volume2 className="h-6 w-6 shrink-0" strokeWidth={1.75} />
                <span className="flex flex-col items-start text-left leading-tight">
                  <span className="text-sm font-bold">Tap to turn on sound</span>
                  <span lang="ar" dir="rtl" className="text-sm font-semibold">اضغط لتشغيل الصوت</span>
                </span>
              </button>
            </div>
          )}
        </div>

        {/* The showcase controls. Below the stage on phones (a sheet that folds down to one row, in
            the page flow so it never covers Sadiq), over the right edge on wide screens. */}
        <section
          aria-label="Showcase controls"
          data-panel={open ? 'open' : 'closed'}
          className="glass-strong relative z-30 mx-3 mb-3 shrink-0 rounded-3xl px-3 py-2 lg:absolute lg:bottom-6 lg:right-6 lg:m-0 lg:w-[24rem] lg:px-4 lg:py-3"
        >
          <div className="flex items-center gap-2">
            <p className="min-w-0 flex-1 text-sm font-bold leading-tight text-white">
              <span className="block truncate">Meadow · <span lang="ar" dir="rtl" className="text-xs font-semibold text-white/80">المرج</span></span>
            </p>
            {!open && firstAr && (
              <button
                type="button"
                data-speak-quick=""
                className={`${chipClass(voice.playing === firstAr.id)} shrink-0 px-4`}
                onClick={(e) => speak(firstAr, e)}
              >
                <span>Speak (Arabic)</span>
                <span lang="ar" dir="rtl" className="text-xs opacity-80">تكلم بالعربية</span>
              </button>
            )}
            <button
              type="button"
              data-panel-toggle=""
              aria-expanded={open}
              aria-label={open ? 'Fold the controls' : 'Open the controls'}
              className="glass-button grid h-11 w-11 shrink-0 place-items-center rounded-full"
              onClick={() => setOpen((v) => !v)}
            >
              <ChevronDown className={`h-5 w-5 text-white/90 transition-transform ${open ? '' : 'rotate-180'}`} strokeWidth={1.75} />
            </button>
          </div>

          {open && (
            <>
              {/* hotfix-2: the primary control on the wide layout, whatever tab is open: real voice, real sound. */}
              {firstAr && (
                <button
                  type="button"
                  data-speak-primary=""
                  aria-pressed={voice.playing === firstAr.id}
                  className="mt-2 hidden min-h-14 w-full items-center justify-center gap-3 rounded-full bg-white px-5 text-slate-900 shadow-xl ring-2 ring-white/50 transition-all hover:scale-[1.01] active:scale-[0.98] lg:flex"
                  onClick={(e) => speak(firstAr, e)}
                >
                  <Volume2 className="h-6 w-6 shrink-0" strokeWidth={1.75} />
                  <span className="flex flex-col items-start leading-tight">
                    <span className="text-base font-extrabold">{voice.playing === firstAr.id ? 'Speaking… tap to stop' : 'Speak (Arabic)'}</span>
                    <span lang="ar" dir="rtl" className="text-sm font-semibold">{voice.playing === firstAr.id ? 'يتكلم… اضغط للإيقاف' : 'تكلم بالعربية'}</span>
                  </span>
                </button>
              )}
              <div className="mt-1.5 grid grid-cols-5 gap-1" role="tablist" aria-label="Controls">
                {TABS.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    role="tab"
                    data-tab={t.id}
                    aria-selected={tab === t.id}
                    className={`flex min-h-11 min-w-0 flex-col items-center justify-center rounded-xl px-0.5 text-[12px] font-bold leading-tight transition-colors ${
                      tab === t.id ? 'bg-white/90 text-slate-900' : 'text-white/85 hover:bg-white/10'
                    }`}
                    onClick={() => setTab(t.id)}
                  >
                    <span>{t.en}</span>
                    <span lang="ar" dir="rtl" className="text-[11px] font-semibold opacity-80">{t.ar}</span>
                  </button>
                ))}
              </div>

              <div role="tabpanel" className="mt-2 min-h-[10.75rem] max-w-md">
                {tab === 'speak' && (
                  <div data-tabpanel="speak">
                    {arClips.length + enClips.length > 0 ? (
                      <div className="grid grid-cols-2 gap-1.5">
                        {arClips.map((c) => speakButton(c))}
                        {enClips.map((c) => speakButton(c, 'col-span-2'))}
                      </div>
                    ) : (
                      <p className="rounded-2xl bg-white/10 px-3 py-2 text-xs leading-snug text-white/80">
                        {voice.loaded ? 'No audio clips in this build. ' : 'Loading the clips. '}
                        Use the Mouth test on Basics: a made-up voice moves the mouth, with no sound.
                      </p>
                    )}
                    <p className="mt-1.5 min-h-8 px-1 text-xs leading-snug text-white/75" aria-live="polite">
                      {nowClip ? (
                        <span lang={nowClip.lang} dir={nowClip.lang === 'ar' ? 'rtl' : 'ltr'} className="line-clamp-2">{nowClip.text}</span>
                      ) : (
                        'Tap a line: real voice, mouth timed by its text. · اضغط ليتكلم'
                      )}
                    </p>
                  </div>
                )}

                {tab === 'style' && (
                  <div data-tabpanel="style">
                    <Label en="Listening style" ar="أسلوب الإصغاء" />
                    <div className="grid grid-cols-4 gap-1.5" role="group" aria-label="Listening style">
                      {LISTEN.map((c) => (
                        <Chip key={c.id} en={c.en} ar={c.ar} data-listen={c.id} active={state === 'listening' && picked.listen === c.id} onClick={() => listen(c)} />
                      ))}
                    </div>
                    <Label en="Talking style" ar="أسلوب الكلام" />
                    <div className="grid grid-cols-5 gap-1" role="group" aria-label="Talking style">
                      {TALK.map((c) => (
                        <Chip key={c.id} en={c.en} ar={c.ar} data-talk={c.id} active={state === 'speaking' && picked.talk === c.id} onClick={(e) => talk(c, e)} />
                      ))}
                    </div>
                  </div>
                )}

                {tab === 'search' && (
                  <div data-tabpanel="search">
                    <Label en="Where to look" ar="أين يبحث" />
                    <div className="grid grid-cols-[3.4rem_repeat(3,minmax(0,1fr))] items-center gap-1.5" role="group" aria-label="Search">
                      {OUTCOMES.map((o) => [
                        <span key={`${o.id}-l`} className="flex flex-col text-center text-[11px] font-bold leading-tight text-white/75">
                          <span>{o.en}</span>
                          <span lang="ar" dir="rtl">{o.ar}</span>
                        </span>,
                        ...KINDS.map((k) => (
                          <Chip
                            key={`${k.id}-${o.id}`}
                            en={k.en}
                            ar={k.ar}
                            data-search={`${k.id}-${o.id}`}
                            active={picked.search === `${k.id}-${o.id}`}
                            onClick={() => search(k.id, o.id)}
                          />
                        )),
                      ])}
                    </div>
                    <Label en="Web page in his hand" ar="صفحة ويب في يده" />
                    <div className="grid grid-cols-2 gap-1.5" role="group" aria-label="Search the web">
                      {WEB_SAMPLES.map((w) => {
                        const l = lang === 'en' ? 'en' : 'ar';
                        return (
                          <Chip
                            key={w.id}
                            en={w.sub ? w.sub.en : w.en}
                            ar={w.sub ? w.sub.ar : w.ar}
                            data-search-web={w.id}
                            data-lang={l}
                            active={picked.search === `webpage-${w.name}-${w.outcome}`}
                            onClick={() => searchWeb(w.name, w.outcome)}
                          />
                        );
                      })}
                    </div>
                  </div>
                )}

                {tab === 'moments' && (
                  <div data-tabpanel="moments">
                    <Label en="Moments" ar="لحظات" />
                    <div className="grid grid-cols-4 gap-1.5" role="group" aria-label="Moments">
                      {MOMENTS.map((c) => (
                        <Chip key={c.id} en={c.en} ar={c.ar} data-moment={c.id} active={picked.moment === c.id} onClick={() => moment(c.id)} />
                      ))}
                    </div>
                    <p className="mt-2 px-1 text-xs leading-snug text-white/70">
                      Greet and Goodbye start a new session, like a salam or a farewell in the agent&apos;s first words. They move the mouth with no sound.
                    </p>
                  </div>
                )}

                {tab === 'basics' && (
                  <div data-tabpanel="basics">
                    <Label en="Agent state" ar="الحالة" />
                    <div className="grid grid-cols-3 gap-1.5" role="group" aria-label="Agent state">
                      {MAIN_STATES.map((s) => (
                        <Chip key={s.id} en={s.en} ar={s.ar} data-state-chip={s.id} active={state === s.id} onClick={() => choose(s.id)} />
                      ))}
                    </div>
                    {/* hotfix-2: the old "Speaking" chip. A made-up voice moves the mouth with NO sound, so it is
                        named for what it is and kept visually secondary (dashed, small, quiet). Real speech is Speak. */}
                    <button
                      type="button"
                      data-state-chip="speaking"
                      aria-pressed={state === 'speaking' && !voice.playing}
                      className={`mt-1.5 flex min-h-9 w-full items-center justify-center gap-2 rounded-full border border-dashed px-3 text-[11px] font-medium leading-tight transition-colors ${
                        state === 'speaking' && !voice.playing
                          ? 'border-white/70 bg-white/20 text-white'
                          : 'border-white/30 bg-transparent text-white/65 hover:bg-white/10'
                      }`}
                      onClick={() => choose('speaking')}
                    >
                      <VolumeX className="h-3.5 w-3.5 shrink-0" strokeWidth={1.75} />
                      <span>{STATES[3].en}</span>
                      <span lang="ar" dir="rtl">{STATES[3].ar}</span>
                    </button>
                    <Label en="Actions" ar="حركات" />
                    <div className="grid grid-cols-3 gap-1.5" role="group" aria-label="Actions">
                      {ACTIONS.map((a) => (
                        <Chip key={a.id} en={a.en} ar={a.ar} data-action={a.id} busy={queued === a.id} onClick={() => play(a)} />
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-1.5 flex items-center gap-3 text-xs font-semibold text-white/80">
                <span className="shrink-0">Voice level · مستوى الصوت</span>
                <div className="h-2 min-w-0 flex-1 overflow-hidden rounded-full bg-white/15" aria-hidden="true">
                  <div ref={meter} data-level-meter="" className="h-full origin-left rounded-full bg-white/85" style={{ transform: 'scaleX(0)' }} />
                </div>
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
