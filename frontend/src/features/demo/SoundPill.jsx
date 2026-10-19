import { useCallback, useEffect, useRef, useState } from 'react';
import { Volume2, VolumeX } from 'lucide-react';
import { soundBus, voiceStarted } from './soundBus';

/**
 * The opt-in sound pill. Nothing is fetched and no AudioContext exists until the visitor presses it
 * (sound.js is imported on that press). The choice is remembered in localStorage (`sadiq_sound`): a
 * visitor who left it on sees it on, and the sound starts with their first tap on the page (browsers
 * only allow audio after a tap). Once a voice session has started in this tab the pill goes away and
 * the sounds stay off.
 *
 *   t      the copy for the current language (soundOn, soundOff)
 *   time   the time of day, so the bed follows it
 */
const KEY = 'sadiq_sound';

const remembered = () => {
  try {
    return window.localStorage.getItem(KEY) === '1';
  } catch {
    return false;
  }
};
const remember = (on) => {
  try {
    window.localStorage.setItem(KEY, on ? '1' : '0');
  } catch {
    // not saved: the choice still works for this visit
  }
};

export default function SoundPill({ t, time }) {
  const [gone] = useState(voiceStarted);
  const [on, setOn] = useState(() => !voiceStarted() && remembered());
  const mod = useRef(null);
  const timeRef = useRef(time);

  const begin = useCallback(async () => {
    if (!mod.current) mod.current = await import('./sound');
    mod.current.setPeriod(timeRef.current);
    return mod.current.start();
  }, []);

  // The bed follows the time of day.
  useEffect(() => {
    timeRef.current = time;
    soundBus.setTime?.(time);
  }, [time]);

  // A remembered "on" starts with the first tap anywhere on the page.
  useEffect(() => {
    if (!on || mod.current || gone) return undefined;
    const go = () => {
      begin().then((ok) => {
        if (!ok) setOn(false);
      });
    };
    document.addEventListener('pointerdown', go, { once: true, capture: true });
    return () => document.removeEventListener('pointerdown', go, { capture: true });
    // Armed once for a remembered choice; a press on the pill itself takes over from here.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (gone) return null;

  const press = async () => {
    if (on) {
      setOn(false);
      remember(false);
      mod.current?.pause();
      return;
    }
    setOn(true);
    remember(true);
    const ok = await begin();
    if (!ok) {
      setOn(false);
      remember(false);
    }
  };

  const Icon = on ? Volume2 : VolumeX;
  return (
    <button
      type="button"
      className="demo-pill demo-sound-btn"
      aria-pressed={on}
      aria-label={on ? t.soundOn : t.soundOff}
      onClick={press}
    >
      <Icon className="demo-sound-icon" strokeWidth={2.25} aria-hidden="true" />
    </button>
  );
}
