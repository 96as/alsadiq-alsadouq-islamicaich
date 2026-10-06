import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom'; // avatar-integ: the meadow Home's quest card
import { ChevronRight, Flame, Keyboard, Mic, RotateCcw, Sparkles, Volume2, VolumeX } from 'lucide-react';
import '../../demo/demo.css';
import { COPY, localDigits } from '../../demo/copy';
import { useClockPeriod, useReducedMotion } from '../../demo/hooks';
import { StageLayer, StaticBubble } from '../../demo/stageParts';
import useStageSpeech from '../../demo/useStageSpeech';
import TimePill from '../../demo/TimePill';
import SoundPill from '../../demo/SoundPill';
import { markVoiceStarted, soundBus } from '../../demo/soundBus';
import { hideVeilWhen } from '../../demo/transitionVeil';
import { readDemoLang } from '../../../services/demoService';
import { useAuth } from '../../../context/AuthContext';
import { ROUTES } from '../../../routes';
import { num } from '../../../i18n'; // i18n // avatar-integ
import { playFx, readSoundOn, writeSoundOn } from './soundFx';
import './meadowScreens.css'; // avatar-integ: the meadow Home and call screens (WebUI photos 1 and 2)

/**
 * The child's idle screen, drawn over the forest stage (ForestStage is the parent; this is its content).
 *
 * Same world as the demo landing, in the demo language (Arabic first): Sadiq in the forest with a
 * bubble anchored to his head, the lantern, book and bulbul to tap, a small level chip, the time pill,
 * and one big sun-coloured key under him. Tapping Sadiq does what the key does. There is no glass card.
 *
 * `status` picks the state (the copy for each is in copy.js, idle.*):
 *   idle        greeting by name and time of day, key "Start talking"
 *   connecting  "One moment... getting my ears ready", the key shimmers and is disabled
 *   error       "Couldn't start the talk...", key "Try again"
 *   voiceoff    the session is open but has no voice (text mode or a voice error), key "Type to Al-Sadiq"
 *   (idle with `ended`) "Our talk is over. Talk again?", key "Start a new talk"
 *
 * Props
 *   status      'idle' | 'completed' | 'connecting' | 'error' | 'voiceoff'
 *   ended       true once a talk has finished on this screen
 *   slow        true when connecting takes longer than expected
 *   refusal     the server's { ar, en } message for a refused start (daily limit and the like), or null
 *   levelData   { level_number, level_name, progress_pct } from the gamification API, or null
 *   quest       i18n: { title } of the quest to show on the meadow Home's quest card, or null for the generic card
 *   onStart     start (or retry) the session
 *   onType      open the text chat (voiceoff)
 *   controlRef  the ref ForestStage fills (the page passes the same ref as `walkControlRef`)
 *   forest      true when the forest stage is the parent (false: the painted meadow, no props)
 *   meadow      avatar-integ: true when MeadowStage is the parent (the painted meadow with Sadiq walking on the path):
 *               the Home of WebUI photo 2 (title, green key, level card, quest card), no forest pills
 *   lang        'ar' | 'en', the page's language (default: the demo language)
 *   onToggleLang  when given, a small language pill sits beside the time pill
 *   langLabel   the pill's accessible name
 */

const WALK_WAVE = 3; // walkIn.js STATE value for the wave
const GREET_FALLBACK_MS = 8000;
const LEVEL_R = 17;
const LEVEL_C = 2 * Math.PI * LEVEL_R;

function LevelChip({ c, lang, levelData }) {
  const n = levelData?.level_number || 1;
  const pct = Math.max(0, Math.min(100, Math.round(levelData?.progress_pct ?? 0)));
  const digits = localDigits(n, lang);
  const rawName = levelData?.level_name;
  const name = c.levels[rawName] || (lang === 'en' ? rawName : null);
  return (
    <div className="demo-level" role="img" aria-label={c.levelAria(digits, localDigits(pct, lang))}>
      <svg className="demo-level-ring" viewBox="0 0 44 44" aria-hidden="true">
        <circle cx="22" cy="22" r={LEVEL_R} className="demo-level-track" />
        <circle
          cx="22"
          cy="22"
          r={LEVEL_R}
          className="demo-level-fill"
          strokeDasharray={`${(LEVEL_C * pct) / 100} ${LEVEL_C}`}
        />
        <text x="22" y="22" className="demo-level-n" textAnchor="middle" dominantBaseline="central">{digits}</text>
      </svg>
      <span className="demo-level-text">
        <span className="demo-level-name">{name || c.level(digits)}</span>
        {name ? <span className="demo-level-sub">{c.level(digits)}</span> : null}
      </span>
    </div>
  );
}

export default function ChildIdleStage({
  status = 'idle',
  ended = false,
  slow = false,
  refusal = null,
  levelData = null,
  quest = null,
  onStart,
  onType,
  controlRef,
  forest = true,
  meadow = false, // avatar-integ
  lang: langProp = null,
  onToggleLang,
  langLabel,
}) {
  const { user } = useAuth();
  const [demoLang] = useState(readDemoLang);
  const lang = langProp || demoLang;
  const t = COPY[lang];
  const c = t.idle;
  const reduced = useReducedMotion();
  const clock = useClockPeriod();
  const [picked, setPicked] = useState(null);
  const time = picked || clock;
  const [touched, setTouched] = useState(false);

  const speech = useStageSpeech({ controlRef, t, live: forest });
  const { later, say, activity, lastActive, bubble } = speech;

  // Arriving from the landing's veil: lift it once Sadiq is on screen (it also goes away by itself).
  useEffect(() => {
    hideVeilWhen(() => !forest || controlRef.current?.rt?.screen?.visible);
  }, [forest, controlRef]);

  const name = user?.first_name || '';
  const greeting = [c.hello(name), c.timePhrase[time]].filter(Boolean).join(' ');
  const greetingRef = useRef(greeting);
  useEffect(() => {
    greetingRef.current = greeting;
  }, [greeting]);

  const connecting = status === 'connecting';
  const failed = status === 'error';
  const voiceOff = status === 'voiceoff';

  const stateLine = (() => {
    if (connecting) return slow ? `${c.connecting} ${c.slow}` : c.connecting;
    if (failed) return refusal?.[lang] || c.failed;
    if (voiceOff) return c.voiceOff;
    return ended ? c.ended : null;
  })();

  // Sadiq says the state's line and keeps it up (a long hold) until the state changes.
  useEffect(() => {
    if (stateLine) say(stateLine, { hold: 120000 });
  }, [stateLine, say]);

  // The greeting: once, when the walk-in reaches the wave (the first thing said, unless a state line came first).
  const greeted = useRef(false);
  useEffect(() => {
    if (stateLine || greeted.current) return undefined;
    const greet = () => {
      if (greeted.current) return;
      greeted.current = true;
      lastActive.current = performance.now();
      say(greetingRef.current, { hold: 5000 });
    };
    if (!forest && !meadow) {
      const id = window.setTimeout(greet, 900);
      return () => window.clearTimeout(id);
    }
    const poll = window.setInterval(() => {
      const w = controlRef.current?.walk;
      if (w && w.state >= WALK_WAVE) greet();
    }, 150);
    const fallback = window.setTimeout(greet, GREET_FALLBACK_MS);
    return () => {
      window.clearInterval(poll);
      window.clearTimeout(fallback);
    };
  }, [stateLine, forest, meadow, controlRef, say, lastActive]);

  // The time pill forces the forest's time; the page colours follow through data-time here.
  const pickTime = useCallback((name) => {
    setPicked(name);
    controlRef.current?.setTime?.(name);
  }, [controlRef]);

  // The key and Sadiq do the same thing.
  const act = useCallback(() => {
    if (connecting) return;
    setTouched(true);
    if (voiceOff) {
      onType?.();
    } else {
      markVoiceStarted(); // the forest sounds end when a voice session begins
      onStart?.();
    }
  }, [connecting, voiceOff, onStart, onType]);

  // The child's own switch for the little UI sounds (off until chosen, remembered on this device).
  const [soundOn, setSoundOn] = useState(readSoundOn);
  const toggleSound = () => {
    const next = !soundOn;
    writeSoundOn(next);
    setSoundOn(next);
    if (next) playFx('chime');
  };
  // The level ring fills from empty when Home appears.
  const [ringIn, setRingIn] = useState(false);
  useEffect(() => {
    const id = window.setTimeout(() => setRingIn(true), 350);
    return () => window.clearTimeout(id);
  }, []);

  const press = () => {
    if (connecting) return;
    playFx('tap');
    try {
      navigator.vibrate?.(10);
    } catch {
      // not supported
    }
    act();
  };

  // Tap Sadiq: he hops, says it, and the key's action follows a beat later (so the hop is seen).
  const startingRef = useRef(false);
  const tapSadiq = useCallback(() => {
    activity();
    if (connecting || startingRef.current) return;
    startingRef.current = true;
    if (!voiceOff) {
      controlRef.current?.hop?.();
      soundBus.play?.('hop');
      say(t.letsTalk, { hold: 1500 });
    }
    later(() => {
      startingRef.current = false;
      act();
    }, reduced || voiceOff ? 150 : 450);
  }, [activity, connecting, voiceOff, controlRef, say, t.letsTalk, later, reduced, act]);

  const Icon = voiceOff ? Keyboard : failed ? RotateCcw : Mic;
  const label = connecting ? c.working : voiceOff ? c.type : failed ? c.retry : ended ? c.again : c.talk;

  if (meadow) {
    // avatar-integ: WebUI photo 2. Sadiq stands in the painted meadow behind this layer; the cards sit on a soft fade.
    const n = levelData?.level_number || 1;
    const pct = Math.max(0, Math.min(100, Math.round(levelData?.progress_pct ?? 0)));
    const digits = localDigits(n, lang);
    const questTitle = quest?.title?.trim() || c.questTitle;
    const rawName = levelData?.level_name;
    const levelName = c.levels[rawName] || (lang === 'en' ? rawName : null) || c.level(digits);
    const streak = levelData?.current_streak || 0;
    const points = levelData?.total_points;
    return (
      <div className="mh" data-time={time} dir={t.dir} lang={t.lang} data-status={status}>
        <div className="mh-top">
          {/* i18n: a Latin name inside the Arabic greeting sits in its own isolate, so the ! and the Arabic words keep their order. */}
          <h1 className="mh-title">
            {name ? <>{c.salamLead}<bdi dir="auto">{name}</bdi>!</> : c.salam('')}
          </h1>
          <div className="mh-top-actions">
            <button type="button" className="mh-snd" onClick={toggleSound} aria-pressed={soundOn} aria-label={soundOn ? c.sound.on : c.sound.off} title={soundOn ? c.sound.on : c.sound.off}>
              {soundOn ? <Volume2 aria-hidden="true" /> : <VolumeX aria-hidden="true" />}
            </button>
            {onToggleLang ? (
              <button type="button" className="mh-lang" onClick={onToggleLang} aria-label={langLabel} lang={lang === 'ar' ? 'en' : 'ar'}>
                {lang === 'ar' ? 'EN' : 'ع'}
              </button>
            ) : null}
          </div>
        </div>
        {stateLine ? <p className="mh-state" role="status">{stateLine}</p> : null}
        {/* Tap Sadiq: the same as the green key (the key is the keyboard path, so this stays out of the tab order). */}
        <button type="button" className="mh-tap" tabIndex={-1} aria-label={c.stageLabel} onClick={tapSadiq} />
        <div className="mh-bottom">
          <button
            type="button"
            className="mh-cta"
            data-loading={connecting ? 'true' : 'false'}
            aria-busy={connecting}
            disabled={connecting}
            onClick={press}
          >
            <Icon aria-hidden="true" strokeWidth={2.4} />
            <span>{label}</span>
          </button>
          <div className="mh-cards">
            <div className="mh-card mh-level" role="img" aria-label={c.levelAria(digits, localDigits(pct, lang))}>
              <svg className="mh-ring" viewBox="0 0 56 56" aria-hidden="true">
                <circle cx="28" cy="28" r="23" className="mh-ring-track" />
                <circle cx="28" cy="28" r="23" className="mh-ring-fill" strokeDasharray={`${(2 * Math.PI * 23 * (ringIn ? pct : 0)) / 100} ${2 * Math.PI * 23}`} />
                <text x="28" y="28" className="mh-ring-n" textAnchor="middle" dominantBaseline="central">{c.lv(digits)}</text>
              </svg>
              <span className="mh-level-text">
                <span className="mh-level-name">{levelName}</span>
                {streak > 0 ? (
                  <span className="mh-level-line"><Flame aria-hidden="true" className="mh-flame" />{c.streak(num(streak, lang))}</span>
                ) : null}
                {typeof points === 'number' ? <span className="mh-level-pts">{c.points(localDigits(points, lang))}</span> : null}
              </span>
            </div>
            <Link to={ROUTES.CHILD_QUESTS} className="mh-card mh-quest">
              <Sparkles aria-hidden="true" className="mh-quest-icon" />
              <span className="mh-quest-text">
                <span className="mh-quest-label">{c.questLabel}</span>
                <span className="mh-quest-title" dir="auto">{questTitle}</span>
              </span>
              <ChevronRight aria-hidden="true" className="mh-quest-go" />
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="demo-tokens demo-idle" data-time={time} dir={t.dir} lang={t.lang} data-status={status}>
      <div className="demo-idle-top">
        <LevelChip c={c} lang={lang} levelData={levelData} />
        <div className="demo-idle-pills">
          {onToggleLang ? (
            <button
              type="button"
              className="demo-pill demo-idle-lang"
              onClick={onToggleLang}
              aria-label={langLabel}
              lang={lang === 'ar' ? 'en' : 'ar'}
            >
              {lang === 'ar' ? 'EN' : 'ع'}
            </button>
          ) : null}
          <TimePill t={t} now={clock} picked={picked} onPick={pickTime} />
          <SoundPill t={t} time={time} />
        </div>
      </div>

      {forest ? (
        <StageLayer controlRef={controlRef} t={t} speech={speech} onTapSadiq={tapSadiq} sadiqLabel={c.talk} />
      ) : bubble ? (
        <StaticBubble bubble={bubble} />
      ) : null}

      <div className="demo-idle-bottom">
        <button
          type="button"
          className="demo-cta demo-talk"
          data-loading={connecting ? 'true' : 'false'}
          data-touched={touched ? 'true' : undefined}
          aria-busy={connecting}
          disabled={connecting}
          onClick={press}
          onPointerEnter={() => setTouched(true)}
          onFocus={() => setTouched(true)}
        >
          <span className="demo-talk-icon" aria-hidden="true">
            <Icon strokeWidth={2.5} />
          </span>
          <span className="demo-cta-stack">
            <span className="demo-cta-label" data-on="true">{label}</span>
          </span>
          <span className="demo-cta-shimmer" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
