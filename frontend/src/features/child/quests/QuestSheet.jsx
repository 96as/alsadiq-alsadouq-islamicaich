import { useNavigate } from 'react-router-dom';
import { Sparkles } from 'lucide-react';
import { Button, Pill, Sheet } from '../../../components/ui';
import { ROUTES } from '../../../routes';
import { shortDate, useLang, useStrings } from '../../../i18n';
import QuestStatusBadge from './QuestStatusBadge';
import { questAction, TYPE_ICON } from './questUtils';

/** Details of one (render only when a quest is picked):  quest and the one button that fits its type: talk, ask a parent, or mark done. */
export default function QuestSheet({ quest, onClose, onComplete, isCompleting }) {
  const navigate = useNavigate();
  const lang = useLang();
  const strings = useStrings();
  const s = strings.quests;

  const TypeIcon = TYPE_ICON[quest.questType];
  const action = questAction(quest);
  const isDone = quest.status === 'completed';
  const isPending = quest.status === 'pending_verification';
  // While the request is sent the quest already reads "done", so keep the button (as "Sending…") until it settles.
  const showAction = (!isDone && !isPending) || (isCompleting && action !== 'talk');
  // Moral theme labels arrive in English: Arabic shows the translation, or nothing rather than mixed scripts.
  const rawTheme = quest.themeLabel?.trim() || '';
  const themeKey = Object.keys(strings.themes).find((k) => k.toLowerCase() === rawTheme.toLowerCase());
  const theme = themeKey ? strings.themes[themeKey] : (lang === 'ar' && /[A-Za-z]/.test(rawTheme) ? '' : rawTheme);

  const label = { talk: s.startTalk, ask: s.askParent, mark: s.markComplete }[action];

  return (
    <Sheet open onClose={onClose} title={quest.title}>
      <div className="flex flex-wrap items-center gap-2">
        <QuestStatusBadge status={quest.status} />
        {TypeIcon ? (
          <Pill icon={<TypeIcon className="size-4" aria-hidden="true" />}>{s.type[quest.questType]}</Pill>
        ) : null}
        {theme ? <Pill>{theme}</Pill> : null}
        <Pill variant="warning" icon={<Sparkles className="size-4" aria-hidden="true" />}>
          {s.points(quest.rewardPoints, lang)}
        </Pill>
      </div>

      {quest.description ? <p dir="auto" className="text-body text-text-muted">{quest.description}</p> : null}

      <p className="rounded-2xl bg-surface-alt p-3 text-label text-text">{s.howFinished[action]}</p>

      {isPending ? <p className="rounded-2xl bg-info-soft p-3 text-label text-text">{s.pendingNote}</p> : null}
      {isDone && quest.completedAt ? (
        <p className="text-label text-text-muted">{s.completedOn(shortDate(quest.completedAt, lang))}</p>
      ) : null}

      {showAction ? (
        <Button
          loading={isCompleting}
          className="w-full"
          onClick={action === 'talk' ? () => { onClose(); navigate(ROUTES.CHILD_HOME); } : () => onComplete(quest.id)}
        >
          {isCompleting ? s.sending : label}
        </Button>
      ) : null}
    </Sheet>
  );
}
