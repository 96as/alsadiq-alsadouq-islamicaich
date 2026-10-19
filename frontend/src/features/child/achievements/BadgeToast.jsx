import { useEffect, useState } from 'react';
import { Medal } from 'lucide-react';
import { useStrings } from '../../../i18n'; // i18n // cards-spec (05)

/**
 * Reusable achievement unlock toast.
 *
 * @param {{
 *   badgeName: string;
 *   badgeIcon?: string | React.ReactNode;
 *   onDone?: () => void;
 * }} props
 */
export default function BadgeToast({ badgeName, badgeIcon, onDone }) {
  const [visible, setVisible] = useState(false);
  const s = useStrings().badges;

  useEffect(() => {
    const enterTimer = window.setTimeout(() => setVisible(true), 10);
    const leaveTimer = window.setTimeout(() => setVisible(false), 3000);
    const doneTimer = window.setTimeout(() => onDone?.(), 3300);

    return () => {
      window.clearTimeout(enterTimer);
      window.clearTimeout(leaveTimer);
      window.clearTimeout(doneTimer);
    };
  }, [onDone]);

  const iconNode = typeof badgeIcon === 'string'
    ? <img src={badgeIcon} alt="" className="size-8 object-contain" />
    : badgeIcon || <Medal className="size-6 text-on-accent" aria-hidden="true" />;

  return (
    <div
      className="pointer-events-none fixed end-4 z-[160] max-w-[calc(100vw-2rem)]"
      style={{ bottom: 'calc(env(safe-area-inset-bottom, 0px) + 96px)' }}
    >
      <div
        className={`rounded-3xl border border-border bg-surface px-4 py-3 text-text shadow-[0_8px_24px_var(--color-shadow)] motion-safe:transition-transform motion-safe:duration-300 ${
          visible ? 'translate-x-0' : 'translate-x-[110%] rtl:-translate-x-[110%]'
        }`}
        role="status"
        aria-live="polite"
      >
        <div className="flex items-center gap-3">
          <div className="grid size-12 shrink-0 place-items-center rounded-full bg-celebration">
            {iconNode}
          </div>
          <div className="min-w-0">
            <p className="text-label text-text-muted">{s.unlocked}</p>
            <p dir="auto" className="truncate text-heading text-text">{badgeName}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
