import { useEffect, useState } from 'react';

/**
 * Dev-only controls for the nature motion (mounted by /dev/forest, hidden with ?panel=0): wind strength, freeze the
 * clock, switch the gust / sway / flutter layers on and off, drop prints in the grass, and a live stats line.
 * It only writes into the runtime the scene already reads (shared uniforms, rt.freezeTime, rt.devFeet).
 */
export default function NatureDevPanel() {
  const [gain, setGain] = useState(1);
  const [frozen, setFrozen] = useState(false);
  const [mix, setMix] = useState([1, 1, 1]);
  const [feet, setFeet] = useState(false);
  const [stats, setStats] = useState('');

  const rt = () => window.__forest?.rt;

  useEffect(() => {
    const r = rt();
    if (r) r.shared.uWindGain.value = gain;
  }, [gain]);
  useEffect(() => {
    const r = rt();
    if (r) r.shared.uWindMix.value.set(mix[0], mix[1], mix[2]);
  }, [mix]);
  useEffect(() => {
    const r = rt();
    if (!r) return;
    r.freezeTime = frozen ? r.shared.uTime.value : null;
  }, [frozen]);
  useEffect(() => {
    const r = rt();
    if (!r) return;
    r.devFeet = feet
      ? [
          [-2.0, 1.0, 1],
          [-1.6, 0.2, 1],
          [-2.6, 0.2, 1],
          [-3.0, -1.0, 1],
        ]
      : null;
  }, [feet]);
  useEffect(() => {
    const id = setInterval(() => {
      const s = window.__forestStats;
      if (s) setStats(`${s.quality} | ${s.drawCalls} calls | ${(s.renderedTriangles / 1000).toFixed(0)}k tris | dpr ${s.dpr}`);
    }, 500);
    return () => clearInterval(id);
  }, []);
  useEffect(
    () => () => {
      const r = rt();
      if (!r) return;
      r.freezeTime = null;
      r.devFeet = null;
      r.shared.uWindGain.value = 1;
      r.shared.uWindMix.value.set(1, 1, 1);
    },
    [],
  );

  const chip = (on) => `rounded-lg px-3 py-1 text-xs font-semibold ${on ? 'bg-white text-slate-900' : 'bg-black/45 text-white hover:bg-black/60'}`;
  const toggleMix = (i) => setMix((m) => m.map((v, k) => (k === i ? 1 - v : v)));

  return (
    <div className="absolute right-3 top-3 z-10 flex w-64 flex-col gap-2 rounded-xl bg-black/50 p-3 text-xs text-white" data-nature-dev-panel="">
      <label className="flex items-center gap-2">
        Wind {gain.toFixed(1)}
        <input type="range" min="0" max="2.5" step="0.1" value={gain} onChange={(e) => setGain(Number(e.target.value))} className="flex-1" />
      </label>
      <div className="flex flex-wrap gap-2">
        <button type="button" className={chip(frozen)} onClick={() => setFrozen((v) => !v)}>
          {frozen ? 'Frozen' : 'Freeze time'}
        </button>
        <button type="button" className={chip(feet)} onClick={() => setFeet((v) => !v)}>
          Prints in grass
        </button>
      </div>
      <div className="flex flex-wrap gap-2" role="group" aria-label="Wind layers">
        {['gust', 'sway', 'flutter'].map((n, i) => (
          <button key={n} type="button" className={chip(mix[i] === 1)} onClick={() => toggleMix(i)}>
            {n}
          </button>
        ))}
      </div>
      <p className="font-mono text-[11px] opacity-80">{stats}</p>
    </div>
  );
}
