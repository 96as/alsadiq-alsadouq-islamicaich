import { useEffect, useState } from 'react';
import { Award, Sparkles, TrendingDown, TrendingUp } from 'lucide-react';
import { COPY } from '../../demo/copy';
import { useDemoLang } from '../../../services/demoService';
import Confetti from './Confetti';
import { playFx } from './soundFx';

const TOAST_MS = 3500;

function ToastCard({ toast, onDone }) {
  const [visible, setVisible] = useState(false);
  const lang = useDemoLang();
  const tt = COPY[lang].idle.toast;
  const celebrate = toast.kind === 'levelup' || toast.kind === 'quest' || toast.delta >= 0;

  useEffect(() => {
    playFx(toast.kind === 'levelup' || toast.kind === 'quest' ? 'cheer' : toast.delta >= 0 ? 'chime' : 'tap');
  }, [toast.id, toast.kind, toast.delta]);

  useEffect(() => {
    const enter = window.setTimeout(() => setVisible(true), 10);
    const leave = window.setTimeout(() => setVisible(false), TOAST_MS);
    const done = window.setTimeout(() => onDone(toast.id), TOAST_MS + 300);
    return () => {
      window.clearTimeout(enter);
      window.clearTimeout(leave);
      window.clearTimeout(done);
    };
  }, [toast.id, onDone]);

  let icon;
  let title;
  let chip;
  if (toast.kind === 'levelup') {
    icon = <Sparkles className="size-6" strokeWidth={2} aria-hidden />;
    title = tt.level(toast.levelNumber, COPY[lang].idle.levels?.[toast.levelName] || (lang === 'en' ? toast.levelName : ''));
    chip = 'bg-accent-soft text-text';
  } else if (toast.kind === 'quest') {
    icon = <Award className="size-6" strokeWidth={2} aria-hidden />;
    title = tt.quest(toast.questTitle);
    chip = 'bg-primary-soft text-primary-strong';
  } else if (toast.delta >= 0) {
    icon = <TrendingUp className="size-6" strokeWidth={2} aria-hidden />;
    title = tt.points(toast.delta);
    chip = 'bg-primary-soft text-primary-strong';
  } else {
    icon = <TrendingDown className="size-6" strokeWidth={2} aria-hidden />;
    title = tt.lost(toast.delta);
    chip = 'bg-danger-soft text-danger-strong';
  }

  return (
    <div
      dir={COPY[lang].dir}
      className={`relative pointer-events-none w-full max-w-md rounded-3xl border border-border bg-surface px-4 py-3 text-text shadow-[0_8px_24px_var(--color-shadow)] transition-all duration-300 motion-reduce:transition-none ${
        visible ? 'translate-y-0 opacity-100' : '-translate-y-3 opacity-0'
      }`}
      role="status"
      aria-live="polite"
    >
      {celebrate && visible ? <Confetti seed={Number(toast.id) || 1} count={toast.kind === 'points' || toast.kind === undefined ? 14 : 26} /> : null}
      <div className="flex items-center gap-3">
        <div className={`grid size-11 shrink-0 place-items-center rounded-2xl ${chip}`}>
          {icon}
        </div>
        <div className="min-w-0">
          <p className="text-body truncate font-bold">{title}</p>
          {toast.subtitle ? (
            <p className="text-label truncate text-text-muted">{toast.subtitle}</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}

/**
 * Stacked realtime toasts for live gamification events during a session.
 *
 * @param {{ toasts: Array<object>, onDone: (id) => void }} props
 */
export default function GamificationToasts({ toasts, onDone }) {
  if (!toasts.length) return null;
  return (
    <div className="pointer-events-none absolute inset-x-0 top-24 z-40 flex flex-col items-center gap-2 px-6">
      {toasts.map((t) => (
        <ToastCard key={t.id} toast={t} onDone={onDone} />
      ))}
    </div>
  );
}
