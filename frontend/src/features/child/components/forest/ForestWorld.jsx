import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { PerformanceMonitor } from '@react-three/drei';
import * as THREE from 'three';
import { useFrame, useThree } from '@react-three/fiber';
import { ForestCtx } from './forestContext';
import SceneClock from './SceneClock';
import CameraRig, { AvatarShadow } from './CameraRig';
import { Backdrop, Moon, Stars } from './Backdrop';
import ProceduralForest from './ProceduralForest';
import Particles from './Particles';
import Butterflies from './Butterflies';
import ForestProps from './ForestProps';
import ForestModel from './ForestModel';
import ForestBoundary from './ForestBoundary';
import { COUNTS } from './quality';

/** Dev only: publishes draw stats so a test run can read them from the page. */
function DevStats({ rt }) {
  const gl = useThree((s) => s.gl);
  const camera = useThree((s) => s.camera);
  const size = useThree((s) => s.size);
  useEffect(() => {
    // lets a test find where a world point is on screen (for click tests)
    const v = new THREE.Vector3();
    window.__forestProject = (x, y, z) => {
      v.set(x, y, z).project(camera);
      return { x: ((v.x + 1) / 2) * size.width, y: ((1 - v.y) / 2) * size.height };
    };
    return () => {
      delete window.__forestProject;
    };
  }, [camera, size]);
  const last = useRef(-1);
  useFrame((state) => {
    // twice a second; a modulo window missed updates at low frame rates (stale stats)
    const t = state.clock.elapsedTime;
    if (t - last.current < 0.5 && window.__forestStats) return;
    last.current = t;
    window.__forestStats = {
      quality: rt.quality,
      authored: { ...rt.stats.triangles, total: rt.stats.total },
      renderedTriangles: gl.info.render.triangles,
      drawCalls: gl.info.render.calls,
      dpr: gl.getPixelRatio(),
    };
  });
  return null;
}

/**
 * Everything inside the canvas. The procedural forest is drawn until the
 * Blender model (if there is one) has downloaded, then it is swapped out.
 */
export default function ForestWorld({ rt, manifest, onClicks, interactive = false }) {
  const mounted = useRef(0);
  useEffect(() => {
    mounted.current = performance.now();
  }, []);
  const [model, setModel] = useState(null); // { hasBackdrop, clicks } once the .glb is in
  const [modelFailed, setModelFailed] = useState(false);
  const counts = COUNTS[rt.quality];

  const onLoaded = useCallback(
    (info) => {
      setModel(info);
      if (onClicks) onClicks(info.clicks);
    },
    [onClicks],
  );

  const useModel = !!manifest && !modelFailed;
  const showProcedural = !model;
  const showBackdrop = !model || !model.hasBackdrop;

  return (
    <ForestCtx.Provider value={rt}>
      <SceneClock />
      <CameraRig />
      <Suspense fallback={null}>{showBackdrop && <Backdrop />}</Suspense>
      <Stars count={counts.stars} />
      <Moon />
      {showProcedural && <ProceduralForest />}
      <AvatarShadow />
      <Particles counts={counts} />
      <Butterflies />
      {interactive && <ForestProps />}
      {/* Frames stay under 40 fps for about 3 s: step the quality down, never back up (see rt.degrade). */}
      <PerformanceMonitor
        ms={250}
        iterations={12}
        flipflops={3}
        bounds={() => [40, 120]}
        onDecline={() => {
          if (performance.now() - mounted.current < 6000) return;
          // eslint-disable-next-line react-hooks/immutability -- the runtime is a shared mutable object by design
          rt.degrade = Math.min(rt.degrade + 1, 3);
        }}
      />
      {useModel && (
        <ForestBoundary onError={() => setModelFailed(true)}>
          <Suspense fallback={null}>
            <ForestModel manifest={manifest} onLoaded={onLoaded} />
          </Suspense>
        </ForestBoundary>
      )}
      {import.meta.env.DEV && <DevStats rt={rt} />}
    </ForestCtx.Provider>
  );
}
