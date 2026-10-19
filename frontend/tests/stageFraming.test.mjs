// Look-dev stage framing (LOOKDEV-SPEC S6, gates L1 to L3). Run with `npm run test:lookdev`.
// The maths use a real three.js PerspectiveCamera with the same setViewOffset call the app makes, so the
// horizon and size checks are measured on the projection, not re-derived from the formulas under test.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { PerspectiveCamera, Vector3 } from 'three';
import { LOOKDEV } from '../src/features/child/components/avatar/lookdev/lookdevConfig.js';
import {
  PAINTING,
  horizonY,
  paintingToScreen,
  pathCentreU,
  pathWidthU,
  screenToPaintingV,
  solveFraming,
} from '../src/features/child/components/avatar/lookdev/stageFraming.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const src = (rel) => readFileSync(path.join(here, '..', 'src', 'features', 'child', 'components', rel), 'utf8');

// The five stages of the spec (S6.3), CSS px, and the Hf the spec's table gives for each (+/- 0.02).
const SIZES = [
  { name: 'phone 390x844', W: 390, H: 844, Hf: 0.5 },
  { name: 'tablet 820x1180', W: 820, H: 1180, Hf: 0.51 },
  { name: '16:9 1280x720', W: 1280, H: 720, Hf: 0.658 },
  { name: 'ultrawide 2000x713', W: 2000, H: 713, Hf: 0.68 },
  { name: '21:9 2560x1080', W: 2560, H: 1080, Hf: 0.68 },
];
const F = LOOKDEV.framing;

/** The camera the app builds (AvatarLookdev StageCamera), and a projection to stage fractions. */
function rig(W, H) {
  const fr = solveFraming(W, H);
  const cam = new PerspectiveCamera(fr.fov, W / H, 0.1, 50);
  cam.position.set(0, fr.eye, fr.dist);
  cam.setViewOffset(W, H, 0, fr.viewOffsetY, W, H);
  cam.updateProjectionMatrix();
  cam.updateMatrixWorld(true);
  const project = (x, y, z) => {
    const p = new Vector3(x, y, z).project(cam);
    return { x: (p.x * 0.5 + 0.5) * W, y: (0.5 - p.y * 0.5) * H }; // px from the top-left
  };
  return { fr, cam, project };
}

for (const s of SIZES) {
  test(`L1 horizon match at ${s.name}`, () => {
    const { fr, project } = rig(s.W, s.H);
    const far = project(0, 0, -1e5); // a ground point at the horizon
    const painted = horizonY(s.W, s.H) * s.H;
    assert.ok(Math.abs(far.y - painted) / s.H < 0.005, `3D horizon ${far.y.toFixed(1)} px, painted ${painted.toFixed(1)} px`);
    assert.ok(Math.abs(fr.yH * s.H - painted) < 1e-6);
  });

  test(`L2 size and safe areas at ${s.name}`, () => {
    const { fr, project } = rig(s.W, s.H);
    const feet = project(fr.avatarX, 0, 0);
    const ears = project(fr.avatarX, F.charHeight, 0);
    const bbox = (feet.y - ears.y) / s.H;
    assert.ok(Math.abs(bbox - s.Hf) <= 0.02, `bbox ${bbox.toFixed(3)} against the table's ${s.Hf}`);
    assert.ok(Math.abs(bbox - fr.Hf) < 1e-6, 'solveFraming reports the Hf the camera really gives');
    assert.ok(ears.y >= LOOKDEV.framing.safe.top + F.earsBelowHeader - 0.5, `ears ${ears.y.toFixed(1)} px under the header`);
    assert.ok(feet.y <= s.H - (LOOKDEV.framing.safe.bottom + F.feetAboveControls) + 0.5, `feet ${feet.y.toFixed(1)} px above the controls row`);
    // The horizon cuts him at k of his height.
    assert.ok(Math.abs((feet.y - fr.yH * s.H) / (feet.y - ears.y) - fr.k) < 1e-6);
  });

  test(`L3 feet on the path at ${s.name}`, () => {
    const { fr, project } = rig(s.W, s.H);
    const feet = project(fr.avatarX, 0, 0);
    const xFrac = feet.x / s.W;
    assert.ok(xFrac >= F.pathScreenX[0] - 1e-6 && xFrac <= F.pathScreenX[1] + 1e-6, `screen x ${xFrac.toFixed(3)} outside 0.40-0.60`);
    const v = screenToPaintingV(feet.y, s.W, s.H);
    const uC = pathCentreU(v);
    const w = pathWidthU(v);
    const [pxLo] = paintingToScreen(uC - w / 2, v, s.W, s.H);
    const [pxHi] = paintingToScreen(uC + w / 2, v, s.W, s.H);
    assert.ok(feet.x >= pxLo && feet.x <= pxHi, `feet x ${feet.x.toFixed(1)} px outside the path span ${pxLo.toFixed(1)}..${pxHi.toFixed(1)} (row v ${v.toFixed(3)})`);
  });
}

test('framing is continuous in aspect (no jump between neighbouring window shapes)', () => {
  let prev = null;
  for (let W = 500; W <= 2800; W += 20) {
    const fr = solveFraming(W, 720);
    if (prev) {
      assert.ok(Math.abs(fr.Hf - prev.Hf) < 0.02, `Hf jumps at W ${W}`);
      assert.ok(Math.abs(fr.feetX - prev.feetX) < 0.03, `feet x jumps at W ${W}`);
    }
    prev = fr;
  }
});

test('the avatar height never leaves the stage (any shape from 0.4 to 3.5 aspect)', () => {
  for (const a of [0.4, 0.46, 0.7, 1, 1.5, 1.78, 2.37, 2.81, 3.5]) {
    const H = 700;
    const fr = solveFraming(Math.round(H * a), H);
    assert.ok(fr.yFeet < 1 && fr.yFeet - fr.Hf > 0, `aspect ${a}: feet ${fr.yFeet.toFixed(2)} ears ${(fr.yFeet - fr.Hf).toFixed(2)}`);
  }
});

// ---- the fit constants must equal the painting's real fit (parsed from the source, so they cannot drift) ----
test('PAINTING mirrors MeadowImage.jsx and meadowFraming.js', () => {
  const image = src('MeadowImage.jsx');
  assert.match(image, /object-cover/, 'MeadowImage draws object-fit: cover');
  const pos = image.match(/'(\d+(?:\.\d+)?)%\s+center'/);
  assert.ok(pos, 'MeadowImage has a static "<x>% center" object-position');
  assert.equal(Number(pos[1]) / 100, PAINTING.posX, 'object-position x');
  assert.equal(PAINTING.posY, 0.5, '"center" is 50%');
  const framing = src('meadowFraming.js');
  const aspect = framing.match(/aspect:\s*(\d+)\s*\/\s*(\d+)/);
  assert.ok(aspect, 'MEADOW_IMAGE.aspect is a w / h expression');
  assert.equal(Number(aspect[1]) / Number(aspect[2]), PAINTING.aspect, 'picture aspect');
});

test('VoiceMode stands Sadiq on the meadow with the anchored image and the meadow framing', () => {
  const voice = src('VoiceMode.jsx');
  assert.match(voice, /<MeadowImage[^>]*anchored/, 'VoiceMode mounts <MeadowImage anchored />');
  assert.match(voice, /framing=["']meadow["']|framing=\{["']meadow["']\}/, 'VoiceMode gives the avatar framing="meadow"');
});

test('the look-dev config and framing stay plain data (no three.js, no React)', () => {
  for (const file of ['avatar/lookdev/lookdevConfig.js', 'avatar/lookdev/stageFraming.js', 'avatar/lookdev/lookFlag.js']) {
    const text = src(file);
    assert.doesNotMatch(text, /from ['"](three|react|@react-three)/, `${file} imports a runtime library`);
  }
});

test('the source tree carries no scripture markers (children app rule)', () => {
  for (const file of ['avatar/lookdev/lookdevConfig.js', 'avatar/lookdev/AvatarLookdev.jsx']) {
    assert.doesNotMatch(src(file), /[؀-ۿ]/, `${file} has Arabic text`);
  }
});
