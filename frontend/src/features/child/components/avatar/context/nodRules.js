// When Sadiq nods (SPEC-EXPERIENCE 5.4 and 5.5). Pure, allocation-free, seeded rng in tests.
//   listening: after the child has spoken for a while and pauses, a nod with some probability
//   speaking:  an emphasis nod on a voice onset
// Both obey a minimum gap and a per-minute cap shared with each other.

const between = (range, rng) => range[0] + rng() * (range[1] - range[0]);

export function createNodder({ rng = Math.random, cfg }) {
  const N = cfg;
  const E = cfg.emphasis;
  const times = new Float64Array(16).fill(-1e9); // start times of recent nods (ring)
  let count = 0;
  let lastT = -999;
  let run = 0; // seconds of child speech
  let armed = false; // the child just stopped after a long enough run
  let pauseT = 0;
  let wasSpeaking = false;
  let lowT = 0; // seconds the voice has been quiet
  let secondAt = -1;
  let secondAmp = 0;
  let secondScale = 1;
  const state = { total: 0 };

  function perMinuteOk(t) {
    let n = 0;
    for (let i = 0; i < times.length; i++) if (t - times[i] < 60) n++;
    return n < N.perMinute;
  }
  function record(t) {
    times[count % times.length] = t;
    count += 1;
    lastT = t;
    state.total += 1;
  }

  function fire(t, weight, scale, out, allowDouble) {
    out.nod = weight;
    out.nodScale = scale;
    record(t);
    if (allowDouble && rng() < N.double) {
      secondAt = t + N.doubleDelay;
      secondAmp = weight * N.doubleAmp;
      secondScale = scale;
    }
  }

  return {
    state,
    /**
     * @param {number} dt
     * @param {number} t director clock
     * @param {{childSpeaking: boolean, listening: boolean, speaking: boolean, blocked: boolean,
     *   mood: string, talkStyle: string, voice: number, reduced: boolean}} env
     *   mood: 'empathy' | 'excited' | ''. voice: level normalised by its peak, or -1 when unknown.
     * @param {{nod: number, nodScale: number}} out nod is the weight to play this frame (0: none)
     */
    update(dt, t, env, out) {
      out.nod = 0;
      out.nodScale = 1;
      const amp = env.reduced ? N.reducedAmp : 1;

      // A double nod's second dip.
      if (secondAt >= 0 && t >= secondAt) {
        if (!env.blocked) {
          out.nod = secondAmp * amp;
          out.nodScale = secondScale;
        }
        secondAt = -1;
      }

      if (env.listening) {
        if (env.childSpeaking) {
          run += dt;
          armed = false;
        } else {
          if (wasSpeaking && run >= N.minSpeech) {
            armed = true;
            pauseT = 0;
          } else if (wasSpeaking) run = 0;
          if (armed) {
            pauseT += dt;
            if (pauseT >= N.minPause) {
              armed = false;
              run = 0;
              if (
                !env.blocked &&
                out.nod === 0 &&
                t - lastT >= N.minGap &&
                perMinuteOk(t) &&
                rng() < N.prob
              ) {
                let w;
                let s;
                if (env.mood === 'empathy') {
                  w = between(N.empathyWeight, rng);
                  s = N.empathyScale;
                } else if (env.mood === 'excited') {
                  w = between(N.excitedWeight, rng);
                  s = between(N.scale, rng);
                } else {
                  w = between(N.weight, rng);
                  s = between(N.scale, rng);
                }
                fire(t, w * amp, s, out, true);
              }
            }
          }
        }
        wasSpeaking = env.childSpeaking;
      } else {
        run = 0;
        armed = false;
        wasSpeaking = false;
      }

      // Emphasis nods while he speaks: a voice onset after a quiet moment.
      if (E.enabled !== false && env.speaking && env.voice >= 0) {
        if (env.voice < E.low) lowT += dt;
        else if (env.voice > E.high) {
          const onset = lowT >= E.lowFor;
          lowT = 0;
          if (onset && !env.blocked && out.nod === 0 && t - lastT >= E.minGap && perMinuteOk(t) && rng() < E.prob) {
            const w = E.byStyle[env.talkStyle] ?? between(E.weight, rng);
            fire(t, w * amp, between(N.scale, rng), out, false);
          }
        }
      } else lowT = 0;
    },
    reset() {
      run = 0;
      armed = false;
      lowT = 0;
      secondAt = -1;
      wasSpeaking = false;
    },
  };
}
