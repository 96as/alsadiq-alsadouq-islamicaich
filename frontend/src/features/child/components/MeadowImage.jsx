import { useLayoutEffect, useRef, useState } from 'react';
import { MEADOW_IMAGE, MEADOW_NARROW, MEADOW_SRC, MEADOW_SRCSET, computeFraming, meadowCap, meadowNarrowSrcset } from './meadowFraming';
// look-dev: the painting keeps a static fit and the 3D stage is solved to it (avatar/lookdev/stageFraming.js).
import { lookdevEnabled } from './avatar/lookdev/lookFlag';
import { detectQuality } from './forest/quality'; // cards-spec (05) perf review: the narrow tier's cap follows the GL layer's

/**
 * The lead's painted meadow, sharp at any size: a srcset of the same 16:9 picture (a phone gets a
 * small file, a 4K or ultra-wide window a large one), drawn with object-fit: cover so it is never
 * stretched.
 *
 * With `anchored` (the voice screens that stand the avatar on the path) the focal point follows the
 * stage: the path stays under Sadiq and his feet row stays where the camera puts them, on any shape
 * from a tall phone to a 32:9 window. A soft contact shadow sits under his feet.
 *
 * The picture path lives in one place, meadowFraming.js (MEADOW_IMAGE), so the living meadow can swap it.
 */
export default function MeadowImage({ anchored = false, className = '' }) {
  const rootRef = useRef(null);
  const [fr, setFr] = useState(null);
  const lookdev = lookdevEnabled(); // look-dev: true unless "?look=before"
  // cards-spec (05) perf review: the narrow tier stops at the width MeadowLife's GL layer loads (2560 on a phone), so a
  // phone downloads one meadow file, not the <img>'s 3840/5120 plus the GL layer's 2560 (meadowFraming.js meadowCap).
  const [narrowSrcset] = useState(() => meadowNarrowSrcset(meadowCap(detectQuality())));

  useLayoutEffect(() => {
    if (!anchored || lookdev) return undefined; // look-dev: no anchoring, the camera follows the painting
    const el = rootRef.current;
    if (!el) return undefined;
    const measure = () => {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) setFr(computeFraming(r.width, r.height));
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, [anchored, lookdev]);

  const position = fr ? `${(fr.objectX * 100).toFixed(2)}% ${(fr.objectY * 100).toFixed(2)}%` : '47.5% center';

  return (
    <div
      ref={rootRef}
      aria-hidden="true"
      data-meadow-image=""
      className={`pointer-events-none absolute inset-0 select-none overflow-hidden ${className}`}
    >
      <picture>
        {/* cards-spec (05) perf: a portrait phone sees a thin slice of the painting, so it takes the narrow tier (about 45% fewer bytes) */}
        <source media={MEADOW_NARROW.media} srcSet={narrowSrcset} sizes={MEADOW_IMAGE.sizes} type="image/webp" />
        <img
          src={MEADOW_SRC}
          srcSet={MEADOW_SRCSET}
          sizes={MEADOW_IMAGE.sizes}
          alt=""
          draggable="false"
          decoding="async"
          fetchPriority="high"
          className="absolute inset-0 h-full w-full object-cover"
          style={{ objectPosition: position }}
        />
      </picture>
      {anchored && fr && !lookdev && ( // look-dev: the contact shadow is now drawn in 3D
        <div
          data-meadow-shadow=""
          className="absolute"
          style={{
            left: fr.pathX, // Avatar.jsx puts Sadiq on this column
            top: fr.feetY,
            width: fr.avatarPx * 0.62,
            height: fr.avatarPx * 0.11,
            transform: 'translate(-50%, -42%)',
            background: 'radial-gradient(closest-side, rgba(24,34,10,0.5), rgba(24,34,10,0.22) 55%, rgba(24,34,10,0) 100%)',
            filter: 'blur(2px)',
            opacity: 'calc(1 - var(--sadiq-shot, 0))', // hotfix-2: the conversation shot crops his feet, so the shadow fades with it
          }}
        />
      )}
    </div>
  );
}
