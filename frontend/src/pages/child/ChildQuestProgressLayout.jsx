import { Outlet } from 'react-router-dom';
import { QuestProgressProvider } from '../../features/child/quests/QuestProgressContext';

/**
 * Wraps only routes that need shared quest state (quests list + completed count).
 * Keeps Conversation / Settings from mounting quest fetch logic.
 */
export default function ChildQuestProgressLayout() {
  return (
    <QuestProgressProvider>
      <Outlet />
    </QuestProgressProvider>
  );
}
