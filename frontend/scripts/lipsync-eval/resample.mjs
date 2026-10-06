// Sample-rate conversion for the evaluation: the clips are cached at the rate ElevenLabs sent
// (22.05 kHz) but a live session hears the voice at 48 kHz (WebRTC), so the evaluation can run the
// pipeline at that rate too (eval.mjs --sr 48000). A Hann-windowed sinc, 16 zero crossings each side,
// band-limited to the lower of the two Nyquist rates. Offline only.

const HALF = 16;

export function resample(pcm, rateIn, rateOut) {
  if (rateIn === rateOut) return pcm;
  const n = Math.round((pcm.length * rateOut) / rateIn);
  const out = new Float32Array(n);
  const ratio = rateIn / rateOut;
  const cutoff = Math.min(1, rateOut / rateIn); // of the input Nyquist
  const reach = HALF / cutoff;
  for (let i = 0; i < n; i++) {
    const x = i * ratio;
    const k0 = Math.ceil(x - reach);
    const k1 = Math.floor(x + reach);
    let acc = 0;
    let norm = 0;
    for (let k = k0; k <= k1; k++) {
      const d = (x - k) * cutoff;
      const sinc = d === 0 ? 1 : Math.sin(Math.PI * d) / (Math.PI * d);
      const w = 0.5 + 0.5 * Math.cos((Math.PI * (x - k)) / reach);
      const c = sinc * w;
      norm += c;
      if (k >= 0 && k < pcm.length) acc += pcm[k] * c;
    }
    out[i] = norm ? (acc / norm) * 1 : 0;
  }
  return out;
}
