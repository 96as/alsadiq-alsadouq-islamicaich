// Dev only (06-avatar-context): the buttons for useSignalSimulator. Plain inline styles so it drops into
// both preview pages. Collapsed with the "signals" button; ?sim=0 hides it (clean screenshots/video).
import { useState } from 'react';
import { SIM_KINDS, SIM_LISTEN, SIM_TALK } from './useSignalSimulator.js';

const btn = (on) => ({
  padding: '5px 9px',
  border: '1px solid #5b6b8c',
  borderRadius: 6,
  cursor: 'pointer',
  font: '12px system-ui, sans-serif',
  background: on ? '#2a3a5c' : '#fff',
  color: on ? '#fff' : '#111',
});
const row = { display: 'flex', flexWrap: 'wrap', gap: 5, alignItems: 'center', marginBottom: 6 };
const label = { font: '600 11px system-ui, sans-serif', color: '#dfe7f7', minWidth: 54 };

const SAMPLE_LINES = [
  ['salam', 'As-salamu alaykum, my friend! Ready to learn?'],
  ['question', 'What do you think happens next?'],
  ['bye', 'Goodbye, see you tomorrow!'],
];

export default function SignalSimulatorPanel({ sim, lang, tier, onTier }) {
  const [open, setOpen] = useState(true);
  const [kind, setKind] = useState('library');
  const [delay, setDelay] = useState(3500);
  const [listenStyle, setListenStyle] = useState('neutral');
  const [talkStyle, setTalkStyle] = useState('explain');
  const [childOn, setChildOn] = useState(false);

  return (
    <div
      data-sim-panel=""
      style={{
        position: 'fixed',
        left: 10,
        bottom: 30,
        zIndex: 20,
        maxWidth: 'min(560px, calc(100vw - 20px))',
        background: 'rgba(14,20,38,0.82)',
        borderRadius: 10,
        padding: 8,
        backdropFilter: 'blur(6px)',
      }}
    >
      <button data-sim-toggle="" style={btn(open)} onClick={() => setOpen((v) => !v)}>
        signals {open ? '▾' : '▸'}
      </button>
      {open ? (
        <div style={{ marginTop: 8 }}>
          <div style={row}>
            <span style={label}>listen</span>
            {SIM_LISTEN.map((s) => (
              <button
                key={s}
                data-listen={s}
                style={btn(listenStyle === s)}
                onClick={() => {
                  setListenStyle(s);
                  sim.listen(s);
                }}
              >
                {s}
              </button>
            ))}
            <button data-child="" style={btn(childOn)} onClick={() => { sim.child(!childOn); setChildOn(!childOn); }}>
              child speaking
            </button>
          </div>
          <div style={row}>
            <span style={label}>talk</span>
            {SIM_TALK.map((s) => (
              <button
                key={s}
                data-talk={s}
                style={btn(talkStyle === s)}
                onClick={() => {
                  setTalkStyle(s);
                  sim.talk(s);
                }}
              >
                {s}
              </button>
            ))}
          </div>
          <div style={row}>
            <span style={label}>search</span>
            {SIM_KINDS.map((k) => (
              <button key={k} data-kind={k} style={btn(kind === k)} onClick={() => setKind(k)}>
                {k}
              </button>
            ))}
            <button data-search-found="" style={btn(false)} onClick={() => sim.search(kind, 'found', delay)}>
              search, found
            </button>
            <button data-search-none="" style={btn(false)} onClick={() => sim.search(kind, 'none', delay)}>
              search, none
            </button>
            <button data-search-interrupt="" style={btn(false)} onClick={() => sim.interrupt()}>
              interrupt
            </button>
          </div>
          <div style={row}>
            <span style={label}>web page</span>
            {[
              ['sky', 'found', 'sky'],
              ['bees', 'found', 'bees'],
              ['sky', 'none', 'none'],
              ['sky', 'grownup', 'grown-up'],
              ['sky', 'meta', 'meta word'],
            ].map(([name, outcome, text]) => (
              <button
                key={`${name}-${outcome}`}
                data-web={`${name}-${outcome}`}
                style={btn(false)}
                onClick={() => sim.searchWeb(name, { outcome, lang })}
                title="fixture text only"
              >
                {text}
              </button>
            ))}
          </div>
          <div style={row}>
            <span style={label}>delay</span>
            <input
              data-delay=""
              type="range"
              min="800"
              max="9000"
              step="100"
              value={delay}
              onChange={(e) => setDelay(Number(e.target.value))}
            />
            <span style={{ ...label, minWidth: 0 }}>{(delay / 1000).toFixed(1)} s</span>
          </div>
          <div style={row}>
            <span style={label}>events</span>
            <button data-gam="happy" style={btn(false)} onClick={() => sim.gam('happy')}>
              points
            </button>
            <button data-gam="celebrate" style={btn(false)} onClick={() => sim.gam('celebrate')}>
              celebrate
            </button>
            <button data-limit="" style={btn(false)} onClick={() => sim.limit()}>
              session ending
            </button>
            {SAMPLE_LINES.map(([name, text]) => (
              <button key={name} data-say={name} style={btn(false)} onClick={() => sim.say(text)}>
                say: {name}
              </button>
            ))}
          </div>
          <div style={row}>
            <span style={label}>session</span>
            <button data-lang="" style={btn(lang === 'ar')} onClick={() => sim.lang(lang === 'ar' ? 'en' : 'ar')}>
              lang: {lang}
            </button>
            {onTier ? (
              <button data-tier="" style={btn(tier === 'low')} onClick={() => onTier(tier === 'low' ? 'high' : 'low')}>
                tier: {tier}
              </button>
            ) : null}
            <button data-sim-reconnect="" style={btn(false)} onClick={() => { sim.disconnect(); sim.connect(); }}>
              reconnect
            </button>
            <button data-sim-reset="" style={btn(false)} onClick={() => sim.reset()}>
              reset
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
