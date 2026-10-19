// Speech feature extraction for the lip-sync driver. Pure functions over Float32Arrays: no DOM,
// no Web Audio, no allocation inside analyse(), so it runs the same live and in node tests.
//
// One call takes the most recent 2048 mono samples and produces:
//   rms / rmsShort   loudness over the last 21 ms and 5 ms
//   voicing          0..1, how periodic the sound is (vowels and voiced consonants are high)
//   low/mid/high/sib fractions of the spectral power in 60-700, 700-2500, 2500-4500, 4500+ Hz
//   centroid         spectral centre of gravity in Hz (about 5-7 kHz for "s", 3-4 kHz for "sh")
//   fluxSum          how much the spectrum grew since the previous call (onsets and bursts)
//   f1, f2, f3       formant estimates in Hz from a linear-prediction spectral envelope
//
// The formants are what tell the vowels apart: F1 follows how open the jaw is, F2 how far the
// tongue is forward (high F2 is a spread "ee", low F2 a rounded "oo").

import { ANALYSIS } from './lipsyncConfig.js';

const TAU = Math.PI * 2;
export const FFT_SIZE = 2048;
const HALF = FFT_SIZE / 2;
const LPC_WINDOW = 1024; // newest raw samples used for the formant fit (about 21 ms)
const SHORT_WINDOW = 256; // newest raw samples used for the burst detector (about 5 ms)
const GRID = 96; // frequencies at which the LPC envelope is evaluated
const MAX_PEAKS = 16;
const BAND_EDGES = [100, 300, 600, 1000, 1600, 2500, 4000, 6000, 10000]; // 8 log-ish bands for flux

export function createFeatures() {
  return {
    rms: 0,
    rmsShort: 0,
    voicing: 0,
    centroid: 0,
    low: 0,
    mid: 0,
    high: 0,
    sib: 0,
    fluxSum: 0,
    f1: 0,
    f2: 0,
    f3: 0,
    f1Prom: 0,
  };
}

export class FeatureExtractor {
  /** @param {number} sampleRate of the audio that analyse() will be given, in Hz */
  constructor(sampleRate) {
    this.sampleRate = sampleRate;
    this.binHz = sampleRate / FFT_SIZE;
    this.nyquist = sampleRate / 2;

    // Decimate to about 12 kHz for the LPC and the voicing search (boxcar average).
    this.decim = Math.max(1, Math.round(sampleRate / 12000));
    this.sr2 = sampleRate / this.decim;
    this.decLen = FFT_SIZE / this.decim;
    this.lpcLen = LPC_WINDOW / this.decim;
    this.order = Math.min(16, Math.round(this.sr2 / 1000) + 2);
    this.dec = new Float32Array(this.decLen);
    this.lpcBuf = new Float32Array(this.lpcLen);
    this.lpcWin = new Float32Array(this.lpcLen);
    for (let i = 0; i < this.lpcLen; i++) {
      this.lpcWin[i] = 0.54 - 0.46 * Math.cos((TAU * i) / (this.lpcLen - 1));
    }
    this.r = new Float64Array(this.order + 1);
    this.a = new Float64Array(this.order + 1);
    this.aTmp = new Float64Array(this.order + 1);
    this.minLag = Math.max(2, Math.floor(this.sr2 / 400));
    this.maxLag = Math.min(this.decLen - 2, Math.ceil(this.sr2 / 70));

    // LPC envelope grid: 150 Hz up to just under the decimated Nyquist (max 5.2 kHz).
    const top = Math.min(5200, this.sr2 * 0.45);
    this.gridHz = new Float32Array(GRID);
    this.gridCos = new Float32Array(GRID * (this.order + 1));
    this.gridSin = new Float32Array(GRID * (this.order + 1));
    for (let g = 0; g < GRID; g++) {
      const f = 150 + ((top - 150) * g) / (GRID - 1);
      this.gridHz[g] = f;
      const w = (TAU * f) / this.sr2;
      for (let k = 1; k <= this.order; k++) {
        this.gridCos[g * (this.order + 1) + k] = Math.cos(w * k);
        this.gridSin[g * (this.order + 1) + k] = Math.sin(w * k);
      }
    }
    this.lnE = new Float32Array(GRID);
    this.peakHz = new Float32Array(MAX_PEAKS);
    this.peakVal = new Float32Array(MAX_PEAKS);
    this.peakProm = new Float32Array(MAX_PEAKS);

    // FFT tables and the Blackman window.
    this.win = new Float32Array(FFT_SIZE);
    for (let i = 0; i < FFT_SIZE; i++) {
      this.win[i] =
        0.42 - 0.5 * Math.cos((TAU * i) / (FFT_SIZE - 1)) + 0.08 * Math.cos((2 * TAU * i) / (FFT_SIZE - 1));
    }
    this.cosT = new Float32Array(HALF);
    this.sinT = new Float32Array(HALF);
    for (let i = 0; i < HALF; i++) {
      this.cosT[i] = Math.cos((TAU * i) / FFT_SIZE);
      this.sinT[i] = -Math.sin((TAU * i) / FFT_SIZE);
    }
    this.rev = new Uint16Array(FFT_SIZE);
    const bits = Math.log2(FFT_SIZE);
    for (let i = 0; i < FFT_SIZE; i++) {
      let x = i;
      let y = 0;
      for (let b = 0; b < bits; b++) {
        y = (y << 1) | (x & 1);
        x >>= 1;
      }
      this.rev[i] = y;
    }
    this.re = new Float32Array(FFT_SIZE);
    this.im = new Float32Array(FFT_SIZE);
    this.power = new Float32Array(HALF);

    // Spectral band edges as bin indices.
    const bin = (hz) => Math.min(HALF - 1, Math.max(1, Math.round(hz / this.binHz)));
    this.bLow = [bin(60), bin(700)];
    this.bMid = [bin(700), bin(2500)];
    this.bHigh = [bin(2500), bin(4500)];
    this.bSib = [bin(4500), bin(Math.min(10000, this.nyquist * 0.98))];
    this.bCent = [bin(200), bin(Math.min(10000, this.nyquist * 0.98))];
    this.bandBins = BAND_EDGES.map((hz) => bin(Math.min(hz, this.nyquist * 0.98)));
    this.logBands = new Float32Array(8);
    this.prevLogBands = new Float32Array(8).fill(-20);
  }

  /** Forget the previous frame (after a gap in the audio), so the first frame is not an onset. */
  reset() {
    this.prevLogBands.fill(-20);
  }

  /**
   * @param {Float32Array} x newest samples, newest last; length must be at least FFT_SIZE
   * @param {object} out a createFeatures() object, overwritten
   */
  analyse(x, out) {
    const start = x.length - FFT_SIZE;

    // Loudness.
    let s = 0;
    for (let i = FFT_SIZE - LPC_WINDOW; i < FFT_SIZE; i++) s += x[start + i] * x[start + i];
    out.rms = Math.sqrt(s / LPC_WINDOW);
    s = 0;
    for (let i = FFT_SIZE - SHORT_WINDOW; i < FFT_SIZE; i++) s += x[start + i] * x[start + i];
    out.rmsShort = Math.sqrt(s / SHORT_WINDOW);

    if (out.rms < 1e-5) {
      out.voicing = 0;
      out.centroid = 0;
      out.low = out.mid = out.high = out.sib = 0;
      out.fluxSum = 0;
      out.f1 = out.f2 = out.f3 = out.f1Prom = 0;
      this.prevLogBands.fill(-20);
      return out;
    }

    this.spectrum(x, start, out);
    this.decimate(x, start);
    out.voicing = this.voicing();
    this.formants(x, start, out);
    return out;
  }

  fft() {
    // The caller loaded the input in bit-reversed order (see spectrum()); these are in-place butterflies.
    const { re, im, cosT, sinT } = this;
    for (let size = 2; size <= FFT_SIZE; size <<= 1) {
      const half = size >> 1;
      const step = FFT_SIZE / size;
      for (let i = 0; i < FFT_SIZE; i += size) {
        for (let j = 0, k = 0; j < half; j++, k += step) {
          const a = i + j;
          const b = a + half;
          const tr = re[b] * cosT[k] - im[b] * sinT[k];
          const ti = re[b] * sinT[k] + im[b] * cosT[k];
          re[b] = re[a] - tr;
          im[b] = im[a] - ti;
          re[a] += tr;
          im[a] += ti;
        }
      }
    }
  }

  spectrum(x, start, out) {
    const { re, im, rev, win, power } = this;
    for (let i = 0; i < FFT_SIZE; i++) {
      re[rev[i]] = x[start + i] * win[i];
      im[rev[i]] = 0;
    }
    this.fft();
    for (let k = 0; k < HALF; k++) power[k] = re[k] * re[k] + im[k] * im[k];

    const sum = (range) => {
      let t = 0;
      for (let k = range[0]; k < range[1]; k++) t += power[k];
      return t;
    };
    const low = sum(this.bLow);
    const mid = sum(this.bMid);
    const high = sum(this.bHigh);
    const sib = sum(this.bSib);
    const total = low + mid + high + sib + 1e-20;
    out.low = low / total;
    out.mid = mid / total;
    out.high = high / total;
    out.sib = sib / total;

    let num = 0;
    let den = 1e-20;
    for (let k = this.bCent[0]; k < this.bCent[1]; k++) {
      num += power[k] * k;
      den += power[k];
    }
    out.centroid = (num / den) * this.binHz;

    // Spectral flux over 8 bands, in natural-log power. Growth only.
    let flux = 0;
    for (let b = 0; b < 8; b++) {
      let e = 1e-12;
      for (let k = this.bandBins[b]; k < this.bandBins[b + 1]; k++) e += power[k];
      const l = Math.log(e);
      this.logBands[b] = l;
      const d = l - this.prevLogBands[b];
      if (d > 0) flux += d;
      this.prevLogBands[b] = l;
    }
    out.fluxSum = flux;
  }

  decimate(x, start) {
    const { dec, decim, decLen } = this;
    let mean = 0;
    for (let i = 0; i < decLen; i++) {
      let v = 0;
      const base = start + i * decim;
      for (let j = 0; j < decim; j++) v += x[base + j];
      v /= decim;
      dec[i] = v;
      mean += v;
    }
    mean /= decLen;
    for (let i = 0; i < decLen; i++) dec[i] -= mean;
  }

  /** Peak of the normalised autocorrelation over lags for 70-400 Hz pitch, bias-corrected. */
  voicing() {
    const { dec, decLen, minLag, maxLag } = this;
    let r0 = 1e-20;
    for (let i = 0; i < decLen; i++) r0 += dec[i] * dec[i];
    let best = 0;
    for (let lag = minLag; lag <= maxLag; lag++) {
      let acc = 0;
      for (let i = 0; i < decLen - lag; i++) acc += dec[i] * dec[i + lag];
      const v = acc / r0 / (1 - lag / decLen);
      if (v > best) best = v;
    }
    return best < 0 ? 0 : best > 1 ? 1 : best;
  }

  formants(x, start, out) {
    const { lpcBuf, lpcWin, lpcLen, decim, order, r, a, aTmp } = this;
    // Newest 1024 raw samples, decimated, pre-emphasised, Hamming-windowed.
    const base0 = start + FFT_SIZE - LPC_WINDOW;
    let prev = 0;
    for (let i = 0; i < lpcLen; i++) {
      let v = 0;
      const base = base0 + i * decim;
      for (let j = 0; j < decim; j++) v += x[base + j];
      v /= decim;
      lpcBuf[i] = (v - 0.95 * prev) * lpcWin[i];
      prev = v;
    }
    for (let k = 0; k <= order; k++) {
      let acc = 0;
      for (let i = 0; i < lpcLen - k; i++) acc += lpcBuf[i] * lpcBuf[i + k];
      r[k] = acc;
    }
    if (r[0] < 1e-14) {
      out.f1 = out.f2 = out.f3 = out.f1Prom = 0;
      return;
    }
    r[0] *= 1.0005; // a little white noise keeps the recursion stable
    // Levinson-Durbin.
    a.fill(0);
    a[0] = 1;
    let err = r[0];
    for (let i = 1; i <= order; i++) {
      let acc = r[i];
      for (let j = 1; j < i; j++) acc += a[j] * r[i - j];
      const k = -acc / err;
      for (let j = 1; j < i; j++) aTmp[j] = a[j] + k * a[i - j];
      for (let j = 1; j < i; j++) a[j] = aTmp[j];
      a[i] = k;
      err *= 1 - k * k;
      if (err <= 0) break;
    }

    // Envelope 1/|A|^2 on the grid, in natural log.
    const { lnE, gridCos, gridSin } = this;
    const stride = order + 1;
    for (let g = 0; g < GRID; g++) {
      let re = 1;
      let im = 0;
      const o = g * stride;
      for (let k = 1; k <= order; k++) {
        re += a[k] * gridCos[o + k];
        im -= a[k] * gridSin[o + k];
      }
      lnE[g] = -Math.log(re * re + im * im + 1e-12);
    }
    this.pickFormants(out);
  }

  pickFormants(out) {
    const { lnE, gridHz, peakHz, peakVal, peakProm } = this;
    // Local maxima with parabolic refinement, and prominence over the higher neighbouring valley.
    let n = 0;
    let valley = lnE[0];
    for (let g = 1; g < GRID - 1 && n < MAX_PEAKS; g++) {
      if (lnE[g] < valley) valley = lnE[g];
      if (lnE[g] > lnE[g - 1] && lnE[g] >= lnE[g + 1]) {
        const y0 = lnE[g - 1];
        const y1 = lnE[g];
        const y2 = lnE[g + 1];
        const denom = y0 - 2 * y1 + y2;
        const shift = denom !== 0 ? (0.5 * (y0 - y2)) / denom : 0;
        const spacing = gridHz[1] - gridHz[0];
        peakHz[n] = gridHz[g] + shift * spacing;
        peakVal[n] = y1;
        peakProm[n] = y1 - valley; // left valley for now; the right one is applied below
        n++;
        valley = lnE[g];
      }
    }
    // Right-hand valleys.
    let rightValley = lnE[GRID - 1];
    let pi = n - 1;
    for (let g = GRID - 2; g >= 1 && pi >= 0; g--) {
      if (lnE[g] < rightValley) rightValley = lnE[g];
      if (lnE[g] > lnE[g - 1] && lnE[g] >= lnE[g + 1]) {
        const right = lnE[g] - rightValley;
        if (right < peakProm[pi]) peakProm[pi] = right;
        pi--;
        rightValley = lnE[g];
      }
    }

    const minProm = ANALYSIS.peakMinProm;
    // F1: strongest peak between 200 and 1000 Hz.
    let i1 = -1;
    for (let i = 0; i < n; i++) {
      if (peakHz[i] < 200 || peakHz[i] > 1000 || peakProm[i] < minProm) continue;
      if (i1 < 0 || peakVal[i] > peakVal[i1]) i1 = i;
    }
    if (i1 < 0) {
      out.f1 = out.f2 = out.f3 = out.f1Prom = 0;
      return;
    }
    const f1 = peakHz[i1];
    out.f1 = f1;
    out.f1Prom = peakProm[i1];
    // F2: lowest real peak above F1 + 200 Hz and below 3.2 kHz. If F1 and F2 merged into one broad
    // peak, assume F2 sits a little above F1 (that is what an open "a" looks like).
    let f2 = 0;
    let f3 = 0;
    for (let i = 0; i < n; i++) {
      if (peakHz[i] < f1 + 200 || peakProm[i] < minProm) continue;
      if (f2 === 0) {
        if (peakHz[i] <= 3200) f2 = peakHz[i];
      } else if (peakHz[i] >= f2 + 300 && peakHz[i] <= 4800) {
        f3 = peakHz[i];
        break;
      }
    }
    out.f2 = f2 > 0 ? f2 : f1 * 1.35;
    out.f3 = f3;
  }
}

/**
 * Convert one frame of float samples from an AnalyserNode's byte data, for browsers whose
 * AnalyserNode has no getFloatTimeDomainData (very old Safari).
 */
export function bytesToFloat(bytes, out) {
  for (let i = 0; i < bytes.length; i++) out[i] = (bytes[i] - 128) / 128;
  return out;
}
