// The wind noise as a GPU texture. The data is generated at load (windField.windNoiseData, 16 KB), so there is
// no asset file. Two helpers: raw WebGL2 (MeadowLife) and three.js (the forest materials).

import { NOISE_SIZE, windNoiseData } from './windField';

/** Upload the noise to a raw WebGL2 context as R8, LINEAR + REPEAT. Leaves TEXTURE_2D unbound afterwards. */
export function createWindNoiseGL(gl) {
  const tex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.R8, NOISE_SIZE, NOISE_SIZE, 0, gl.RED, gl.UNSIGNED_BYTE, windNoiseData());
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.REPEAT);
  gl.pixelStorei(gl.UNPACK_ALIGNMENT, 4);
  return tex;
}

let threeTexture = null;
/** The same noise as a three.js DataTexture (shared by every material). Pass the THREE namespace. */
export function windNoiseThree(THREE) {
  if (!threeTexture) {
    const t = new THREE.DataTexture(windNoiseData(), NOISE_SIZE, NOISE_SIZE, THREE.RedFormat, THREE.UnsignedByteType);
    t.wrapS = THREE.RepeatWrapping;
    t.wrapT = THREE.RepeatWrapping;
    t.magFilter = THREE.LinearFilter;
    t.minFilter = THREE.LinearFilter;
    t.generateMipmaps = false;
    t.colorSpace = THREE.NoColorSpace;
    t.unpackAlignment = 1;
    t.needsUpdate = true;
    threeTexture = t;
  }
  return threeTexture;
}
