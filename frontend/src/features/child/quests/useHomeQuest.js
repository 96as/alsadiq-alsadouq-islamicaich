import { useEffect, useState } from 'react';
import { fetchQuests } from '../../../services/gamificationService';
import { mapQuests } from './QuestProgressContext';
import { partitionCurrentAndCompleted } from './questUtils';

/**
 * The quest the Home card should show: the first one the child can still act on, in the Quests page order
 * (in progress before not started; one already waiting for a parent is skipped). Null while loading, on a
 * failure, or when there is nothing to do, and the card then keeps its generic wording.
 *
 * Home sits outside the QuestProgressProvider (it should not mount the whole quest list), so this
 * reads the list once on its own.
 */
export default function useHomeQuest() {
  const [quest, setQuest] = useState(null);

  useEffect(() => {
    let cancelled = false;
    fetchQuests()
      .then((data) => {
        if (cancelled) return;
        const { current } = partitionCurrentAndCompleted(mapQuests(data));
        const open = current.find((q) => q.status !== 'pending_verification') || null;
        setQuest(open ? { id: open.id, title: open.title, status: open.status } : null);
      })
      .catch(() => {
        if (!cancelled) setQuest(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return quest;
}
