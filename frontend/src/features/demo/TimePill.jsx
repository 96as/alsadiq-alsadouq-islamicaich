import { useEffect, useRef, useState } from 'react';
import { Clock, MoonStar, Sun, Sunrise, Sunset } from 'lucide-react';

/**
 * The time-of-day pill: a sun or moon and the current period. Tap it for a small menu with the four
 * times and "Now". Picking one makes the forest (and the page colours that follow it) glide to that
 * time; it goes back to the device clock after 90 s, or on "Now". Icon-only on phones.
 *
 *   t        the copy for the current language (timeLabel, times)
 *   now      the device clock's period, 'morning' | 'noon' | 'maghrib' | 'night'
 *   picked   the period the visitor chose, or null for the device clock
 *   onPick   (name | null) => void
 */
const ICONS = { morning: Sunrise, noon: Sun, maghrib: Sunset, night: MoonStar };
const ORDER = ['morning', 'noon', 'maghrib', 'night'];
const BACK_MS = 90000;

export default function TimePill({ t, now, picked, onPick }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const btnRef = useRef(null);
  const current = picked || now;
  const Icon = ICONS[current] || Sun;

  // Back to the device clock after 90 s.
  useEffect(() => {
    if (!picked) return undefined;
    const id = window.setTimeout(() => onPick(null), BACK_MS);
    return () => window.clearTimeout(id);
  }, [picked, onPick]);

  // Close on a tap outside or Escape (focus goes back to the pill).
  useEffect(() => {
    if (!open) return undefined;
    const onDown = (e) => {
      if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => {
      if (e.key === 'Escape') {
        setOpen(false);
        btnRef.current?.focus();
      }
    };
    document.addEventListener('pointerdown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('pointerdown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const choose = (name) => {
    onPick(name);
    setOpen(false);
    btnRef.current?.focus();
  };

  return (
    <div className="demo-time" ref={rootRef} data-picked={picked ? 'true' : 'false'}>
      <button
        ref={btnRef}
        type="button"
        className="demo-pill demo-time-btn"
        aria-label={t.timeLabel}
        aria-haspopup="true"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        <Icon className="demo-time-icon" strokeWidth={2.25} aria-hidden="true" />
        <span className="demo-time-name">{t.times[current]}</span>
      </button>
      {open ? (
        <div className="demo-time-pop" role="group" aria-label={t.timeLabel}>
          {ORDER.map((name) => {
            const I = ICONS[name];
            return (
              <button
                key={name}
                type="button"
                className="demo-time-opt"
                aria-pressed={picked === name}
                onClick={() => choose(name)}
              >
                <I strokeWidth={2.25} aria-hidden="true" />
                {t.times[name]}
              </button>
            );
          })}
          <button type="button" className="demo-time-opt" aria-pressed={!picked} onClick={() => choose(null)}>
            <Clock strokeWidth={2.25} aria-hidden="true" />
            {t.times.now}
          </button>
        </div>
      ) : null}
    </div>
  );
}
