import { Fragment, useRef } from 'react';
import { Leaf } from 'lucide-react';
import useStageAnchor, { archInset } from '../child/components/forest/useStageAnchor';
import { wordsOf } from './useStageSpeech';

/**
 * Small pieces that sit on the 3D forest stage: a bubble that points at Sadiq's head, the book's value
 * card, the bulbul's sleep letters and the real buttons laid over Sadiq and the three props.
 * Used by the demo landing (DemoHeroScene) and the child idle screen (ChildIdleStage).
 * Every piece is pinned with useStageAnchor, so nothing re-renders per frame.
 */

const clamp = (v, lo, hi) => Math.min(Math.max(v, lo), hi);

// ── Where things sit (all in CSS px inside the stage) ────────────────────────────────────────

/** Puts a box of `size` above the point (cx, bottomY), kept inside the arch, with its tail on cx. */
function fitAbove(out, size, cx, bottomY, ok) {
  if (!ok) {
    out.show = false;
    return;
  }
  const pad = 12;
  const y = Math.max(bottomY - size.h, pad);
  const inset = archInset(size.radius, y);
  const minX = pad + inset;
  const maxX = Math.max(minX, size.stageW - pad - size.w - inset);
  const x = clamp(cx - size.w / 2, minX, maxX);
  out.x = x;
  out.y = y;
  out.tail = clamp(cx - x, 22, Math.max(size.w - 22, 22));
}

const placeBubble = (rt, size, out) => fitAbove(out, size, rt.screen.headX, rt.screen.headY - 10, rt.screen.visible);
const placeCard = (rt, size, out) => {
  const b = rt.propBox.book;
  fitAbove(out, size, b.x, b.y - b.h / 2 - 6, b.visible);
};
const placeZ = (rt, size, out) => {
  const b = rt.propBox.bird;
  if (!b.visible) {
    out.show = false;
    return;
  }
  out.x = b.x - size.w / 2;
  out.y = b.y - b.h / 2 - size.h + 6;
};
const placeSadiq = (rt, size, out) => {
  const s = rt.screen;
  if (!s.visible || s.heightPx < 20) {
    out.show = false;
    return;
  }
  const h = s.heightPx;
  const w = Math.max(h * 0.6, 48);
  out.w = w;
  out.h = Math.max(h, 48);
  out.x = s.feetX - w / 2;
  out.y = s.feetY - out.h;
};
const placeProp = (name) => (rt, size, out) => {
  const b = rt.propBox[name];
  if (!b.visible) {
    out.show = false;
    return;
  }
  out.w = Math.max(b.w, 48);
  out.h = Math.max(b.h, 48);
  out.x = b.x - out.w / 2;
  out.y = b.y - out.h / 2;
};
const PLACE = { sadiq: placeSadiq, lantern: placeProp('lantern'), book: placeProp('book'), bird: placeProp('bird') };

// ── Pieces ───────────────────────────────────────────────────────────────────────────────────

/** A positioned wrapper; its content animates on a child (the wrapper only carries the transform). */
export function Anchor({ controlRef, place, className = '', children, ...rest }) {
  const ref = useRef(null);
  useStageAnchor(controlRef, ref, place);
  return (
    <div ref={ref} className={`demo-anchor ${className}`} {...rest}>
      {children}
    </div>
  );
}

/** The words of a line, each in its own span so they can arrive one by one (never split inside a word). */
export function Words({ text }) {
  const words = wordsOf(text);
  return words.map((w, i) => (
    <Fragment key={`${w}-${i}`}>
      <span className="demo-word" style={{ '--w': i }}>{w}</span>
      {i < words.length - 1 ? ' ' : null}
    </Fragment>
  ));
}

/** The line bubble, with its tail on Sadiq's head. `bubble` is { id, text, leaving }. */
export function Bubble({ controlRef, bubble }) {
  return (
    <Anchor controlRef={controlRef} place={placeBubble}>
      <p
        key={bubble.id}
        className="demo-bubble"
        data-leaving={bubble.leaving ? 'true' : 'false'}
        role="status"
        aria-label={bubble.text}
      >
        <span aria-hidden="true">
          <Words text={bubble.text} />
        </span>
      </p>
    </Anchor>
  );
}

/** The same bubble placed by CSS (no 3D stage to anchor to: the meadow fallback, or before the forest draws). */
export function StaticBubble({ bubble }) {
  return (
    <p
      key={bubble.id}
      className="demo-bubble demo-bubble-static"
      data-leaving={bubble.leaving ? 'true' : 'false'}
      role="status"
      aria-label={bubble.text}
    >
      <span aria-hidden="true">
        <Words text={bubble.text} />
      </span>
    </p>
  );
}

function ValueCard({ controlRef, card, values }) {
  const v = values[card.idx];
  return (
    <Anchor controlRef={controlRef} place={placeCard}>
      <div key={card.id} className="demo-value" data-leaving={card.leaving ? 'true' : 'false'} role="status">
        <Leaf className="demo-value-leaf" strokeWidth={2.25} aria-hidden="true" />
        <p className="demo-value-name">{v.name}</p>
        <p className="demo-value-text">{v.text}</p>
      </div>
    </Anchor>
  );
}

function SleepLetters({ controlRef, letter }) {
  return (
    <Anchor controlRef={controlRef} place={placeZ} aria-hidden="true">
      <span className="demo-z" style={{ '--z': 0 }}>{letter}</span>
      <span className="demo-z" style={{ '--z': 1 }}>{letter}</span>
      <span className="demo-z" style={{ '--z': 2 }}>{letter}</span>
    </Anchor>
  );
}

/** A real button over a 3D object. The label is also the accessible name, and shows as a verb tag. */
export function TapTarget({ name, controlRef, label, showLabel, quiet = false, onTap, onHover, className = '' }) {
  const ref = useRef(null);
  useStageAnchor(controlRef, ref, PLACE[name]);
  return (
    <button
      ref={ref}
      type="button"
      className={`demo-anchor demo-target ${className}`}
      data-target={name}
      data-flash={showLabel ? 'true' : 'false'}
      data-quiet={quiet ? 'true' : 'false'}
      aria-label={label}
      onClick={() => onTap(name)}
      onPointerEnter={() => onHover(name, true)}
      onPointerLeave={() => onHover(name, false)}
      onFocus={() => onHover(name, true)}
      onBlur={() => onHover(name, false)}
    >
      <span className="demo-vlabel" aria-hidden="true">{label}</span>
    </button>
  );
}

/**
 * Sadiq's tap target, the lantern, the book and the bulbul as buttons, plus the things that belong to
 * them (the sleep letters, the value card, the bubble). `speech` is the object from useStageSpeech.
 */
export function StageLayer({ controlRef, t, speech, onTapSadiq, sadiqLabel }) {
  const { ps, flash, card, bubble, onHover, onTapProp } = speech;
  return (
    <>
      <TapTarget
        name="sadiq"
        controlRef={controlRef}
        label={sadiqLabel || t.labels.sadiq}
        showLabel={flash === 'sadiq'}
        onTap={onTapSadiq}
        onHover={onHover}
        className="demo-target-sadiq"
      />
      <TapTarget
        name="lantern"
        controlRef={controlRef}
        label={ps.lit ? t.labels.lanternLit : t.labels.lantern}
        showLabel={flash === 'lantern'}
        onTap={onTapProp}
        onHover={onHover}
      />
      <TapTarget
        name="book"
        controlRef={controlRef}
        label={t.labels.book}
        showLabel={flash === 'book'}
        quiet={Boolean(card)}
        onTap={onTapProp}
        onHover={onHover}
      />
      <TapTarget
        name="bird"
        controlRef={controlRef}
        label={ps.asleep ? t.labels.birdAsleep : t.labels.bird}
        showLabel={flash === 'bird'}
        onTap={onTapProp}
        onHover={onHover}
      />
      {ps.asleep ? <SleepLetters controlRef={controlRef} letter={t.sleepLetter} /> : null}
      {card ? <ValueCard controlRef={controlRef} card={card} values={t.values} /> : null}
      {bubble ? <Bubble controlRef={controlRef} bubble={bubble} /> : null}
    </>
  );
}
