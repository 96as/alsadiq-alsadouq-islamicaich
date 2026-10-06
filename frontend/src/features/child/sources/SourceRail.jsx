import { useEffect, useRef } from 'react';
import { BookOpen, History, X } from 'lucide-react';
import SourceCard from './SourceCard';
import { SOURCE_LABELS } from './sourceLabels'; // cards-spec (05)
import { FOCUS_RING } from '../../../components/ui/cx';
import { num } from '../../../i18n';

const AUTO_DISMISS_MS = 30000; // hk-14: how long a card stays when the child does nothing
const TICK_MS = 250;
// A re-sent card arrives as a new object: keying by object gives it a fresh mount, so its 30 s start again.
const cardKeys = new WeakMap();
let nextCardKey = 0;
const keyOf = (card) => {
  if (!cardKeys.has(card)) cardKeys.set(card, `${card.id}:${nextCardKey += 1}`);
  return cardKeys.get(card);
};

/**
 * One card with its close button and the auto-dismiss timer. The timer pauses (does not restart) while the pointer
 * is over the card, focus is inside it, or a recitation <audio> in it is playing. `audio` events do not bubble, so
 * they are listened to in the capture phase on the wrapper. One interval per card; the bar is written through a ref
 * so a tick never re-renders the card (it steps every 250 ms and has no CSS transition under reduced motion).
 */
function RailCard({ card, lang, L, autoDismiss, onClose }) {
  const wrapRef = useRef(null);
  const barRef = useRef(null);
  const pausedRef = useRef({ hover: false, focus: false, audio: false });
  const onCloseRef = useRef(onClose);
  useEffect(() => { onCloseRef.current = onClose; });

  useEffect(() => {
    if (!autoDismiss) return undefined;
    const wrap = wrapRef.current;
    const flags = pausedRef.current;
    const syncAudio = () => { flags.audio = [...wrap.querySelectorAll('audio')].some((a) => !a.paused && !a.ended); };
    const mediaEvents = ['play', 'playing', 'pause', 'ended', 'emptied', 'error', 'abort'];
    mediaEvents.forEach((e) => wrap.addEventListener(e, syncAudio, true));
    const over = () => { flags.hover = true; };
    const out = () => { flags.hover = false; };
    const focusIn = () => { flags.focus = true; };
    const focusOut = (e) => { flags.focus = wrap.contains(e.relatedTarget); };
    wrap.addEventListener('pointerenter', over);
    wrap.addEventListener('pointerleave', out);
    wrap.addEventListener('focusin', focusIn);
    wrap.addEventListener('focusout', focusOut);
    let left = AUTO_DISMISS_MS;
    const id = window.setInterval(() => {
      if (flags.hover || flags.focus || flags.audio) return;
      left -= TICK_MS;
      if (barRef.current) barRef.current.style.width = `${Math.max(0, (left / AUTO_DISMISS_MS) * 100)}%`;
      if (left <= 0) {
        window.clearInterval(id);
        onCloseRef.current();
      }
    }, TICK_MS);
    return () => {
      window.clearInterval(id);
      mediaEvents.forEach((e) => wrap.removeEventListener(e, syncAudio, true));
      wrap.removeEventListener('pointerenter', over);
      wrap.removeEventListener('pointerleave', out);
      wrap.removeEventListener('focusin', focusIn);
      wrap.removeEventListener('focusout', focusOut);
    };
  }, [autoDismiss]);

  return (
    <div ref={wrapRef} className="relative shrink-0">
      {/* The header row of the card keeps clear of the close button (56px target, 32px circle). */}
      <div className="[&>article>div:first-child]:min-h-14 [&>article>div:first-child]:pe-14">
        <SourceCard card={card} lang={lang} />
      </div>
      <button
        type="button"
        aria-label={L.closeCard}
        title={L.closeCard}
        onClick={() => {
          // Focus goes to the "Sources this session" chip (never into another card, which would pause its timer).
          const aside = wrapRef.current?.closest('aside');
          onClose();
          requestAnimationFrame(() => aside?.querySelector('[data-sources-chip]')?.focus());
        }}
        className={`absolute end-0 top-0 inline-flex size-14 cursor-pointer items-center justify-center ${FOCUS_RING}`}
      >
        <span className="flex size-8 items-center justify-center rounded-full bg-surface-alt text-text">
          <X aria-hidden="true" className="size-5" />
        </span>
      </button>
      {autoDismiss ? (
        <div aria-hidden="true" className="absolute inset-x-5 bottom-1.5 h-1 overflow-hidden rounded-full bg-surface-alt">
          <div ref={barRef} className="h-full w-full bg-accent motion-safe:transition-[width] motion-safe:duration-200 motion-safe:ease-linear" />
        </div>
      ) : null}
    </div>
  );
}

/**
 * SourceRail, the live region holding the session's source cards (newest first, max 3 visible; the child can reopen
 * the rest from the "Sources this session" chip). Placement is decided by the parent: beside the avatar on lg+, under
 * the chat on phones. The aside is always rendered (at every width) so screen readers announce new cards; only the
 * empty placeholder is hidden visually below lg. Dismissals are not announced (aria-relevant: additions).
 *
 * @param {{ cards: object[], history?: object[], pinned?: string[], onDismiss?: (id: string) => void,
 *   onReopen?: () => void, bare?: boolean, lang?: 'ar'|'en' }} props
 */
export default function SourceRail({ cards, history = cards, pinned = [], onDismiss, onReopen, bare = false, lang = 'en' }) { // avatar-integ: bare = no empty placeholder (the call screen on the meadow); cards-spec (05): lang
  const L = SOURCE_LABELS[lang === 'ar' ? 'ar' : 'en']; // cards-spec (05)
  const empty = cards.length === 0;
  const noHistory = history.length === 0;
  const hiddenSome = history.length > cards.length; // the chip shows only when it has something to bring back
  if (bare && empty && noHistory) return <aside aria-label={L.sources} aria-live="polite" className="sr-only" />;
  return (
    <aside
      aria-label={L.sources}
      aria-live="polite"
      aria-relevant="additions"
      className={`flex min-h-0 flex-col gap-3 overflow-y-auto overscroll-contain ${
        empty && noHistory ? '' : 'max-h-[35dvh] lg:max-h-none'
      } lg:h-full lg:w-[22rem] lg:shrink-0`}
    >
      {empty && noHistory ? (
        <div className="sr-only lg:not-sr-only lg:flex lg:flex-1 lg:flex-col lg:items-center lg:justify-center lg:gap-2 lg:rounded-3xl lg:border lg:border-dashed lg:border-border lg:p-6 lg:text-center">
          <BookOpen aria-hidden="true" className="size-8 text-text-muted" />
          <p className="text-body text-text-muted">
            {L.sourcesEmpty}
          </p>
        </div>
      ) : (
        cards.map((card) => (
          <RailCard
            key={keyOf(card)}
            card={card}
            lang={lang}
            L={L}
            autoDismiss={!pinned.includes(card.id)}
            onClose={() => onDismiss?.(card.id)}
          />
        ))
      )}
      {hiddenSome && onReopen ? (
        <button
          type="button"
          onClick={onReopen}
          data-sources-chip=""
          className={`text-label inline-flex min-h-target shrink-0 cursor-pointer items-center justify-center gap-2 self-start rounded-full bg-surface px-4 text-text shadow-[0_4px_16px_var(--color-shadow)] ${FOCUS_RING}`}
        >
          <History aria-hidden="true" className="size-5" />
          {L.sessionSources.replace('{n}', num(history.length, lang))}
        </button>
      ) : null}
    </aside>
  );
}
