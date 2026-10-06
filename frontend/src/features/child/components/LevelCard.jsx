import { Card, ProgressBar } from '../../../components/ui';

/**
 * LevelCard, current level plus XP progress.
 *
 * @param {string} title    - Level title (e.g. "Level 3 Explorer")
 * @param {number} progress - 0-100 percentage
 * @param {string} percentLabel - i18n: the percentage as shown (Arabic digits and the Arabic percent sign in Arabic)
 */
const LevelCard = ({ title = 'Level 1 Explorer', progress = 0, dir, progressLabel = 'progress', percentLabel }) => { // avatar-integ
  const safeProgress = Math.max(0, Math.min(100, progress));

  return (
    <Card className="min-w-0 flex-1 px-4 py-3" dir={dir}>
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-label truncate text-text">{title}</p>
        <p className="text-label text-text-muted">{percentLabel ?? `${safeProgress}%`}</p>
      </div>
      <ProgressBar className="mt-2" progress={safeProgress} label={`${title} ${progressLabel}`} />
    </Card>
  );
};

export default LevelCard;
