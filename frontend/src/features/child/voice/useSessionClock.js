import { useEffect, useState } from 'react';
import { ENDING_SECONDS, ONE_MINUTE } from './voiceGuards';

/**
 * The session clock. phase: 'run' | 'warn' (last minute) | 'ending' (goodbye time) | 'over'.
 *
 * endsAt is a local time (see clockEndFromStart). The agent's own "session_ending" message
 * wins over it: it says exactly how many seconds are left, on the server's clock.
 *
 * Passing the end does not mean the chat is over: the goodbye is still being said. 'over'
 * only means the time is up; the screen waits for the agent's session_ended or the room
 * closing (see ConversationPage).
 */
export default function useSessionClock({ endsAt, signal }) {
  const [now, setNow] = useState(() => Date.now());

  const active = Boolean(endsAt) || signal?.phase === 'ending';
  useEffect(() => {
    if (!active) return undefined;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [active]);

  if (!active) return { active: false, secondsLeft: null, phase: 'run' };

  let end = endsAt;
  if (signal?.phase === 'ending' && Number.isFinite(signal.secondsLeft)) {
    end = signal.at + signal.secondsLeft * 1000;
  }
  const secondsLeft = Math.max(0, Math.ceil((end - now) / 1000));

  let phase = 'run';
  if (signal?.phase === 'ended' || secondsLeft <= 0) phase = 'over';
  else if (signal?.phase === 'ending' || secondsLeft <= ENDING_SECONDS) phase = 'ending';
  else if (secondsLeft <= ONE_MINUTE) phase = 'warn';
  return { active: true, secondsLeft, phase };
}
