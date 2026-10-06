// URL switches for the look-dev rig, read once per page load (the A/B and the gates use them).
//   ?look=before   today's look exactly (the old lights, camera, ACES, avatarX and the old meadow framing)
//   ?look=after    force the rig on a page that does not frame the meadow (the dev preview)
//   ?tier=low|high override the quality tier (shots of both tiers on one machine)
//   ?adaptive=0    keep the DPR cap fixed (frame-stepped shots on a slow headless GPU)
// No React, no three.js.

function readParams() {
  try {
    return new URLSearchParams(window.location.search);
  } catch {
    return new URLSearchParams('');
  }
}

let cached = null;
export function lookParams() {
  if (!cached) {
    const p = readParams();
    cached = {
      look: p.get('look') || '',
      tier: p.get('tier') === 'low' || p.get('tier') === 'high' ? p.get('tier') : '',
      adaptive: p.get('adaptive') !== '0',
    };
  }
  return cached;
}

/** True unless "?look=before": the painted-meadow page then uses the new framing, rig and grade. */
export function lookdevEnabled() {
  return lookParams().look !== 'before';
}

/** The avatar canvas runs the rig when the stage is the painted meadow, or when "?look=after" asks for it. */
export function lookdevActive(framing) {
  const { look } = lookParams();
  return look !== 'before' && (framing === 'meadow' || look === 'after');
}
