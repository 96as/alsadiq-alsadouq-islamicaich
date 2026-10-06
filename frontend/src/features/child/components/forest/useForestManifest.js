import { useEffect, useState } from 'react';
import { assetUrl } from '../../../../utils/assetUrl';

export const MANIFEST_URL = assetUrl('/models/forest/forest-manifest.json');

/**
 * Checks a parsed manifest. Vite's single page fallback answers a missing file
 * with index.html and status 200, so "response ok" alone proves nothing: the
 * body has to be JSON with a "model" string that points at a .glb.
 */
export function validateManifest(data) {
  if (!data || typeof data !== 'object') return null;
  if (typeof data.model !== 'string' || !data.model.startsWith('/') || !/\.glb(\?.*)?$/i.test(data.model)) return null;
  return {
    model: data.model,
    version: Number.isFinite(data.version) ? data.version : 0,
    bytes: Number.isFinite(data.bytes) ? data.bytes : 0,
    triangles: Number.isFinite(data.triangles) ? data.triangles : 0,
    source: typeof data.source === 'string' ? data.source : '',
    generated: typeof data.generated === 'string' ? data.generated : '',
  };
}

/** "Click_Bird" becomes "Bird", "Click_Sun_Flower" becomes "Sun Flower". */
export function clickLabel(name) {
  return name.replace(/^Click_/, '').replace(/[_.]+/g, ' ').trim() || 'Item';
}

/** Looks for the Blender pipeline manifest. status: 'loading' | 'none' | 'ready'. */
export function useForestManifest(enabled = true) {
  // The showcase build sets VITE_FOREST_MANIFEST=0 when no manifest was shipped, so the
  // page does not request a file that is not there (a static host answers it with a 404).
  const shipped = import.meta.env.VITE_FOREST_MANIFEST !== '0';
  const [state, setState] = useState({ status: shipped ? 'loading' : 'none', manifest: null });

  useEffect(() => {
    if (!enabled || !shipped) return undefined;
    const controller = new AbortController();
    (async () => {
      try {
        const res = await fetch(MANIFEST_URL, { cache: 'no-store', signal: controller.signal });
        if (!res.ok) throw new Error(`manifest ${res.status}`);
        const text = await res.text();
        const manifest = validateManifest(JSON.parse(text));
        if (!manifest) throw new Error('manifest has no model');
        setState({ status: 'ready', manifest });
      } catch (err) {
        if (err?.name === 'AbortError') return;
        setState({ status: 'none', manifest: null });
      }
    })();
    return () => controller.abort();
  }, [enabled, shipped]);

  return enabled ? state : { status: 'none', manifest: null };
}
