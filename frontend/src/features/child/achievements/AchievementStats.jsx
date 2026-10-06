import { CheckCircle2, Star, Medal } from 'lucide-react';
import { Card } from '../../../components/ui';
import { num, useLang, useStrings } from '../../../i18n'; // i18n // cards-spec (05)

const ITEMS = [
  { key: 'completedChallenges', icon: CheckCircle2, label: 'quests' },
  { key: 'currentLevel',        icon: Star,         label: 'level'  },
  { key: 'totalEarnedBadges',   icon: Medal,        label: 'badges' },
];

const AchievementStats = ({ completedChallenges, currentLevel, totalEarnedBadges }) => {
  const lang = useLang();
  const s = useStrings().badges;
  const values = { completedChallenges, currentLevel, totalEarnedBadges };

  return (
    <Card
      padding="md"
      className="flex shrink-0"
      role="region"
      aria-label={s.summaryAria}
    >
      {ITEMS.map((item, idx) => {
        const Icon = item.icon;
        return (
          <div
            key={item.key}
            className={`flex flex-1 flex-col items-center justify-center gap-1 py-1 ${idx > 0 ? 'border-s border-border' : ''}`}
          >
            <span className="flex size-10 items-center justify-center rounded-full bg-accent-soft text-text">
              <Icon className="size-5" aria-hidden="true" />
            </span>
            <p className="text-title tabular-nums leading-none text-text">
              {num(values[item.key], lang)}
            </p>
            <p className="text-label text-text-muted">{s.stats[item.label]}</p>
          </div>
        );
      })}
    </Card>
  );
};

export default AchievementStats;
