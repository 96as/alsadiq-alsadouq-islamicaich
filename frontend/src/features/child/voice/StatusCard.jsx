import { useEffect, useRef } from 'react';
import { Hand, Hourglass, MessageCircleHeart, MoonStar, Sparkles } from 'lucide-react';
import './voiceui.css';

const MOODS = {
  moon: { Icon: MoonStar, tone: 'sun' },
  hourglass: { Icon: Hourglass, tone: 'sun' },
  chat: { Icon: MessageCircleHeart, tone: 'leaf' },
  wave: { Icon: Hand, tone: 'sun', wave: true },
  sparkles: { Icon: Sparkles, tone: 'leaf' },
};

// In the card's side padding (24px), so a sparkle never lands on a word.
const SPARKS = [
  { side: 'left', x: '9px', top: '14%', d: '0s' },
  { side: 'right', x: '10px', top: '24%', d: '0.7s' },
  { side: 'left', x: '5px', top: '54%', d: '1.3s' },
  { side: 'right', x: '5px', top: '64%', d: '0.4s' },
];

const CONFETTI_COLORS = ['#f7b929', '#86efac', '#ffffff', '#1d6b3c', '#ffd35c'];
const CONFETTI = Array.from({ length: 22 }, (_, n) => {
  const angle = (Math.PI * 2 * n) / 22 - Math.PI / 2;
  const reach = 90 + ((n * 37) % 70);
  return {
    n,
    dx: `${Math.round(Math.cos(angle) * reach * 1.5)}px`,
    dy: `${Math.round(Math.sin(angle) * reach + 40)}px`,
    rot: `${(n % 2 ? 1 : -1) * (180 + n * 20)}deg`,
    c: CONFETTI_COLORS[n % CONFETTI_COLORS.length],
  };
});

/**
 * StatusCard: one friendly card for everything that is not the chat itself (a refusal, the
 * voice resting, the goodbye). A floating badge sits on its top edge.
 *
 * Props: mood, title, children (the body), actions (buttons, passed as nodes), dir, lang,
 * confetti (the goodbye), corner (a small control in the top corner), role ('status' by default, 'alertdialog' when it sits on a scrim).
 * An alertdialog takes the focus when it opens (the button marked data-autofocus, else the
 * first one), and onEscape, when given, closes it with the Escape key.
 */
const StatusCard = ({ mood = 'moon', title, children, actions, dir, lang, confetti = false, corner = null, role = 'status', labelledBy, onEscape, className = 'mt-14' }) => {
  const { Icon, tone, wave } = MOODS[mood] || MOODS.moon;
  const cardRef = useRef(null);
  const dialog = role === 'alertdialog';
  const bodyId = labelledBy && children ? `${labelledBy}-body` : undefined;

  useEffect(() => {
    if (!dialog) return;
    const card = cardRef.current;
    const target = card?.querySelector('[data-autofocus]:not([disabled])')
      || card?.querySelector('button:not([disabled])');
    target?.focus({ preventScroll: true });
  }, [dialog]);

  const handleKeyDown = onEscape
    ? (e) => {
      if (e.key !== 'Escape') return;
      e.stopPropagation();
      onEscape();
    }
    : undefined;

  // The wrapper is only as wide as the card (21rem + padding). A full-width one centred the card
  // on desktop, right over the avatar, instead of beside it (forestPlace in ConversationPage).
  return (
    <div className={`vu w-full max-w-[23.5rem] px-5 ${className}`} dir={dir} lang={lang}>
      <div
        ref={cardRef}
        className="vu-card vu-pop"
        role={role}
        aria-labelledby={labelledBy}
        aria-describedby={dialog ? bodyId : undefined}
        aria-modal={dialog ? 'true' : undefined}
        onKeyDown={handleKeyDown}
      >
        {SPARKS.map((s) => (
          <span key={s.side + s.top} className="vu-spark" style={{ [s.side]: s.x, top: s.top, '--d': s.d }} aria-hidden="true" />
        ))}
        {corner}
        <div className="vu-badge" data-tone={tone} data-wave={wave ? 'true' : undefined} aria-hidden="true">
          <Icon strokeWidth={1.75} />
        </div>
        {confetti ? (
          <div className="vu-confetti" aria-hidden="true">
            {CONFETTI.map((c) => (
              <i key={c.n} style={{ '--n': c.n, '--dx': c.dx, '--dy': c.dy, '--rot': c.rot, '--c': c.c }} />
            ))}
          </div>
        ) : null}
        <h2 id={labelledBy} className="vu-rise" style={{ '--i': 0 }}>{title}</h2>
        {children ? <p id={bodyId} className="vu-rise" style={{ '--i': 1 }}>{children}</p> : null}
        {actions ? <div className="vu-card-actions vu-rise" style={{ '--i': 2 }}>{actions}</div> : null}
      </div>
    </div>
  );
};

export default StatusCard;
