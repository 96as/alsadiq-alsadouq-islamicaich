// The conversation shot's full-body end, for the look-dev stage camera (see stageFraming.js and conversationShot.js).
// Returns what meadowFraming.computeFraming returns, as far as the shot reads it, plus `tanHalf` (look-dev's lens)
// and `lensY` (the painted horizon as a fraction of the stage height; the camera has a vertical lens shift).
// Pure numbers, no React or three.js, so node can test it.
import { LOOKDEV } from './lookdevConfig.js';
import { solveFraming } from './stageFraming.js';

export function lookdevShotFraming(w, h) {
  const fr = solveFraming(w, h);
  const tanHalf = Math.tan((fr.fov * Math.PI) / 360);
  const worldH = 2 * fr.dist * tanHalf; // world units the camera sees from the top of the stage to the bottom
  const safe = LOOKDEV.framing.safe;
  return {
    worldH,
    // the world height at the middle row of the screen: the eye is level with the horizon row, which is yH of the way down
    targetY: fr.eye - (0.5 - fr.yH) * worldH,
    pathX: fr.feetX * w,
    avatarX: fr.avatarX,
    top: safe.top,
    bottom: safe.bottom,
    feetY: fr.yFeet * h,
    tanHalf,
    lensY: fr.yH,
  };
}
