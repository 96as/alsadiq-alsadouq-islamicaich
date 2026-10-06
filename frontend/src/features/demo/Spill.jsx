import { useEffect, useMemo, useRef, useState } from 'react';

/**
 * Petals by day and fireflies by night that drift out of the arch onto the wall (12 small DOM sprites,
 * moved with transform and opacity only, no per-frame JS). At sunset it is a mix of both. They never
 * take a tap, are hidden from screen readers, and are off under reduced motion (see demo.css).
 * They pause while the arch is scrolled out of view, like the forest itself.
 *
 *   time   'morning' | 'noon' | 'maghrib' | 'night'
 */
const COUNT = 12;

// A fixed spread, so the sprites do not jump around when the time changes.
const SPRITES = Array.from({ length: COUNT }, (_, i) => ({
  x: 8 + ((i * 37) % 84), // start point across the arch, in %
  dx: ((i % 2 ? 1 : -1) * (30 + ((i * 53) % 90))), // how far it drifts sideways, in px
  delay: -((i * 1.7) % 9), // negative: already in flight when the page opens
  dur: 8 + ((i * 29) % 70) / 10, // 8 to 15 s
  size: 8 + ((i * 7) % 8), // 8 to 15 px
  rot: (i * 47) % 360,
}));

export default function Spill({ time }) {
  const ref = useRef(null);
  const [paused, setPaused] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || !('IntersectionObserver' in window)) return undefined;
    const io = new IntersectionObserver(([entry]) => setPaused(!entry.isIntersecting), { threshold: 0 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  const kinds = useMemo(
    () => SPRITES.map((_, i) => (time === 'night' ? 'fly' : time === 'maghrib' && i % 2 ? 'fly' : 'petal')),
    [time],
  );
  return (
    <div ref={ref} className="demo-spill" aria-hidden="true" data-time={time} data-paused={paused ? 'true' : 'false'}>
      {SPRITES.map((s, i) => (
        <span
          key={`${i}-${kinds[i]}`}
          className={`demo-spill-i demo-spill-${kinds[i]}`}
          style={{
            '--x': `${s.x}%`,
            '--dx': `${s.dx}px`,
            '--delay': `${s.delay}s`,
            '--dur': `${s.dur}s`,
            '--s': `${s.size}px`,
            '--rot': `${s.rot}deg`,
          }}
        />
      ))}
    </div>
  );
}
