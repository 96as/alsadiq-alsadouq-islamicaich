import { Hourglass, MessageCircleHeart, X } from 'lucide-react';
import './voiceui.css';

/**
 * NoticeToast: a friendly message that sits over the chat. `kind` picks the icon:
 * 'rest' (the voice is resting, we chat by text) or 'time' (one minute left).
 * Closeable with a 56px target; a time toast closes itself (the page times it).
 */
const NoticeToast = ({ kind = 'rest', children, onClose, closeLabel, dir, lang }) => {
  const Icon = kind === 'time' ? Hourglass : MessageCircleHeart;
  return (
    <div className="vu vu-toast" dir={dir} lang={lang} role="status">
      <span className="vu-toast-icon" data-tone={kind === 'time' ? 'sun' : 'leaf'} aria-hidden="true">
        <Icon strokeWidth={2} />
      </span>
      <span className="min-w-0 flex-1">{children}</span>
      {onClose ? (
        <button type="button" className="vu-toast-close" onClick={onClose} aria-label={closeLabel}>
          <span><X strokeWidth={2.5} aria-hidden="true" /></span>
        </button>
      ) : null}
    </div>
  );
};

export default NoticeToast;
