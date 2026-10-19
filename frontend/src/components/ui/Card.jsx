import { cx } from './cx';

const PADDING = { md: 'p-4', lg: 'p-6' };

/**
 * Surface card (mirrors mobile Card).
 * Props: as (element, 'div'), padding 'md'|'lg' (md => p-4, lg => p-6), className, children.
 */
export default function Card({ as = 'div', padding = 'md', className, children, ...rest }) {
  const Tag = as;
  return (
    <Tag
      className={cx(
        'rounded-3xl border border-border bg-surface text-text shadow-[0_4px_16px_var(--color-shadow)]',
        PADDING[padding],
        className,
      )}
      {...rest}
    >
      {children}
    </Tag>
  );
}
