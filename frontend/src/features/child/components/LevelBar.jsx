import { Leaf, Star } from 'lucide-react';
import { COPY, localDigits } from '../../demo/copy';

/**
 * The call screen's level bar (WebUI photo 1): "Lv 2", the points, and a tall rounded bar that fills from the leaf at
 * the bottom up to the star as the child nears the next level. Decoration for the eyes; the whole thing is one labelled
 * image for screen readers. It never takes a tap.
 *
 * Props: levelData ({ level_number, progress_pct, total_points } or null), lang ('ar' | 'en').
 */
export default function LevelBar({ levelData = null, lang = 'ar' }) {
  const c = COPY[lang]?.idle || COPY.ar.idle;
  const n = levelData?.level_number || 1;
  const pct = Math.max(0, Math.min(100, Math.round(levelData?.progress_pct ?? 0)));
  const digits = localDigits(n, lang);
  const points = levelData?.total_points;
  return (
    <div className="mc-level" role="img" aria-label={c.levelAria(digits, localDigits(pct, lang))} data-level-bar="">
      <span className="mc-level-n">{c.lv(digits)}</span>
      {typeof points === 'number' ? <span className="mc-level-pts">{c.points(localDigits(points, lang))}</span> : null}
      <div className="mc-bar" dir={lang === 'ar' ? 'rtl' : 'ltr'} aria-hidden="true">
        <div className="mc-bar-fill" style={{ height: `${Math.max(pct, 6)}%` }} />
        <span className="mc-bar-star"><Star /></span>
        <span className="mc-bar-leaf"><Leaf /></span>
      </div>
    </div>
  );
}
