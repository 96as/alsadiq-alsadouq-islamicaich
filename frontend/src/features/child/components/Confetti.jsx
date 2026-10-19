import { useMemo } from 'react';

const COLOURS = ['#f7c447', '#27a857', '#ff7a59', '#5aa9ff', '#c58bff', '#ffd9a0'];

/** A small seeded generator, so a burst looks the same on every render. */
function seeded(seed) {
  const box = { s: seed * 9301 + 49297 };
  return () => {
    box.s = (box.s * 9301 + 49297) % 233280;
    return box.s / 233280;
  };
}

/**
 * A short confetti burst (CSS only, about 1.4 s) for points, level-ups and finished quests.
 * Pieces fly out from the centre of their parent; nothing renders under reduced motion.
 */
export default function Confetti({ count = 22, seed = 1 }) {
  const reduced = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const pieces = useMemo(() => {
    const rnd = seeded(seed);
    return Array.from({ length: count }, (_, i) => {
      const a = (i / count) * Math.PI * 2 + rnd() * 0.5;
      const r = 70 + rnd() * 90;
      return {
        dx: Math.cos(a) * r,
        dy: Math.sin(a) * r - 40,
        rot: Math.round(rnd() * 540 - 270),
        c: COLOURS[i % COLOURS.length],
        d: Math.round(rnd() * 120),
        w: 6 + Math.round(rnd() * 5),
      };
    });
  }, [count, seed]);
  if (reduced) return null;
  return (
    <span className="confetti" aria-hidden="true">
      {pieces.map((p, i) => (
        <i
          key={i}
          style={{ '--dx': `${p.dx}px`, '--dy': `${p.dy}px`, '--rot': `${p.rot}deg`, background: p.c, animationDelay: `${p.d}ms`, width: p.w, height: p.w * 0.6 }}
        />
      ))}
    </span>
  );
}
