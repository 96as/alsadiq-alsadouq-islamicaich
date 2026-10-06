// Step 2: the conversation shot on top of look-dev's stage camera (lookdev/shotFraming.js). Pure: no browser.
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { SHOT, shotCamera, shotTarget } from '../src/features/child/components/avatar/conversationShot.js';
import { lookdevShotFraming } from '../src/features/child/components/avatar/lookdev/shotFraming.js';
import { solveFraming } from '../src/features/child/components/avatar/lookdev/stageFraming.js';

const HEAD = { cy: 0.72, h: 0.3, w: 0.34 };
const SIZES = [[2000, 713], [1440, 900], [1280, 720], [768, 1024], [390, 844], [360, 740]];

test('at zoom 0 the shot camera is exactly the look-dev stage camera', () => {
  for (const [w, h] of SIZES) {
    const fr = lookdevShotFraming(w, h);
    const st = solveFraming(w, h);
    const tgt = shotTarget(fr, w, h, h, HEAD);
    const cam = shotCamera(fr, tgt, 0, w, h, st.avatarX);
    assert.ok(Math.abs(cam.x) < 1e-9, `${w}x${h} x ${cam.x}`);
    assert.ok(Math.abs(cam.eyeY - st.eye) < 1e-9, `${w}x${h} eye ${cam.eyeY} vs ${st.eye}`);
    assert.ok(Math.abs(cam.z - st.dist) < 1e-9, `${w}x${h} dist ${cam.z} vs ${st.dist}`);
  }
});

test('at zoom 1 the face is at least 25% of the viewport, and the horizon stays on the painted row', () => {
  for (const [w, h] of SIZES) {
    const fr = lookdevShotFraming(w, h);
    const st = solveFraming(w, h);
    const tgt = shotTarget(fr, w, h, h, HEAD);
    const cam = shotCamera(fr, tgt, 1, w, h, st.avatarX);
    const px = (HEAD.h / cam.worldH) * h;
    assert.ok(px >= SHOT.floorFrac * h, `${w}x${h}: face ${px.toFixed(0)}px`);
    // a level camera with the lens shift: the horizon is its principal row whatever the zoom
    assert.ok(Math.abs(fr.lensY - st.yH) < 1e-12);
  }
});

test('the zoom never goes wider than look-dev full body', () => {
  for (const [w, h] of SIZES) {
    const fr = lookdevShotFraming(w, h);
    const tgt = shotTarget(fr, w, h, h, HEAD);
    assert.ok(tgt.worldH <= fr.worldH + 1e-9);
  }
});
