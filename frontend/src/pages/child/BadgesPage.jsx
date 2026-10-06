import { useCallback, useEffect, useState } from 'react';
import { Medal } from 'lucide-react';
import { Button, Card, EmptyState, Pill, SegmentedControl } from '../../components/ui';
import AchievementStats from '../../features/child/achievements/AchievementStats';
import BadgeSheet from '../../features/child/achievements/BadgeSheet';
import BadgeTile from '../../features/child/achievements/BadgeTile';
import BadgeToast from '../../features/child/achievements/BadgeToast';
import { useQuestProgress } from '../../features/child/quests/QuestProgressContext';
import { fetchBadges, fetchLevel } from '../../services/gamificationService';
import { useStrings } from '../../i18n'; // i18n // cards-spec (05)

const SHELL =
  'w-full max-w-3xl mx-auto lg:max-w-none lg:mx-0 px-4 sm:px-6 pt-4 pb-6 flex flex-col min-h-0 flex-1';

const CATEGORY_KEYS = ['streak', 'values', 'quest', 'level', 'conversation', 'special'];

const BadgesPage = () => {
  const { completedChallenges } = useQuestProgress();
  const strings = useStrings();
  const s = strings.badges;
  const [badges, setBadges] = useState([]);
  const [levelData, setLevelData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all');
  const [openId, setOpenId] = useState(null);
  const [retrySeed, setRetrySeed] = useState(0);
  const [toastPayload, setToastPayload] = useState(null);
  const closeSheet = useCallback(() => setOpenId(null), []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError('');
      try {
        const [badgesRes, levelRes] = await Promise.all([fetchBadges(), fetchLevel()]);
        if (cancelled) return;
        setBadges(
          badgesRes.map((b) => ({
            id: b.id,
            name: b.name,
            description: b.description,
            imageSrc: b.icon || null,
            category: b.category || 'special',
            requirementValue: b.requirement_value,
            progressCurrent: b.progress_current,
            earned: b.earned,
            earnedAt: b.earned_at,
          })),
        );
        // Integration note:
        // When session-end or badge-award API returns "newly earned" badges,
        // trigger setToastPayload({ name, icon }) here (or from ConversationPage)
        // so the reusable BadgeToast appears immediately.
        setLevelData(levelRes);
      } catch (err) {
        console.error('Failed to load badges/level:', err);
        if (!cancelled) {
          setError('load');
          setBadges([]);
          setLevelData(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [retrySeed]);

  // The catalog is seeded in English by the backend: show the Arabic name and hint when we have one.
  const displayBadges = badges.map((b) => {
    const local = strings.badgeCatalog[b.name];
    return local ? { ...b, name: local[0], description: local[1] } : b;
  });

  const currentLevel = levelData?.level_number ?? 1;
  const totalEarnedBadges = displayBadges.filter((b) => b.earned).length;
  const counts = { all: displayBadges.length, earned: totalEarnedBadges, locked: displayBadges.length - totalEarnedBadges };
  const visible = displayBadges.filter((b) => filter === 'all' || (filter === 'earned') === b.earned);
  const opened = displayBadges.find((b) => b.id === openId);

  if (loading) {
    return (
      <div className={SHELL}>
        <p className="mt-10 text-center text-body text-text-muted" role="status">{s.loading}</p>
      </div>
    );
  }

  return (
    <div className={SHELL}>
      <header className="mb-4 shrink-0">
        <h1 className="text-display text-text">{s.title}</h1>
      </header>

      <div className="mb-6 shrink-0">
        <AchievementStats
          completedChallenges={completedChallenges}
          currentLevel={currentLevel}
          totalEarnedBadges={totalEarnedBadges}
        />
      </div>

      {import.meta.env.DEV ? (
        <div className="mb-4 shrink-0">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setToastPayload({ name: strings.badgeCatalog['Rising Star']?.[0] ?? 'Rising Star', icon: null })}
          >
            {s.testToast}
          </Button>
        </div>
      ) : null}

      <div className="min-h-0 flex-1 overflow-y-auto pb-4">
        {error ? (
          <Card padding="lg" className="text-center">
            <p className="text-body text-text">{s.loadError}</p>
            <Button className="mt-4" onClick={() => setRetrySeed((prev) => prev + 1)}>
              {strings.common.retry}
            </Button>
          </Card>
        ) : (
        <section aria-labelledby="badges-heading">
          <h2 id="badges-heading" className="mb-2 text-title text-text">
            {s.yourBadges}
          </h2>
          <p className="mb-6 text-body text-text-muted">
            {s.intro}
          </p>
          {displayBadges.length > 0 ? (
            <>
            <SegmentedControl
              label={s.filterLabel}
              value={filter}
              onChange={setFilter}
              options={[
                { value: 'all', label: s.filter.all },
                { value: 'earned', label: s.filter.earned(counts.earned) },
                { value: 'locked', label: s.filter.locked(counts.locked) },
              ]}
              className="mb-6"
            />
            {visible.length === 0 ? <p className="text-body text-text-muted">{s.filterEmpty[filter]}</p> : null}
            <div className="space-y-8">
              {CATEGORY_KEYS.map((key) => {
                const [label, subtitle] = s.categories[key];
                const all = displayBadges.filter((b) => b.category === key);
                const items = visible.filter((b) => b.category === key);
                if (!items.length) return null;
                const earnedCount = all.filter((b) => b.earned).length;
                return (
                  <div key={key}>
                    <div className="mb-3 flex items-start justify-between gap-3">
                      <div>
                        <h3 className="text-heading text-text">{label}</h3>
                        <p className="text-label text-text-muted">{subtitle}</p>
                      </div>
                      <Pill variant={earnedCount === all.length ? 'success' : 'neutral'} className="shrink-0">
                        {s.count(earnedCount, all.length)}
                      </Pill>
                    </div>
                    <ul className="grid grid-cols-3 gap-3 sm:grid-cols-4 lg:grid-cols-5">
                      {items.map((b) => (
                        <li key={b.id}><BadgeTile badge={b} onOpen={() => setOpenId(b.id)} /></li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>
            </>
          ) : (
            <EmptyState
              icon={Medal}
              title={s.empty}
              message={s.emptyMessage}
            />
          )}
        </section>
        )}
      </div>

      {toastPayload ? (
        <BadgeToast
          badgeName={toastPayload.name}
          badgeIcon={toastPayload.icon}
          onDone={() => setToastPayload(null)}
        />
      ) : null}

      {opened ? <BadgeSheet badge={opened} onClose={closeSheet} /> : null}
    </div>
  );
};

export default BadgesPage;
