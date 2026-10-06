import { Fragment, useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { gsap } from 'gsap';
import { LogIn, MoonStar, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import {
  describeDemoError,
  readDemoLang,
  startOrRestartDemo,
  writeDemoLang,
} from '../services/demoService';
import { COPY } from '../features/demo/copy';
import DemoHeroScene from '../features/demo/DemoHeroScene';
import TimePill from '../features/demo/TimePill';
import SoundPill from '../features/demo/SoundPill';
import Spill from '../features/demo/Spill';
import { showVeil, hideVeil } from '../features/demo/transitionVeil';
import { useClockPeriod, useMedia, useReducedMotion } from '../features/demo/hooks';
import useSceneTilt from '../features/demo/useSceneTilt';
import { ROUTES } from '../routes';
import { PRIVACY_LINK } from '../features/child/ai/aiStrings'; // cards-spec (05)
import { SHOWCASE } from '../utils/assetUrl';
import { useDocumentLang } from '../i18n'; // i18n
import '../features/demo/demo.css';

const MAX_AUTO_RETRIES = 5;

const prefersReduced = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/** Split a headline into words so each can rise in turn (words, never letters: Arabic letters join). */
const Words = ({ text, animate }) =>
  text.split(' ').map((word, i, all) => (
    <Fragment key={`${word}-${i}`}>
      <span className={`${animate ? 'demo-rise ' : ''}inline-block`} style={{ '--i': i }}>
        {word}
      </span>
      {i < all.length - 1 ? ' ' : null}
    </Fragment>
  ));

/** Sparks for the press: four-point sun stars and leaf-green leaves, thrown out and faded. */
function burstSparks(btn) {
  if (!btn || prefersReduced()) return;
  const COUNT = 12;
  for (let i = 0; i < COUNT; i += 1) {
    const spark = document.createElement('span');
    spark.className = 'demo-spark';
    spark.dataset.kind = i % 2 ? 'leaf' : 'star';
    btn.appendChild(spark);
    const angle = (Math.PI * 2 * i) / COUNT + Math.random() * 0.4;
    const dist = 70 + Math.random() * 60;
    gsap.fromTo(
      spark,
      { x: 0, y: 0, scale: 0.4, opacity: 1, rotate: 0 },
      {
        x: Math.cos(angle) * dist,
        y: Math.sin(angle) * dist,
        scale: 0.8 + Math.random() * 0.8,
        opacity: 0,
        rotate: (i % 2 ? 160 : 120) * (Math.random() < 0.5 ? -1 : 1),
        duration: 0.7 + Math.random() * 0.3,
        ease: 'power2.out',
        onComplete: () => spark.remove(),
      },
    );
  }
}

const DemoLanding = () => {
  const navigate = useNavigate();
  const { startDemoSession } = useAuth();
  const [lang, setLang] = useState(readDemoLang);
  useDocumentLang(); // i18n: <html lang dir> follows the language, restored on leaving
  const [phase, setPhase] = useState('idle'); // idle | loading | problem
  const [problem, setProblem] = useState(null);
  const [countdown, setCountdown] = useState(0);
  const [intro, setIntro] = useState(true); // the headline rises once, never again on a language switch

  const clock = useClockPeriod();
  const [picked, setPicked] = useState(null); // a time chosen with the pill; null follows the device clock
  const time = picked || clock;
  const reduced = useReducedMotion();
  const finePointer = useMedia('(pointer: fine)');

  const ctaRef = useRef(null);
  const zoneRef = useRef(null);
  const retries = useRef(0);
  const controlRef = useRef(null); // the forest stage fills it: { walk, rt, hop, wave, look }
  const tiltRef = useRef(null);
  const specRef = useRef(null);
  const sceneRef = useRef(null);
  const h1Ref = useRef(null);
  const rootRef = useRef(null);
  const textRef = useRef(null);
  const visualRef = useRef(null);
  const flipFrom = useRef(null); // where the arch was before a language switch (for the glide)
  const [showMini, setShowMini] = useState(false); // phones: the small button once the big one scrolls away
  const t = COPY[lang];

  // Language switch: the text blurs out (160 ms), the page flips direction, the arch glides to its new
  // side (520 ms, by transform only) and the text blurs back in (260 ms). The headline does not rise again.
  const toggleLang = () => {
    const next = lang === 'ar' ? 'en' : 'ar';
    const text = textRef.current;
    const visual = visualRef.current;
    if (prefersReduced() || !text || !visual || !text.animate || flipFrom.current) {
      setLang(next);
      writeDemoLang(next);
      return;
    }
    flipFrom.current = visual.getBoundingClientRect();
    const out = text.animate(
      [{ filter: 'blur(0px)', opacity: 1 }, { filter: 'blur(6px)', opacity: 0.15 }],
      { duration: 160, easing: 'ease-in', fill: 'forwards' },
    );
    out.finished.then(() => {
      setLang(next);
      writeDemoLang(next);
    }).catch(() => {
      flipFrom.current = null;
    });
  };

  useLayoutEffect(() => {
    const from = flipFrom.current;
    const visual = visualRef.current;
    const text = textRef.current;
    if (!from || !visual || !text) return;
    flipFrom.current = null;
    const to = visual.getBoundingClientRect();
    const dx = from.left - to.left;
    const dy = from.top - to.top;
    text.getAnimations().forEach((a) => a.cancel());
    text.animate(
      [{ filter: 'blur(6px)', opacity: 0.15 }, { filter: 'blur(0px)', opacity: 1 }],
      { duration: 260, delay: 200, easing: 'ease-out', fill: 'backwards' },
    );
    if (Math.abs(dx) > 1 || Math.abs(dy) > 1) {
      visual.animate(
        [{ transform: `translate(${dx}px, ${dy}px)` }, { transform: 'translate(0, 0)' }],
        { duration: 520, easing: 'cubic-bezier(0.22, 1, 0.36, 1)' },
      );
    }
  }, [lang]);

  // Phones: when the big button scrolls out of view, a small one stays at the bottom.
  useEffect(() => {
    const btn = ctaRef.current;
    const root = rootRef.current;
    if (!btn || !root || !('IntersectionObserver' in window)) return undefined;
    const io = new IntersectionObserver(
      ([entry]) => setShowMini(!entry.isIntersecting && entry.boundingClientRect.top < 0),
      { root, threshold: 0 },
    );
    io.observe(btn);
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    const id = window.setTimeout(() => setIntro(false), 2600);
    return () => window.clearTimeout(id);
  }, []);

  useEffect(() => {
    const prevTitle = document.title;
    document.title = lang === 'ar' ? 'جرّب الصديق' : 'Try Al-Sadiq';
    return () => { document.title = prevTitle; };
  }, [lang]);

  // Tilt and drift follow the pointer (and the phone's tilt). Off under reduced motion, live.
  useSceneTilt({ enabled: !reduced, tiltRef, specRef, driftRef: h1Ref, controlRef, sceneRef });

  // Magnetic pull: on a mouse, the button leans toward the pointer (0.18 across, 0.28 down).
  useEffect(() => {
    const zone = zoneRef.current;
    const btn = ctaRef.current;
    if (!zone || !btn || reduced || !finePointer) return undefined;
    const qx = gsap.quickTo(btn, 'x', { duration: 0.5, ease: 'power3.out' });
    const qy = gsap.quickTo(btn, 'y', { duration: 0.5, ease: 'power3.out' });
    const move = (e) => {
      const r = btn.getBoundingClientRect();
      qx((e.clientX - (r.left + r.width / 2)) * 0.18);
      qy((e.clientY - (r.top + r.height / 2)) * 0.28);
    };
    const leave = () => { qx(0); qy(0); };
    zone.addEventListener('pointermove', move);
    zone.addEventListener('pointerleave', leave);
    return () => {
      zone.removeEventListener('pointermove', move);
      zone.removeEventListener('pointerleave', leave);
      gsap.killTweensOf(btn);
      gsap.set(btn, { x: 0, y: 0 });
    };
  }, [reduced, finePointer]);

  // Where the CTA is on screen (Sadiq glances at it).
  const ctaPoint = useCallback(() => {
    const r = ctaRef.current?.getBoundingClientRect();
    return r ? { x: r.left + r.width / 2, y: r.top + r.height / 2 } : null;
  }, []);

  const lookAtCta = useCallback(() => {
    const p = ctaPoint();
    const scene = sceneRef.current?.getBoundingClientRect();
    if (p && scene) controlRef.current?.look({ x: p.x - scene.left, y: p.y - scene.top }, 2.4);
  }, [ctaPoint]);

  // The breathing ring ends for good at the first hover or focus.
  const settleCta = useCallback(() => {
    if (ctaRef.current) ctaRef.current.dataset.touched = 'true';
    lookAtCta();
  }, [lookAtCta]);

  // Hovering step 1 of the judges card pulses the button's ring once.
  const pulseCta = useCallback(() => {
    const btn = ctaRef.current;
    if (!btn || prefersReduced()) return;
    btn.dataset.pulse = 'true';
    window.setTimeout(() => { delete btn.dataset.pulse; }, 1100);
  }, []);

  const shakeCta = useCallback(() => {
    const btn = ctaRef.current;
    if (!btn || prefersReduced()) return;
    btn.classList.remove('demo-shake');
    void btn.offsetWidth; // restart the animation if it is still running
    btn.classList.add('demo-shake');
  }, []);

  const begin = useCallback(async ({ auto = false, fromScene = false } = {}) => {
    if (!auto) {
      retries.current = 0;
      if (!fromScene) {
        burstSparks(ctaRef.current);
        navigator.vibrate?.(10);
      }
    }
    if (SHOWCASE) {
      // Showcase build: there is no server to lease a demo family from.
      setProblem({ kind: 'showcase', ar: COPY.ar.showcaseNote, en: COPY.en.showcaseNote });
      setPhase('problem');
      setCountdown(0);
      return;
    }
    setPhase('loading');
    setProblem(null);
    try {
      const payload = await startOrRestartDemo();
      await startDemoSession(payload, 'child');
      // The arch swells and softens under a wall-coloured veil, then the child screen takes over.
      const wall = rootRef.current ? getComputedStyle(rootRef.current).getPropertyValue('--wall-m').trim() : '';
      const win = sceneRef.current;
      if (win?.animate && !prefersReduced()) {
        win.animate(
          [{ scale: 1, filter: 'blur(0px)' }, { scale: 1.06, filter: 'blur(6px)' }],
          { duration: 450, easing: 'ease-in', fill: 'forwards' },
        );
      }
      await showVeil(wall);
      navigate(ROUTES.CHILD_HOME, { replace: true });
    } catch (err) {
      hideVeil();
      const info = describeDemoError(err);
      setProblem(info);
      setPhase('problem');
      shakeCta();
      setCountdown(info.kind === 'busy' && retries.current < MAX_AUTO_RETRIES
        ? Math.min(Math.max(info.retryAfter, 5), 30)
        : 0);
    }
  }, [navigate, shakeCta, startDemoSession]);

  const beginFromScene = useCallback(() => begin({ fromScene: true }), [begin]);

  // Busy rooms: count down, then try again by ourselves a few times.
  useEffect(() => {
    if (phase !== 'problem' || countdown <= 0) return undefined;
    const id = window.setTimeout(() => {
      if (countdown === 1) {
        retries.current += 1;
        begin({ auto: true });
      } else {
        setCountdown(countdown - 1);
      }
    }, 1000);
    return () => window.clearTimeout(id);
  }, [phase, countdown, begin]);

  const loading = phase === 'loading';
  const otherLang = lang === 'ar' ? 'en' : 'ar';

  return (
    <div
      ref={rootRef}
      dir={t.dir}
      lang={t.lang}
      data-time={time}
      className="demo-landing fixed inset-0 overflow-y-auto overflow-x-hidden"
    >
      <div className="demo-shell">
        {/* Header */}
        <header className="demo-header">
          <div className="demo-header-id flex min-w-0 items-center gap-3">
            <span className="demo-logo" aria-hidden="true">
              <MoonStar className="h-6 w-6" strokeWidth={1.75} />
            </span>
            {/* Phones get the short name so the header fits 360px in both languages. */}
            <span className="demo-brand truncate whitespace-nowrap">
              <span className="sm:hidden">{t.brandShort}</span>
              <span className="hidden sm:inline">{t.brand}</span>
            </span>
          </div>
          <div className="demo-header-pills flex shrink-0 items-center gap-2">
            <TimePill t={t} now={clock} picked={picked} onPick={setPicked} />
            <SoundPill t={t} time={time} />
            <Link to={SHOWCASE ? '/' : ROUTES.LOGIN} className="demo-pill demo-login-head">
              <LogIn className="demo-login-icon h-4 w-4" strokeWidth={2} aria-hidden="true" />
              <span className="hidden sm:inline">{SHOWCASE ? t.showcaseLink : t.login}</span>
              <span className="sr-only sm:hidden">{SHOWCASE ? t.showcaseLink : t.login}</span>
            </Link>
            <button
              type="button"
              className="demo-seg"
              data-lang={lang}
              onClick={toggleLang}
              aria-label={t.toggleLabel}
              lang={otherLang}
              dir="ltr"
            >
              <span className="demo-seg-thumb" aria-hidden="true" />
              <span className="demo-seg-opt" lang="ar" data-on={lang === 'ar'} aria-hidden="true">ع</span>
              <span className="demo-seg-opt" lang="en" data-on={lang === 'en'} aria-hidden="true">EN</span>
            </button>
          </div>
        </header>

        <main className="demo-grid">
          {/* The headline, the button and the problem card. On phones the scene sits above them. */}
          <div ref={textRef} className="demo-text">
            <h1 ref={h1Ref} className="demo-h1">
              <Words text={t.headline} animate={intro} />
            </h1>

            <div ref={zoneRef} className="demo-cta-zone">
              <div className="demo-land">
                <button
                  ref={ctaRef}
                  type="button"
                  className="demo-cta"
                  onClick={() => { if (!loading) begin(); }}
                  onPointerEnter={settleCta}
                  onFocus={settleCta}
                  aria-busy={loading}
                  data-pressed={loading}
                  data-loading={loading}
                  onAnimationEnd={(e) => { if (e.animationName === 'demo-shake') e.currentTarget.classList.remove('demo-shake'); }}
                >
                  <span className="demo-cta-stack">
                    <span className="demo-cta-label" data-on={!loading}>{t.cta}</span>
                    <span className="demo-cta-label" data-on={loading} aria-hidden={!loading}>{t.ctaLoading}</span>
                  </span>
                  <span className="demo-cta-shimmer" aria-hidden="true" />
                </button>
              </div>
            </div>

            <p className="demo-sub demo-rise" style={{ '--i': 6 }}>
              {t.sub}
            </p>

            {phase === 'problem' && problem ? (
              <div role="alert" className="demo-problem demo-pop">
                <p className="demo-problem-title">
                  {problem.kind === 'showcase' ? t.showcaseTitle : problem.kind === 'busy' ? t.busyTitle : t.errorTitle}
                </p>
                <p className="leading-7">{problem[lang]}</p>
                <div className="flex flex-wrap items-center gap-3">
                  {problem.kind === 'showcase' ? null : (
                    <button type="button" className="demo-pill" onClick={() => begin()}>
                      {t.retry}
                    </button>
                  )}
                  {countdown > 0 ? (
                    <span className="text-sm font-semibold text-[color:var(--ink-soft)]">
                      {t.retryIn(countdown)}
                    </span>
                  ) : null}
                </div>
              </div>
            ) : null}
          </div>

          {/* The picture: an arch window onto the forest. */}
          <div ref={visualRef} className="demo-visual">
            <div className="demo-tilt-host">
              <Spill time={time} />
              <div ref={tiltRef} className="demo-tilt">
                <div ref={sceneRef} className="demo-window">
                  <DemoHeroScene
                    t={t}
                    time={time}
                    forcedTime={picked}
                    onStart={beginFromScene}
                    busy={loading}
                    controlRef={controlRef}
                    ctaPoint={ctaPoint}
                  />
                  <span ref={specRef} className="demo-spec" aria-hidden="true" />
                </div>
              </div>
            </div>
          </div>

          <section aria-labelledby="demo-judges" className="demo-judges demo-card-in">
            <h2 id="demo-judges" className="demo-judges-title">
              {t.judgesTitle}
            </h2>
            <div className="demo-steps">
              <svg className="demo-path" viewBox="0 0 36 100" preserveAspectRatio="none" aria-hidden="true">
                <path d="M18 0 C 4 22, 32 28, 18 50 S 4 78, 18 100" />
              </svg>
              <ol>
                {t.steps.map((step, i) => (
                  <li
                    // Keyed by position: a language switch must not remount the steps (the badges would pop again).
                    key={`step-${i}`}
                    onPointerEnter={i === 0 ? pulseCta : undefined}
                    onPointerDown={i === 0 ? pulseCta : undefined}
                  >
                    <span className="demo-step-no" style={{ '--n': i }} aria-hidden="true">
                      {lang === 'ar' ? ['١', '٢', '٣'][i] : i + 1}
                    </span>
                    <div>
                      <p className="demo-step-title">{step.title}</p>
                      <p className="demo-step-body">{step.body}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
            <p className="demo-privacy">
              <ShieldCheck className="h-5 w-5 shrink-0" strokeWidth={2} aria-hidden="true" />
              {t.privacy}
            </p>
          </section>
        </main>

        <footer className="demo-footer">
          <Link to={ROUTES.LOGIN} className="demo-pill demo-login-foot">
            <LogIn className="h-4 w-4" strokeWidth={2} aria-hidden="true" />
            {t.login}
          </Link>
          <p>{t.foot}</p>
          {/* cards-spec (05) section 5: privacy link on the landing page */}
          <Link to={`${ROUTES.PRIVACY}?lang=${lang}`} className="demo-privacy-link" data-testid="landing-privacy-link">
            {PRIVACY_LINK[lang]}
          </Link>
        </footer>
      </div>

      {/* Phones: the big button has scrolled away, so a small one stays within reach. */}
      <button
        type="button"
        className="demo-cta demo-mini"
        data-show={showMini ? 'true' : 'false'}
        data-loading={loading}
        tabIndex={showMini ? 0 : -1}
        aria-hidden={!showMini}
        onClick={() => { if (!loading) begin(); }}
      >
        <span className="demo-cta-stack">
          <span className="demo-cta-label" data-on={!loading}>{t.cta}</span>
          <span className="demo-cta-label" data-on={loading} aria-hidden={!loading}>{t.ctaLoading}</span>
        </span>
        <span className="demo-cta-shimmer" aria-hidden="true" />
      </button>
    </div>
  );
};

export default DemoLanding;
