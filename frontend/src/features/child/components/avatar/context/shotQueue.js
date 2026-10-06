// One-shot priorities, the single pending slot, TTLs and cooldowns (SPEC-EXPERIENCE 5.6).
// Pure and allocation-free after construction.

export function createShotQueue(cfg) {
  const prio = cfg.priority;
  const priorityOf = (name) => prio[name] ?? 0;
  const cooldownUntil = { Happy: 0, Celebrate: 0 };
  const state = {
    cur: '', // the logical name playing now: Goodbye | search | Celebrate | Greet | Happy | LookAround | other
    curUntil: 0,
    curInterruptible: false,
    pend: '',
    pendExpires: 0,
    pendClip: '', // the clip the pending request will play
  };

  return {
    state,
    priorityOf,
    /** Is something (any kind) playing at time t? */
    busy: (t) => state.cur !== '' && t < state.curUntil,
    playing: (t) => (state.cur !== '' && t < state.curUntil ? state.cur : ''),
    /** Called every step: forget a one-shot that has ended. */
    update(t) {
      if (state.cur !== '' && t >= state.curUntil) state.cur = '';
    },
    /** Ask for a one-shot. Returns false if it is refused (cooldown). */
    request(name, t) {
      const cd = cooldownUntil[name];
      if (cd !== undefined && t < cd) return false;
      if (state.pend !== '' && priorityOf(name) < priorityOf(state.pend)) return false;
      state.pend = name;
      state.pendExpires = t + (cfg.ttl[name] ?? 0.5);
      return true;
    },
    clearPending(name) {
      if (state.pend === name) state.pend = '';
    },
    /**
     * The search sequence plays atomically. An interruptible one-shot gives way to it.
     * Returns 1 when it cut something, else 0.
     */
    playSearch(dur, t) {
      let cut = 0;
      if (state.cur !== '' && t < state.curUntil && state.curInterruptible) cut = 1;
      state.cur = 'search';
      state.curUntil = t + dur;
      state.curInterruptible = false;
      return cut;
    },
    /**
     * Decide the pending request. `env.speaking`: Happy waits for a quiet moment. `env.holoActive`:
     * nothing but the search plays while the hologram is open.
     * Returns '' (nothing to start), or the name to start; `cut` is set when it interrupts.
     */
    take(t, env, out) {
      out.cut = false;
      const p = state.pend;
      if (p === '') return '';
      if (t > state.pendExpires) {
        state.pend = '';
        return '';
      }
      if (env.holoActive) return '';
      if (p === 'Happy' && env.speaking) return '';
      if (state.cur !== '' && t < state.curUntil) {
        if (!(state.curInterruptible && priorityOf(p) > priorityOf(state.cur))) return '';
        out.cut = true;
      }
      state.pend = '';
      return p;
    },
    /** The one-shot `name` started playing now for `dur` seconds. */
    begin(name, dur, t, interruptible) {
      state.cur = name;
      state.curUntil = t + dur;
      state.curInterruptible = interruptible;
      const cd = cfg.cooldown[name];
      if (cd !== undefined && cooldownUntil[name] !== undefined) cooldownUntil[name] = t + cd;
    },
    /** A cut one-shot is over now. */
    cut() {
      state.cur = '';
    },
    reset() {
      state.cur = '';
      state.pend = '';
      cooldownUntil.Happy = 0;
      cooldownUntil.Celebrate = 0;
    },
  };
}
