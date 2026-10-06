import { Lock } from 'lucide-react';
import { Pill, ProgressBar, Sheet } from '../../../components/ui';
import { shortDate, useLang, useStrings } from '../../../i18n';
import { hasProgress } from './badgeUtils';
import { Medallion } from './BadgeTile';

/** Details of one badge, earned or locked (render only when a badge is picked). */
export default function BadgeSheet({ badge, onClose }) {
  const lang = useLang();
  const s = useStrings().badges;
  const earnedDate = badge.earned && badge.earnedAt ? shortDate(badge.earnedAt, lang) : '';

  return (
    <Sheet open onClose={onClose} title={badge.name}>
      <Medallion imageSrc={badge.imageSrc} earned={badge.earned} className="size-28" />
      <p dir="auto" className="text-body text-text-muted">
        {badge.description?.trim() ? badge.description : s.defaultHint}
      </p>
      {badge.earned ? (
        <Pill variant="success" className="self-start">{earnedDate ? s.earnedOn(earnedDate) : s.earned}</Pill>
      ) : (
        <>
          <Pill icon={<Lock className="size-4" aria-hidden="true" />} className="self-start">{s.locked}</Pill>
          {hasProgress(badge) ? (
            <div>
              <div className="mb-2 flex items-baseline justify-between text-label text-text-muted">
                <span>{s.progress}</span>
                <span className="text-text">{s.progressOf(badge.progressCurrent, badge.requirementValue)}</span>
              </div>
              <ProgressBar
                label={s.progressLabel(badge.name)}
                progress={Math.round((badge.progressCurrent / badge.requirementValue) * 100)}
              />
            </div>
          ) : null}
        </>
      )}
    </Sheet>
  );
}
