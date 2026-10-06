import { useEffect, useState } from 'react';
import { Languages, LoaderCircle, MessageCircleHeart, RotateCcw, Sparkles } from 'lucide-react';
import StatusCard from './StatusCard';
import './voiceui.css';

const SHADOW = '0 1px 3px rgba(15,45,28,0.9), 0 2px 14px rgba(15,45,28,0.7)';

/** Counts down from `seconds` to 0, once a second. */
function useCountdown(seconds) {
  const [left, setLeft] = useState(seconds);
  useEffect(() => {
    if (left <= 0) return undefined;
    const id = window.setTimeout(() => setLeft((n) => n - 1), 1000);
    return () => window.clearTimeout(id);
  }, [left]);
  return left;
}

/** The idle card: "shall we talk with Sadiq?" with the start key and the language pill. */
export const IdleCard = ({ t, onStart, onToggleLang }) => (
  <StatusCard
    mood="sparkles"
    title={t.idleTitle}
    dir={t.dir}
    lang={t.lang}
    labelledBy="vu-idle-title"
    corner={(
      <button type="button" className="vu-lang" onClick={onToggleLang} aria-label={t.langToggleLabel} lang={t.langToggleLang}>
        <span><Languages aria-hidden="true" strokeWidth={2.25} />{t.langToggle}</span>
      </button>
    )}
    actions={(
      <button type="button" className="vu-key" onClick={onStart}>
        {t.start}
      </button>
    )}
  >
    {t.idleBody}
  </StatusCard>
);

/** Starting: three bouncing dots and a calm line. */
export const StartingView = ({ t, slow }) => (
  <div className="vu text-center" dir={t.dir} lang={t.lang} role="status">
    <div className="vu-dots" aria-hidden="true"><span /><span /><span /></div>
    <p className="vu-starting mt-4">{slow ? t.startingSlow : t.starting}</p>
  </div>
);

/** A start the server refused (the daily cap, a throttle, the voice switched off) or that failed. */
export const RefusedCard = ({ t, refusal, onBack, onChat }) => {
  const wait = useCountdown(refusal.retryAfter || 0);
  const waiting = wait > 0;
  return (
    <StatusCard
      mood={refusal.mood}
      title={refusal.title}
      dir={t.dir}
      lang={t.lang}
      labelledBy="vu-refused-title"
      actions={(
        <>
          <button type="button" className="vu-key" onClick={onBack} disabled={waiting}>
            {refusal.action}
          </button>
          {onChat ? (
            <button type="button" className="vu-pill" onClick={onChat}>
              <MessageCircleHeart aria-hidden="true" strokeWidth={2.25} />
              {t.restText}
            </button>
          ) : null}
        </>
      )}
    >
      {refusal.body}
      {waiting ? <span className="mt-2 block text-[0.95rem] font-semibold">{t.retryIn(wait)}</span> : null}
    </StatusCard>
  );
};

/** A start that failed (no network, a server error). */
export const ErrorCard = ({ t, message, onRetry }) => (
  <StatusCard
    mood="hourglass"
    title={t.errorTitle}
    dir={t.dir}
    lang={t.lang}
    labelledBy="vu-error-title"
    actions={(
      <button type="button" className="vu-key" onClick={onRetry}>
        {t.tryAgain}
      </button>
    )}
  >
    {message}
  </StatusCard>
);

/**
 * "Sadiq's voice is resting" (the agent sent voice_error). Offers the text chat, unless the
 * voice was switched off for everyone (voice_off), where the only way out is to come back later.
 */
export const VoiceRestingCard = ({ t, canChat, busy, onChat, onBack }) => (
  <StatusCard
    mood="moon"
    title={t.restTitle}
    dir={t.dir}
    lang={t.lang}
    role="alertdialog"
    labelledBy="vu-rest-title"
    actions={(
      <>
        {canChat ? (
          <button type="button" className="vu-key" onClick={onChat} disabled={busy}>
            {busy ? <LoaderCircle className="animate-spin" aria-hidden="true" /> : <MessageCircleHeart aria-hidden="true" strokeWidth={2.25} />}
            {t.restText}
          </button>
        ) : null}
        <button type="button" className={canChat ? 'vu-pill' : 'vu-key'} onClick={onBack} disabled={busy}>
          {t.restBack}
        </button>
      </>
    )}
  >
    {canChat ? t.restBody : t.restOffBody}
  </StatusCard>
);

/** The warm goodbye after the time limit. In a demo it offers "start over". */
export const EndCard = ({ t, demo, busy, error, onStartOver, onAgain }) => (
  <StatusCard
    mood="wave"
    title={t.endTitle}
    dir={t.dir}
    lang={t.lang}
    confetti
    labelledBy="vu-end-title"
    actions={(
      <>
        {demo ? (
          <button type="button" className="vu-key" onClick={onStartOver} disabled={busy}>
            {busy ? <LoaderCircle className="animate-spin" aria-hidden="true" /> : <RotateCcw aria-hidden="true" strokeWidth={2.5} />}
            {busy ? t.working : t.endStartOver}
          </button>
        ) : (
          <button type="button" className="vu-key" onClick={onAgain}>
            <Sparkles aria-hidden="true" strokeWidth={2.5} />
            {t.endAgain}
          </button>
        )}
        {demo ? (
          <button type="button" className="vu-pill" onClick={onAgain} disabled={busy}>
            {t.endAgain}
          </button>
        ) : null}
        {error ? <p role="alert" className="text-sm font-semibold">{error}</p> : null}
      </>
    )}
  >
    {t.endBody}
  </StatusCard>
);

/** The empty text chat: a friendly line and three things to tap. */
export const TextChatEmpty = ({ t, onPick }) => (
  <section className="vu flex min-h-0 flex-1 flex-col items-center justify-center gap-4 overflow-y-auto px-5 py-4" dir={t.dir} lang={t.lang}>
    {/* qa: the chat panel is a light card now, so the old white-on-dark text was 2:1; dark green is 12:1 */}
    <p className="text-center text-lg font-bold text-[#17351f]">{t.chatEmpty}</p>
    <p className="text-center text-base font-semibold text-[#2f4f3a]">{t.ideasTitle}</p>
    <div className="vu-ideas">
      {t.ideas.map((idea, i) => (
        <button key={idea} type="button" className="vu-idea vu-rise" style={{ '--i': i }} onClick={() => onPick(idea)}>
          <Sparkles aria-hidden="true" strokeWidth={2.25} />
          {idea}
        </button>
      ))}
    </div>
  </section>
);
