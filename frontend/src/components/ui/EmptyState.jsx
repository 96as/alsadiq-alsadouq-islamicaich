import { Leaf } from 'lucide-react';
import { cx } from './cx';

/**
 * Empty state (mirrors mobile EmptyState).
 * Props: icon (lucide component, Leaf), title, message, action (node, e.g. <Button size="sm">), className.
 */
export default function EmptyState({ icon = Leaf, title, message, action = null, className }) {
  const Icon = icon;
  return (
    <div className={cx('flex flex-col items-center gap-3 p-8 text-center', className)}>
      <div className="flex size-18 items-center justify-center rounded-4xl bg-primary-soft text-primary-strong">
        <Icon aria-hidden="true" className="size-8" />
      </div>
      {title ? <h2 className="text-heading text-text">{title}</h2> : null}
      {message ? <p className="text-body text-text-muted">{message}</p> : null}
      {action}
    </div>
  );
}
