/**
 * What the child's app does with the guard answers (docs/hackathon/demo-guards.md):
 * the 429 and 503 start refusals, and the numbers on the session clock.
 */

const REFUSAL_CODES = ['daily_limit', 'rate_limited', 'voice_off'];

/**
 * Turn a failed POST /sessions/ into what the screen shows.
 *
 *   {kind: 'refused', code, mood, title, body, action, retryAfter}  a friendly card
 *   {kind: 'error', message}                                          a plain "could not start"
 *
 * The body is the local copy, written to sit under the card's title (the server's {ar, en}
 * message stands alone and repeats the title, e.g. "Slow down, my friend, ..."). The server's
 * words are only a fallback.
 */
export function describeStartFailure(err, t, lang) {
  const status = err?.response?.status;
  const data = err?.response?.data;
  const headers = err?.response?.headers || {};

  if (status === 429 || status === 503) {
    const code = REFUSAL_CODES.includes(data?.code)
      ? data.code
      : (status === 429 ? 'rate_limited' : 'busy');
    const local = t.refusals[code];
    const fromServer = data?.message && typeof data.message[lang] === 'string' ? data.message[lang] : '';
    const retryAfter = Number(headers['retry-after']) || (code === 'rate_limited' ? 30 : 0);
    return {
      kind: 'refused',
      code,
      mood: local.mood,
      title: local.title,
      body: local.body || fromServer,
      action: local.action,
      retryAfter: Math.min(Math.max(retryAfter, 0), 120),
    };
  }

  const combined = `${err?.message || ''} ${err?.cause || ''}`.toLowerCase();
  if (!err?.response || /couldn't connect|could not connect|connection refused|failed to fetch|websocket|networkerror|timeout/.test(combined)) {
    return { kind: 'error', message: t.connectError };
  }
  return { kind: 'error', message: t.genericError };
}

/**
 * Where the session clock ends, as a local time. It is counted from the moment the start
 * answer arrived (max_seconds), so a wrong clock on the child's device cannot shorten or
 * stretch it. session_ends_at is the fallback.
 */
export function clockEndFromStart(data, receivedAt) {
  const max = Number(data?.max_seconds);
  if (Number.isFinite(max) && max > 0) {
    return { endsAt: receivedAt + max * 1000, totalSeconds: max };
  }
  const at = data?.session_ends_at ? Date.parse(data.session_ends_at) : NaN;
  if (Number.isFinite(at) && at > receivedAt) {
    return { endsAt: at, totalSeconds: Math.round((at - receivedAt) / 1000) };
  }
  return { endsAt: null, totalSeconds: 0 };
}

/** "4:05" in Western digits, "٤:٠٥" in Arabic-Indic. Always left to right. */
export function formatClock(seconds, lang) {
  const s = Math.max(0, Math.floor(seconds));
  const m = Math.floor(s / 60);
  const rest = String(s % 60).padStart(2, '0');
  const text = `${m}:${rest}`;
  if (lang !== 'ar') return text;
  return text.replace(/\d/g, (d) => String.fromCharCode(0x0660 + Number(d)));
}

export const ONE_MINUTE = 60;
export const ENDING_SECONDS = 20;
