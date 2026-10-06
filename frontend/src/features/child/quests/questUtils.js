import { Globe2, MessageCircleHeart, NotebookPen } from 'lucide-react';

export const TYPE_ICON = {
  conversation: MessageCircleHeart,
  real_world: Globe2,
  reflection: NotebookPen,
};

/**
 * Current = not completed; Completed = completed.
 * Sorts: current with in_progress first; completed by completedAt desc.
 */
export function partitionCurrentAndCompleted(quests) {
  const current = quests.filter((q) => q.status !== 'completed');
  const completed = quests.filter((q) => q.status === 'completed');

  const order = { pending_verification: 0, in_progress: 1, not_started: 2 };
  const sortedCurrent = [...current].sort(
    (a, b) => (order[a.status] ?? 2) - (order[b.status] ?? 2),
  );

  const sortedCompleted = [...completed].sort((a, b) => {
    const ta = a.completedAt ? new Date(a.completedAt).getTime() : 0;
    const tb = b.completedAt ? new Date(b.completedAt).getTime() : 0;
    return tb - ta;
  });

  return { current: sortedCurrent, completed: sortedCompleted };
}

/**
 * What the sheet's button does: 'talk' (Sadiq marks it), 'ask' (a parent confirms) or 'mark' (self-reported).
 * The verification method decides (the server enforces it); the type only fills in when the method is missing.
 */
export function questAction({ questType, verificationMethod }) {
  if (verificationMethod === 'companion') return 'talk';
  if (verificationMethod === 'parent') return 'ask';
  if (verificationMethod === 'self') return 'mark';
  if (questType === 'conversation') return 'talk';
  return questType === 'real_world' ? 'ask' : 'mark';
}

export const isWaiting = (q) => q.status === 'pending_verification';
