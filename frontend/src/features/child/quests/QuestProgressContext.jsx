/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { fetchQuests, completeQuest } from '../../../services/gamificationService';

const QuestProgressContext = createContext(null);

export function mapQuests(data) { // i18n // cards-spec (05): exported for the Home quest card
  return data.map((q) => ({
    id: q.id,
    questId: q.quest_id,
    title: q.title,
    description: q.description,
    rewardPoints: q.reward_points,
    themeLabel: q.moral_theme_name,
    status: q.status,
    questType: q.quest_type,
    verificationMethod: q.verification_method,
    proofNote: q.proof_note,
    verifiedBy: q.verified_by,
    startedAt: q.started_at,
    completedAt: q.completed_at,
    isAiGenerated: q.is_ai_generated,
  }));
}

export function QuestProgressProvider({ children }) {
  const [quests, setQuests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [completingQuestIds, setCompletingQuestIds] = useState([]);

  const loadQuests = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchQuests();
      setQuests(mapQuests(data));
    } catch (err) {
      setError(err);
      setQuests([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load: state starts as loading with no error, so only set state after the fetch resolves.
  useEffect(() => {
    let cancelled = false;
    fetchQuests()
      .then((data) => {
        if (!cancelled) setQuests(mapQuests(data));
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err);
          setQuests([]);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const markQuestComplete = useCallback(
    async (progressId) => {
      const nowIso = new Date().toISOString();
      setCompletingQuestIds((prev) => (prev.includes(progressId) ? prev : [...prev, progressId]));
      setQuests((prev) =>
        prev.map((q) =>
          q.id === progressId
            ? {
                ...q,
                status: 'completed',
                completedAt: q.completedAt || nowIso,
              }
            : q,
        ),
      );
      try {
        await completeQuest(progressId);
        await loadQuests();
      } catch (err) {
        console.error('Failed to complete quest:', err);
        await loadQuests();
      } finally {
        setCompletingQuestIds((prev) => prev.filter((id) => id !== progressId));
      }
    },
    [loadQuests],
  );

  const value = useMemo(() => {
    const completedChallenges = quests.filter((q) => q.status === 'completed').length;
    return {
      quests,
      markQuestComplete,
      completedChallenges,
      loading,
      error,
      completingQuestIds,
      refetch: loadQuests,
    };
  }, [quests, markQuestComplete, loading, error, completingQuestIds, loadQuests]);

  return <QuestProgressContext.Provider value={value}>{children}</QuestProgressContext.Provider>;
}

export function useQuestProgress() {
  const ctx = useContext(QuestProgressContext);
  if (!ctx) {
    throw new Error('useQuestProgress must be used within QuestProgressProvider');
  }
  return ctx;
}
