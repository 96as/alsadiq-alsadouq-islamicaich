// hotfix-2: the conversation shot's maths (conversationShot.js). Pure: no browser. The measured face
// in the real model is checked by the e2e run (scripts in the hotfix 2 handoff).
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { computeFraming, FOV_DEG } from '../src/features/child/components/meadowFraming.js';
import { SHOT, shotCamera, shotTarget, stepAmount } from '../src/features/child/components/avatar/conversationShot.js';

// The head measured in the browser (world units, ears to chin) and where it stands in the idle pose.
const HEAD = { cy: 0.72, h: 0.3, w: 0.34 };
const SIZES = [[2000, 713], [1440, 900], [1280, 720], [768, 1024], [390, 844], [360, 740]];
const tan = Math.tan((FOV_DEG * Math.PI) / 360);

// Face height on screen for a camera that sees worldH world units over h px.
const facePx = (worldH, h) => (HEAD.h / worldH) * h;

test('the shot makes the face at least 25% of the viewport, on every size', () => {
  for (const [w, h] of SIZES) {
    const fr = computeFraming(w, h);
    const t = shotTarget(fr, w, h, h, HEAD);
    const px = facePx(t.worldH, h);
    assert.ok(px >= SHOT.floorFrac * h, `${w}x${h}: face ${px.toFixed(0)}px is under 25% (${(0.25 * h).toFixed(0)}px)`);
  }
});

test('the face fits across the stage, even on a phone', () => {
  for (const [w, h] of SIZES) {
    const fr = computeFraming(w, h);
    const t = shotTarget(fr, w, h, h, HEAD);
    const widthPx = (HEAD.w / t.worldH) * h;
    assert.ok(widthPx <= SHOT.widthFrac * w + 0.5, `${w}x${h}: the face is ${widthPx.toFixed(0)}px wide on a ${w}px stage`);
  }
});

test('the shot never zooms out from the full body, and is bigger than it', () => {
  for (const [w, h] of SIZES) {
    const fr = computeFraming(w, h);
    const t = shotTarget(fr, w, h, h, HEAD);
    assert.ok(t.worldH <= fr.worldH);
    assert.ok(facePx(t.worldH, h) > facePx(fr.worldH, h) * 1.4, `${w}x${h}: the shot is not clearly closer than the full body`);
  }
});

test('the face stays between the header and the controls', () => {
  for (const [w, h] of SIZES) {
    const fr = computeFraming(w, h);
    const t = shotTarget(fr, w, h, h, HEAD);
    const cam = shotCamera(fr, t, 1, w, h, fr.avatarX);
    const centreFromTop = (0.5 - (HEAD.cy - cam.y) / cam.worldH) * h;
    const px = facePx(cam.worldH, h);
    assert.ok(centreFromTop - px / 2 >= fr.top - 1, `${w}x${h}: the ears reach the header`);
    assert.ok(centreFromTop + px / 2 <= h - fr.bottom + 1, `${w}x${h}: the chin reaches the controls`);
  }
});

test('amount 0 is exactly the full-body framing; the camera never tilts', () => {
  for (const [w, h] of SIZES) {
    const fr = computeFraming(w, h);
    const t = shotTarget(fr, w, h, h, HEAD);
    const c0 = shotCamera(fr, t, 0, w, h, fr.avatarX);
    assert.ok(Math.abs(c0.x) < 1e-9 && Math.abs(c0.y - fr.targetY) < 1e-9 && Math.abs(c0.z - fr.distance) < 1e-9);
    const c1 = shotCamera(fr, t, 1, w, h, fr.avatarX);
    assert.ok(Math.abs(c1.z - c1.worldH / (2 * tan)) < 1e-9);
  }
});

test('Sadiq stays on the path column through the zoom', () => {
  for (const [w, h] of SIZES) {
    const fr = computeFraming(w, h);
    const t = shotTarget(fr, w, h, h, HEAD);
    for (const e of [0, 0.3, 0.7, 1]) {
      const c = shotCamera(fr, t, e, w, h, fr.avatarX);
      const screenX = w / 2 + ((fr.avatarX - c.x) / c.worldH) * h;
      assert.ok(Math.abs(screenX - fr.pathX) < 0.01, `${w}x${h} e=${e}: column ${screenX} vs ${fr.pathX}`);
    }
  }
});

test('the measured correction closes in, and a short stage under a tall viewport still reaches the floor', () => {
  const [w, h] = [390, 480]; // the phone sheet open: a short stage on an 844 px viewport
  const fr = computeFraming(w, h);
  const a = shotTarget(fr, w, h, 844, HEAD, 1);
  const b = shotTarget(fr, w, h, 844, HEAD, 1.2);
  assert.ok(b.worldH <= a.worldH);
  const usable = h - fr.top - fr.bottom;
  assert.ok(facePx(b.worldH, h) <= usable * SHOT.usableFrac + 0.5, 'the face must not outgrow the room between the header and the controls');
});

test('reduced motion cuts, otherwise it eases', () => {
  assert.equal(stepAmount(0, 1, 1 / 60, true), 1);
  const a = stepAmount(0, 1, 1 / 60, false);
  assert.ok(a > 0 && a < 0.1);
  let s = 0;
  for (let i = 0; i < 60 * 3; i += 1) s = stepAmount(s, 1, 1 / 60, false);
  assert.ok(s > 0.99, 'settles within about three seconds');
});
