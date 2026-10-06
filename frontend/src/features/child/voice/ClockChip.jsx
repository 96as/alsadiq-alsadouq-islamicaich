import { formatClock } from './voiceGuards';
import './voiceui.css';

const R = 14;
const CIRC = 2 * Math.PI * R;

/**
 * ClockChip: the 5-minute session timer. A ring that empties, the minutes and seconds, and
 * from the last minute on a warm colour and a slow breath. It is a timer role, not a live
 * region: the one-minute toast does the announcing, so a screen reader is not read every second.
 */
const ClockChip = ({ secondsLeft, totalSeconds, phase, t, lang }) => {
  const total = Math.max(1, totalSeconds || secondsLeft || 1);
  const fraction = Math.max(0, Math.min(1, secondsLeft / total));
  return (
    <div className="vu vu-chip" data-phase={phase} dir={t.dir} role="timer" aria-label={`${t.clockLabel}: ${formatClock(secondsLeft, lang)}`}>
      <svg className="vu-chip-ring" viewBox="0 0 36 36" aria-hidden="true">
        <circle className="track" cx="18" cy="18" r={R} />
        <circle
          className="fill"
          cx="18"
          cy="18"
          r={R}
          strokeDasharray={CIRC}
          strokeDashoffset={CIRC * (1 - fraction)}
        />
      </svg>
      <span className="vu-chip-time" dir="ltr">{formatClock(secondsLeft, lang)}</span>
      {phase === 'ending' ? <span className="vu-chip-note">{t.ending}</span> : null}
    </div>
  );
};

export default ClockChip;
