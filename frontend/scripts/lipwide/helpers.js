// Init script for the wide lip-sync glitch test (scripts/lipwide/*.py). Dev only: it needs the lab page
// (avatar-component-preview.html), which exposes window.__control and window.__voice.
//
//   window.__rec.start()/stop()      samples every displayed frame at the end of the avatar's useFrame
//                                    (acting.onFrame): the morph influences of every morph mesh, the jaw
//                                    command and the real jaw bone angle, the audio clock
//   window.__tearCheck(frames)       sets recorded morphs + jaw back on the real mesh and counts flipped and
//                                    crushed triangles of the face region (head-local, so body motion is out)
//   window.__capturePoses(poses)     renders each recorded pose (morphs + jaw) on the live avatar and returns a
//                                    face crop (JPEG data URL) per pose
(() => {
  const orig = HTMLMediaElement.prototype.play;
  HTMLMediaElement.prototype.play = function (...a) {
    window.__aud = this;
    return orig.apply(this, a);
  };

  const ctl = () => window.__control && window.__control.current;
  const r5 = (v) => Math.round(v * 1e5) / 1e5;

  function morphMeshes() {
    const c = ctl();
    let root = c.bones.head;
    while (root.parent) root = root.parent;
    const list = [];
    root.traverse((o) => {
      if (o.morphTargetDictionary && o.morphTargetInfluences) list.push(o);
    });
    return { root, list };
  }

  const rec = { on: false, rows: [], nonFinite: 0, meshes: null, t0: 0 };
  window.__rec = {
    names() {
      const { list } = morphMeshes();
      return list.map((m) => ({ name: m.name, dict: { ...m.morphTargetDictionary }, count: m.morphTargetInfluences.length }));
    },
    start() {
      const c = ctl();
      const { list } = morphMeshes();
      rec.meshes = list;
      rec.rows = [];
      rec.nonFinite = 0;
      rec.t0 = performance.now();
      const jr = c.bones.jawRest;
      const jb = c.bones.jaw;
      const sh = c.acting.shaper;
      c.acting.onFrame = () => {
        if (!rec.on) return;
        const q = jb.quaternion;
        const relx = jr.w * q.x - jr.x * q.w - jr.y * q.z + jr.z * q.y;
        const relw = jr.w * q.w + jr.x * q.x + jr.y * q.y + jr.z * q.z;
        const ja = 2 * Math.atan2(relx, relw);
        const aud = window.__aud;
        const row = {
          t: performance.now() - rec.t0,
          at: aud ? aud.currentTime : -1,
          pa: aud ? (aud.paused ? 1 : 0) : 1,
          en: aud ? (aud.ended ? 1 : 0) : 0,
          jw: sh.jaw,
          ja,
          q: [q.x, q.y, q.z, q.w],
          lv: c.lipRig.live ? 1 : 0,
          ac: c.lipRig.active ? 1 : 0,
          pj: sh.ppJawMorph,
          m: [],
        };
        let bad = 0;
        for (const v of [row.jw, row.ja, row.pj, ...row.q]) if (!Number.isFinite(v)) bad++;
        for (const mesh of rec.meshes) {
          const arr = mesh.morphTargetInfluences;
          const out = new Array(arr.length);
          for (let i = 0; i < arr.length; i++) {
            const v = arr[i];
            if (!Number.isFinite(v)) {
              bad++;
              out[i] = null;
            } else out[i] = r5(v);
          }
          row.m.push(out);
        }
        rec.nonFinite += bad;
        row.bad = bad;
        rec.rows.push(row);
      };
      rec.on = true;
    },
    stop() {
      const c = ctl();
      rec.on = false;
      c.acting.onFrame = null;
      const aud = window.__aud;
      return { rows: rec.rows, nonFinite: rec.nonFinite, duration: aud ? aud.duration : 0 };
    },
  };

  // ---- triangle flips and crushes ----------------------------------------------------------------------
  function sub(a, b) {
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  }
  function cross(a, b) {
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  }

  async function prepareTear() {
    const c = ctl();
    if (window.__tearState) return window.__tearState;
    const mm = await c.metrics();
    const { list } = morphMeshes();
    const jaw = c.bones.jaw;
    const jawRest = c.bones.jawRest.clone();
    const state = { mPerUnit: mm.mPerUnit, jawRest, meshes: [] };
    for (const mesh of list) {
      if (!mesh.isSkinnedMesh) continue;
      const g = mesh.geometry;
      const pos = g.attributes.position;
      const idx = g.index ? g.index.array : null;
      const triCount = idx ? idx.length / 3 : pos.count / 3;
      const jawIdx = mesh.skeleton.bones.indexOf(jaw);
      const si = g.attributes.skinIndex;
      const sw = g.attributes.skinWeight;
      const mask = new Uint8Array(pos.count);
      const morphs = g.morphAttributes.position || [];
      for (let v = 0; v < pos.count; v++) {
        let jw = 0;
        for (let k = 0; k < 4; k++) if (si.getComponent(v, k) === jawIdx) jw += sw.getComponent(v, k);
        let moved = jw > 0.02;
        if (!moved) {
          for (const ma of morphs) {
            if (Math.abs(ma.getX(v)) + Math.abs(ma.getY(v)) + Math.abs(ma.getZ(v)) > 1e-6) {
              moved = true;
              break;
            }
          }
        }
        mask[v] = moved ? 1 : 0;
      }
      const tris = [];
      for (let t = 0; t < triCount; t++) {
        const a = idx ? idx[3 * t] : 3 * t;
        const b = idx ? idx[3 * t + 1] : 3 * t + 1;
        const cc = idx ? idx[3 * t + 2] : 3 * t + 2;
        if (mask[a] || mask[b] || mask[cc]) tris.push(a, b, cc);
      }
      const verts = Array.from(new Set(tris));
      state.meshes.push({ mesh, tris: Int32Array.from(tris), verts, vmask: mask, restN: null, restA: null, morphCount: mesh.morphTargetInfluences.length });
    }
    captureRest(state);
    window.__tearState = state;
    return state;
  }

  // rest: every morph 0, jaw at its rest. The idle animation keeps moving the neck and shoulders, so the rest
  // reference is taken again right before every pose (same bone state), never once at the start.
  function captureRest(state) {
    const c = ctl();
    const jaw = c.bones.jaw;
    const head = c.bones.head;
    const { root } = morphMeshes();
    const saveJaw = jaw.quaternion.clone();
    const saveMorph = state.meshes.map((s) => s.mesh.morphTargetInfluences.slice());
    for (const s of state.meshes) s.mesh.morphTargetInfluences.fill(0);
    jaw.quaternion.copy(state.jawRest);
    for (const s of state.meshes) {
      const { n, a } = evaluate(s, head, root);
      s.restN = n;
      s.restA = a;
    }
    jaw.quaternion.copy(saveJaw);
    state.meshes.forEach((s, i) => {
      for (let k = 0; k < saveMorph[i].length; k++) s.mesh.morphTargetInfluences[k] = saveMorph[i][k];
    });
  }

  const _inv = { m: null };
  function evaluate(s, head, root) {
    root.updateMatrixWorld(true);
    s.mesh.skeleton.update();
    if (!_inv.m) _inv.m = head.matrixWorld.clone();
    _inv.m.copy(head.matrixWorld).invert();
    const P = new Map();
    const v = { x: 0, y: 0, z: 0 };
    const tmp = head.position.clone();
    for (const i of s.verts) {
      s.mesh.getVertexPosition(i, tmp);
      tmp.applyMatrix4(s.mesh.matrixWorld).applyMatrix4(_inv.m);
      P.set(i, [tmp.x, tmp.y, tmp.z]);
    }
    const nT = s.tris.length / 3;
    const n = new Float64Array(nT * 3);
    const a = new Float64Array(nT);
    for (let t = 0; t < nT; t++) {
      const p0 = P.get(s.tris[3 * t]);
      const p1 = P.get(s.tris[3 * t + 1]);
      const p2 = P.get(s.tris[3 * t + 2]);
      const c = cross(sub(p1, p0), sub(p2, p0));
      n[3 * t] = c[0];
      n[3 * t + 1] = c[1];
      n[3 * t + 2] = c[2];
      a[t] = 0.5 * Math.hypot(c[0], c[1], c[2]);
    }
    void v;
    return { n, a };
  }

  function setPose(state, frame) {
    const c = ctl();
    state.meshes.forEach((s, mi) => {
      const arr = frame.m[mi];
      const dst = s.mesh.morphTargetInfluences;
      for (let k = 0; k < dst.length; k++) dst[k] = arr && arr[k] != null ? arr[k] : 0;
    });
    const q = frame.q;
    c.bones.jaw.quaternion.set(q[0], q[1], q[2], q[3]);
  }

  window.__tearCheck = async (frames, areaMm2 = [0.25]) => {
    const c = ctl();
    const state = await prepareTear();
    const head = c.bones.head;
    const { root } = morphMeshes();
    const k2 = state.mPerUnit * state.mPerUnit * 1e6; // unit^2 -> mm^2
    const out = [];
    const saveJaw = c.bones.jaw.quaternion.clone();
    for (const f of frames) {
      captureRest(state);
      setPose(state, f);
      let flips = 0;
      let crushed = 0;
      let nTri = 0;
      const sig = areaMm2.map(() => ({ flips: 0, crushed: 0 }));
      let worstDot = 1;
      let worst = null;
      state.meshes.forEach((s) => {
        const { n, a } = evaluate(s, head, root);
        const nT = a.length;
        nTri += nT;
        for (let t = 0; t < nT; t++) {
          const restA = s.restA[t];
          const nr0 = s.restN[3 * t];
          const nr1 = s.restN[3 * t + 1];
          const nr2 = s.restN[3 * t + 2];
          const lr = Math.hypot(nr0, nr1, nr2);
          const lp = Math.hypot(n[3 * t], n[3 * t + 1], n[3 * t + 2]);
          if (lr < 1e-14) continue; // degenerate at rest: nothing to compare with
          const dot = lp < 1e-14 ? 1 : (nr0 * n[3 * t] + nr1 * n[3 * t + 1] + nr2 * n[3 * t + 2]) / (lr * lp);
          const poseMm = a[t] * k2;
          const restMm = restA * k2;
          const ratio = a[t] / restA;
          if (dot < 0) {
            flips++;
            if (dot < worstDot) {
              worstDot = dot;
              worst = { tri: t, mesh: s.mesh.name, dot: +dot.toFixed(3), poseMm2: +poseMm.toFixed(4), restMm2: +restMm.toFixed(3) };
            }
            areaMm2.forEach((th, i) => {
              if (poseMm >= th) sig[i].flips++;
            });
          }
          if (ratio < 0.05) {
            crushed++;
            areaMm2.forEach((th, i) => {
              if (restMm >= th) sig[i].crushed++;
            });
          }
        }
      });
      out.push({ flips, crushed, nTri, sig, worst });
    }
    c.bones.jaw.quaternion.copy(saveJaw);
    return out;
  };

  // ---- face crops of recorded poses -----------------------------------------------------------------------
  window.__capturePoses = async (poses, size = 360) => {
    const c = ctl();
    const state = await prepareTear();
    const canvas = document.querySelector('canvas');
    const faceBones = new Set([c.bones.head, c.bones.jaw]);
    const result = [];
    let sq = 0;
    for (const p of poses) {
      const res = await new Promise((resolve) => {
        c.acting.onFrame = () => {
          setPose(state, p);
          c.acting.onFrame = null;
          queueMicrotask(() => {
            try {
              // the drawing buffer is still valid: the avatar's render has just run in this same callback
              const cam = c.camera;
              const s0 = state.meshes[0];
              const g = s0.mesh.geometry;
              const si = g.attributes.skinIndex;
              const sw = g.attributes.skinWeight;
              const bones = s0.mesh.skeleton.bones;
              s0.mesh.skeleton.update();
              let x0 = Infinity;
              let x1 = -Infinity;
              let y0 = Infinity;
              let y1 = -Infinity;
              const t = c.bones.head.position.clone();
              const W = canvas.clientWidth;
              const H = canvas.clientHeight;
              for (let i = 0; i < g.attributes.position.count; i += 3) {
                let best = -1;
                let bw = 0;
                for (let k = 0; k < 4; k++) {
                  const w = sw.getComponent(i, k);
                  if (w > bw) {
                    bw = w;
                    best = si.getComponent(i, k);
                  }
                }
                if (bw < 0.5 || !faceBones.has(bones[best])) continue;
                s0.mesh.getVertexPosition(i, t);
                t.applyMatrix4(s0.mesh.matrixWorld).project(cam);
                const x = (t.x * 0.5 + 0.5) * W;
                const y = (1 - (t.y * 0.5 + 0.5)) * H;
                x0 = Math.min(x0, x);
                x1 = Math.max(x1, x);
                y0 = Math.min(y0, y);
                y1 = Math.max(y1, y);
              }
              const cx = (x0 + x1) / 2;
              const cy = (y0 + y1) / 2;
              if (!sq) sq = Math.max(x1 - x0, y1 - y0) * 1.12;
              const scale = canvas.width / W;
              const out = document.createElement('canvas');
              out.width = size;
              out.height = size;
              const ctx = out.getContext('2d');
              ctx.drawImage(canvas, (cx - sq / 2) * scale, (cy - sq / 2) * scale, sq * scale, sq * scale, 0, 0, size, size);
              resolve({ url: out.toDataURL('image/jpeg', 0.92), box: [x0, y0, x1, y1].map((v) => Math.round(v)), sq: Math.round(sq) });
            } catch (e) {
              resolve({ error: String(e) });
            }
          });
        };
      });
      result.push(res);
    }
    return result;
  };
})();
