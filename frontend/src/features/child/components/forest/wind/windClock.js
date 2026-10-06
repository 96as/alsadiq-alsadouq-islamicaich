// One wind clock for the painted meadow's layers (MeadowLife, the foreground strip), so a gust that crosses the
// painting is the same gust that crosses the grass in front of the avatar. The forest has its own clock
// (rt.shared.uTime) and passes it to the strip instead.

const T0 = typeof performance !== 'undefined' ? performance.now() : 0;

/** Seconds since the module loaded. */
export function windNow(now = performance.now()) {
  return (now - T0) / 1000;
}
