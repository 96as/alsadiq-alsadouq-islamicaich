import { Check, Lock, Medal } from 'lucide-react';
import { cx, FOCUS_RING } from '../../../components/ui/cx';
import { useStrings } from '../../../i18n'; // i18n // cards-spec (05)
import { hasProgress } from './badgeUtils';

/** The round badge picture. Earned: full colour with a check on the corner. Locked: grey with a lock (not colour-only). */
export function Medallion({ imageSrc, earned, className = 'size-24' }) {
  const Corner = earned ? Check : Lock;
  return (
    <span className={cx('relative mx-auto block shrink-0', className)}>
      <span
        className={cx(
          'flex size-full items-center justify-center overflow-hidden rounded-full',
          earned ? 'bg-celebration' : 'bg-surface-alt',
        )}
      >
        {imageSrc ? (
          <img
            src={imageSrc}
            alt=""
            className={cx('h-full w-full object-contain p-3', !earned && 'opacity-40 grayscale')}
            loading="lazy"
            draggable={false}
          />
        ) : (
          <Medal className={cx('size-1/2', earned ? 'text-on-accent' : 'text-text-muted')} aria-hidden="true" />
        )}
      </span>
      <span
        className={cx(
          'absolute -bottom-1 -end-1 grid size-8 place-items-center rounded-full ring-2 ring-surface',
          earned ? 'bg-primary text-on-primary' : 'bg-surface-alt text-text',
        )}
        aria-hidden="true"
      >
        <Corner className="size-5" />
      </span>
    </span>
  );
}

/** One badge: medallion and name, plus "1 / 3" when locked. The details open in a sheet. */
const BadgeTile = ({ badge, onOpen }) => {
  const s = useStrings().badges;
  const progress = !badge.earned && hasProgress(badge) ? s.progressOf(badge.progressCurrent, badge.requirementValue) : '';
  const label = badge.earned ? s.earnedLabel(badge.name) : s.lockedLabel(badge.name);

  return (
    <button
      type="button"
      onClick={onOpen}
      aria-label={progress ? `${label}, ${progress}` : label}
      className={cx(
        'flex h-full min-h-target w-full cursor-pointer flex-col items-center gap-2 rounded-3xl border border-border bg-surface px-2 py-3 text-center',
        'transition-transform motion-safe:active:scale-[0.98]',
        FOCUS_RING,
      )}
    >
      <Medallion imageSrc={badge.imageSrc} earned={badge.earned} className="size-18" />
      <span dir="auto" className="text-label text-text">{badge.name}</span>
      {progress ? <span className="-mt-1 text-label text-text-muted">{progress}</span> : null}
    </button>
  );
};

export default BadgeTile;
