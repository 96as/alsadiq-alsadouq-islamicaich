import { useCallback, useEffect, useRef } from 'react';
import { createVisemeDriver } from './visemeDriver.js';

/**
 * Lip-sync from an audio source. Returns stable functions that read the newest viseme state, so
 * a per-frame consumer (the avatar's useFrame, a meter) never causes a React render.
 *
 * @param {MediaStream|MediaStreamTrack|HTMLMediaElement|object|null} source the agent's voice:
 *   a LiveKit remote audio track, a MediaStream or track, or an audio element. null = none.
 * @param {{lang?: 'en'|'ar', timeline?: import('./timelineSync.js').TimelineSync|null}} [opts] 'ar'
 *   selects the Arabic vowel mode (default 'en'); `timeline` is the sink of the lk.lipsync messages
 * @returns {{
 *   getLipsync: () => ({weights: Float32Array, stress: number, level: number, speaking: boolean,
 *                       active: boolean, phraseEnds: number}) | null,
 *   resume: () => Promise<void>,
 * }}
 *   getLipsync() gives 14 weights in the Oculus order (see visemes.js), or null when there is no
 *   source or the audio context is not running yet (call resume() from a click or tap).
 */
export default function useVisemes(source, { lang = 'en', timeline = null } = {}) {
  const driverRef = useRef(null);

  useEffect(() => {
    const driver = createVisemeDriver({ source, lang, timeline });
    driverRef.current = driver;
    return () => {
      driverRef.current = null;
      driver?.dispose();
    };
  }, [source, lang, timeline]);

  const getLipsync = useCallback(() => driverRef.current?.read() ?? null, []);
  const resume = useCallback(() => driverRef.current?.resume() ?? Promise.resolve(), []);
  // hotfix-2: for the showcase's Safari-safe tap (unlock, mute, and a check that sound can come out)
  const unlock = useCallback(() => driverRef.current?.unlock() ?? false, []);
  const setMuted = useCallback((m) => driverRef.current?.setMuted(m) ?? false, []);
  const contextState = useCallback(() => driverRef.current?.contextState ?? 'none', []);
  const gainValue = useCallback(() => driverRef.current?.gainValue ?? -1, []);
  return { getLipsync, resume, unlock, setMuted, contextState, gainValue };
}
