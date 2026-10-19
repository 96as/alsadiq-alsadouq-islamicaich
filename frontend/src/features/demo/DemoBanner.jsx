import { useEffect, useRef, useState } from 'react';
import { assetUrl } from '../../utils/assetUrl';
import { useNavigate } from 'react-router-dom';
import { LoaderCircle, RotateCcw, ShieldCheck, Users, Baby } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import {
  describeDemoError,
  isDemoSession,
  readDemoLang,
  readDemoSession,
  resetOrStartDemo,
} from '../../services/demoService';
import { COPY } from './copy';
import { ROUTES } from '../../routes';
import './demo.css';

/**
 * DemoBanner: the slim bar shown on the child and parent screens during a demo.
 *
 *   "عرض وليّ الأمر" flips to the parent dashboard for the SAME child (both token
 *   pairs came from one /api/demo/start, so no login happens). On the parent
 *   screen the same slot flips back to the child view.
 *   "ابدأ من جديد" wipes this visitor's family on the server and re-seeds it, then
 *   reloads the child screen. If the lease already ended it leases a new family.
 *
 * Renders nothing outside a demo session, so it is safe in the shared layout.
 */
const DemoBanner = () => {
  const navigate = useNavigate();
  const { user, switchDemoRole, startDemoSession } = useAuth();
  const [busy, setBusy] = useState(null); // 'switch' | 'reset' | null
  const [message, setMessage] = useState('');
  const lang = readDemoLang();
  const t = COPY[lang];

  useEffect(() => {
    if (!message) return undefined;
    const id = window.setTimeout(() => setMessage(''), 7000);
    return () => window.clearTimeout(id);
  }, [message]);

  // The demo family's history is Arabic inside the English app screens. This class lets
  // each paragraph take its direction from its own text (see demo.css), so Arabic lines
  // read right to left with their full stop and quotes at the right ends.
  const active = isDemoSession() && Boolean(user);
  useEffect(() => {
    if (!active) return undefined;
    const root = document.documentElement;
    root.classList.add('demo-session');
    return () => root.classList.remove('demo-session');
  }, [active]);

  // The server ends the demo tokens exactly when the lease ends. Know it here too, so
  // the bar offers a fresh demo instead of leaving the visitor on screens that 401.
  const session = active ? readDemoSession() : null;
  const endsAt = session?.started_at && session?.expires_in
    ? session.started_at + session.expires_in * 1000
    : null;
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!endsAt) return undefined;
    const left = endsAt - Date.now();
    if (left <= 0) return undefined;
    const id = window.setTimeout(() => setNow(Date.now()), Math.min(left + 50, 2147483647));
    return () => window.clearTimeout(id);
  }, [endsAt]);
  const expired = Boolean(endsAt) && now >= endsAt;

  // cards-spec (05) judge r2: publish the bar's height so fixed overlays at the top of the page (the permanent AI
  // chip) start below the bar instead of under it.
  const barRef = useRef(null);
  useEffect(() => {
    const el = barRef.current;
    if (!active || !el) return undefined;
    const root = document.documentElement;
    const publish = () => root.style.setProperty('--demo-bar-h', `${Math.ceil(el.getBoundingClientRect().height)}px`);
    publish();
    const ro = typeof ResizeObserver === 'function' ? new ResizeObserver(publish) : null;
    if (ro) ro.observe(el);
    return () => {
      if (ro) ro.disconnect();
      root.style.removeProperty('--demo-bar-h');
    };
  }, [active]);

  if (!active) return null;

  const inParentView = Boolean(user.is_parent);

  const flip = async () => {
    if (busy) return;
    setBusy('switch');
    try {
      const target = inParentView ? 'child' : 'parent';
      await switchDemoRole(target);
      // The role guard bounces the old route to the new role's home first. Wait for that,
      // then land the parent on this child's week (insights) instead of the bare list.
      await new Promise((resolve) => { window.setTimeout(resolve, 120); });
      navigate(target === 'parent' ? ROUTES.PARENT_INSIGHTS : ROUTES.CHILD_HOME);
    } catch {
      setMessage(lang === 'ar' ? 'تعذّر التبديل. حاول من جديد.' : 'Could not switch. Please try again.');
    } finally {
      setBusy(null);
    }
  };

  const startOver = async () => {
    if (busy) return;
    setBusy('reset');
    try {
      const payload = await resetOrStartDemo();
      await startDemoSession(payload, 'child');
      // A full load gives every screen a clean slate (chat, level, summaries).
      window.location.assign(assetUrl(ROUTES.CHILD_HOME));
    } catch (err) {
      const info = describeDemoError(err);
      setMessage(info[lang]);
      setBusy(null);
    }
  };

  return (
    <div ref={barRef} className="demo-banner" dir={t.dir} lang={t.lang} role="region" aria-label={t.bannerAria}>
      <span className="demo-badge">
        <ShieldCheck className="h-3.5 w-3.5" strokeWidth={2.5} aria-hidden="true" />
        {t.demoBadge}
      </span>
      {expired ? (
        <span role="status" className="text-sm font-semibold">{t.ended}</span>
      ) : (
        <span className="hidden text-sm font-semibold opacity-85 md:inline">{t.bannerHint}</span>
      )}

      <span className="flex-1" />

      {expired ? null : (
        <button type="button" className="demo-banner-btn" onClick={flip} disabled={Boolean(busy)} data-primary="true">
          <span className="demo-banner-face">
            {busy === 'switch' ? (
              <LoaderCircle className="demo-spin h-4 w-4" strokeWidth={2.5} aria-hidden="true" />
            ) : inParentView ? (
              <Baby className="h-4 w-4" strokeWidth={2.25} aria-hidden="true" />
            ) : (
              <Users className="h-4 w-4" strokeWidth={2.25} aria-hidden="true" />
            )}
            {inParentView ? t.childView : t.parentView}
          </span>
        </button>
      )}

      <button
        type="button"
        className="demo-banner-btn"
        onClick={startOver}
        disabled={Boolean(busy)}
        data-primary={expired ? 'true' : undefined}
      >
        <span className="demo-banner-face">
          {busy === 'reset' ? (
            <LoaderCircle className="demo-spin h-4 w-4" strokeWidth={2.5} aria-hidden="true" />
          ) : (
            <RotateCcw className="h-4 w-4" strokeWidth={2.25} aria-hidden="true" />
          )}
          {busy === 'reset' ? t.working : expired ? t.newDemo : t.startOver}
        </span>
      </button>

      {message ? (
        <p
          role="alert"
          className="demo-pop absolute inset-x-3 top-[calc(100%+8px)] z-50 rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-[#0f2d1c] shadow-lg"
        >
          {message}
        </p>
      ) : null}
    </div>
  );
};

export default DemoBanner;
