import { useCallback, useMemo, useState } from 'react';
import { Compass } from 'lucide-react';
import { Card, EmptyState, ProgressBar, SegmentedControl } from '../../components/ui';
import QuestRow from '../../features/child/quests/QuestRow';
import QuestSheet from '../../features/child/quests/QuestSheet';
import { partitionCurrentAndCompleted, isWaiting } from '../../features/child/quests/questUtils';
import { useQuestProgress } from '../../features/child/quests/QuestProgressContext';
import { useStrings } from '../../i18n'; // i18n // cards-spec (05)

const SHELL =
  'w-full max-w-3xl mx-auto lg:max-w-none lg:mx-0 px-4 sm:px-6 pt-4 pb-6 flex flex-col min-h-0 flex-1';

export default function QuestsPage() {
  const { quests, markQuestComplete, loading, completingQuestIds } = useQuestProgress();
  const s = useStrings().quests;
  const [filter, setFilter] = useState('todo');
  const [openId, setOpenId] = useState(null);
  const closeSheet = useCallback(() => setOpenId(null), []);

  const groups = useMemo(() => {
    const { current, completed } = partitionCurrentAndCompleted(quests);
    return {
      todo: current.filter((q) => !isWaiting(q)),
      waiting: current.filter(isWaiting),
      done: completed,
    };
  }, [quests]);

  const totalPointsAvailable = quests.reduce((sum, q) => sum + q.rewardPoints, 0);
  const completedPoints = groups.done.reduce((sum, q) => sum + q.rewardPoints, 0);
  const progressPct = totalPointsAvailable > 0
    ? Math.round((completedPoints / totalPointsAvailable) * 100)
    : 0;

  // A refetch after completing keeps the list (and an open sheet) on screen; only the first load shows the loading line.
  if (loading && quests.length === 0) {
    return (
      <div className={SHELL}>
        <p className="mt-10 text-center text-body text-text-muted" role="status">{s.loading}</p>
      </div>
    );
  }

  const shown = groups[filter];
  const opened = quests.find((q) => q.id === openId);

  return (
    <div className={SHELL}>
      <header className="mb-4 shrink-0">
        <h1 className="text-display text-text">{s.title}</h1>
        <p className="mt-2 text-body text-text-muted">
          {s.intro}
        </p>
        {quests.length > 0 ? (
          <Card className="mt-4">
            <div className="flex items-baseline justify-between gap-3">
              <p className="text-heading text-text">{s.progressTitle}</p>
              <p className="text-label text-text-muted">
                {s.progress(completedPoints, totalPointsAvailable)}
              </p>
            </div>
            <ProgressBar progress={progressPct} label={s.progressLabel} className="mt-3" />
          </Card>
        ) : null}
      </header>

      {quests.length === 0 ? (
        <EmptyState icon={Compass} title={s.emptyTitle} message={s.emptyMessage} />
      ) : (
        <>
          <SegmentedControl
            label={s.filterLabel}
            value={filter}
            onChange={setFilter}
            options={['todo', 'waiting', 'done'].map((k) => ({ value: k, label: s.filter[k](groups[k].length) }))}
            className="mb-4 shrink-0"
          />
          <div className="min-h-0 flex-1 overflow-y-auto pb-4">
            {shown.length > 0 ? (
              <ul className="space-y-3">
                {shown.map((q) => (
                  <li key={q.id}><QuestRow quest={q} onOpen={() => setOpenId(q.id)} /></li>
                ))}
              </ul>
            ) : (
              <p className="text-body text-text-muted">{s.filterEmpty[filter]}</p>
            )}
          </div>
        </>
      )}

      {opened ? (
        <QuestSheet
          quest={opened}
          onClose={closeSheet}
          onComplete={markQuestComplete}
          isCompleting={completingQuestIds.includes(opened.id)}
        />
      ) : null}
    </div>
  );
}
