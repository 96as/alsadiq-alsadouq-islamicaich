import { CheckCircle2, Clock, Hourglass, Circle } from 'lucide-react';
import { Pill } from '../../../components/ui';
import { useStrings } from '../../../i18n'; // i18n // cards-spec (05)

const META = {
  not_started: { variant: 'neutral', Icon: Circle },
  in_progress: { variant: 'warning', Icon: Clock },
  pending_verification: { variant: 'info', Icon: Hourglass },
  completed: { variant: 'success', Icon: CheckCircle2 },
};

/**
 * @param {{ status: 'not_started' | 'in_progress' | 'pending_verification' | 'completed' }} props
 */
export default function QuestStatusBadge({ status }) {
  const s = useStrings().quests.status;
  const key = META[status] ? status : 'not_started';
  const { variant, Icon } = META[key];
  return (
    <Pill variant={variant} icon={<Icon className="size-4" aria-hidden="true" />}>
      {s[key]}
    </Pill>
  );
}
