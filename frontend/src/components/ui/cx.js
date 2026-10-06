/** Join truthy class names. */
export const cx = (...parts) => parts.filter(Boolean).join(' ');

export const FOCUS_RING =
  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-strong';
