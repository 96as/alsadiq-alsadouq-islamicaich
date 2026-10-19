import { Check, Hourglass, Sparkles } from 'lucide-react';
import { Pill } from '../../../components/ui';
import { cx, FOCUS_RING } from '../../../components/ui/cx';
import { useLang, useStrings } from '../../../i18n';
import { TYPE_ICON } from './questUtils';

/** Empty ring = to do, dashed hourglass = waiting for a parent, filled check = done. */
function StatusCircle({ status }) {
  const base = 'grid size-8 shrink-0 place-items-center rounded-full';
  if (status === 'completed') {
    return (
      <span className={cx(base, 'bg-primary text-on-primary')} aria-hidden="true">
        <Check className="size-5" />
      </span>
    );
  }
  if (status === 'pending_verification') {
    return (
      <span className={cx(base, 'border-2 border-dashed border-info bg-info-soft text-text')} aria-hidden="true">
        <Hourglass className="size-4" />
      </span>
    );
  }
  return <span className={cx(base, 'border-2 border-text-muted')} aria-hidden="true" />;
}

/** One quest on one line. The accessible name carries the status word, so it never relies on colour. */
export default function QuestRow({ quest, onOpen }) {
  const lang = useLang();
  const s = useStrings().quests;
  const TypeIcon = TYPE_ICON[quest.questType];
  const points = s.points(quest.rewardPoints, lang);
  const done = quest.status === 'completed';

  return (
    <button
      type="button"
      onClick={onOpen}
      aria-label={s.rowLabel(quest.title, s.status[quest.status] ?? s.status.not_started, points)}
      className={cx(
        'flex min-h-target w-full cursor-pointer items-center gap-3 rounded-3xl border border-border px-4 py-2 text-start',
        'transition-transform motion-safe:active:scale-[0.99]',
        FOCUS_RING,
        done ? 'bg-primary-soft' : 'bg-surface',
      )}
    >
      <StatusCircle status={quest.status} />
      <span dir="auto" className="min-w-0 flex-1 line-clamp-2 text-heading text-text">{quest.title}</span>
      {TypeIcon ? <TypeIcon className="size-6 shrink-0 text-text-muted" aria-hidden="true" /> : null}
      <Pill variant="warning" icon={<Sparkles className="size-4" aria-hidden="true" />} className="shrink-0">
        {points}
      </Pill>
    </button>
  );
}
