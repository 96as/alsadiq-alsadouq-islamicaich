import { useSyncExternalStore } from 'react';
import api from './api';
import { getStoredTokens, storeTokens } from './authService';

/**
 * One-click demo ("Try Al-Sadiq").
 *
 * Everything here is inert unless the build sets VITE_DEMO_MODE=1 and the
 * backend runs with DEMO_MODE=1. A demo visit leases a synthetic family on the
 * server, which answers with a child token pair and a parent token pair for the
 * SAME child. We keep both pairs in localStorage ("demo_session") and copy the
 * active role's pair into the normal access_token / refresh_token keys, so the
 * rest of the app (axios interceptor, guards, AuthContext) works unchanged.
 */

export const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === '1';

const SESSION_KEY = 'demo_session';
const LANG_KEY = 'demo_lang';

// ── Stored session ──────────────────────────────────────────────────────────

export const readDemoSession = () => {
    try {
        const raw = localStorage.getItem(SESSION_KEY);
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
};

const writeDemoSession = (session) => {
    try {
        localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    } catch {
        // Storage can be blocked; the demo then lasts until the page closes.
    }
};

export const clearDemoSession = () => {
    try {
        localStorage.removeItem(SESSION_KEY);
    } catch {
        // ignore
    }
};

export const isDemoSession = () => DEMO_MODE && Boolean(readDemoSession());

/** 'child' or 'parent': the role whose tokens are currently active. */
export const activeDemoRole = () => readDemoSession()?.role || null;

// ── Language (shared by the landing page and the in-app banner) ─────────────

export const readDemoLang = () => {
    try {
        return localStorage.getItem(LANG_KEY) === 'en' ? 'en' : 'ar';
    } catch {
        return 'ar';
    }
};

const LANG_EVENT = 'demo-lang-change'; // qa: lets the nav and toasts follow a language toggle without a route change

export const writeDemoLang = (lang) => {
    try {
        localStorage.setItem(LANG_KEY, lang === 'en' ? 'en' : 'ar');
    } catch {
        // ignore
    }
    try {
        window.dispatchEvent(new Event(LANG_EVENT));
    } catch {
        // ignore
    }
};

const subscribeLang = (cb) => {
    window.addEventListener(LANG_EVENT, cb);
    window.addEventListener('storage', cb);
    return () => {
        window.removeEventListener(LANG_EVENT, cb);
        window.removeEventListener('storage', cb);
    };
};

/** The demo language as React state: re-renders when writeDemoLang runs anywhere in the app. */
export const useDemoLang = () => useSyncExternalStore(subscribeLang, readDemoLang, () => 'ar');

// ── Token handling ──────────────────────────────────────────────────────────

/**
 * Install a /demo/start (or /demo/reset) payload and activate one role.
 * Returns the active role's token pair.
 */
export const installDemoPayload = (payload, role = 'child') => {
    const pair = payload[role];
    storeTokens(pair.access, pair.refresh);
    writeDemoSession({
        role,
        child: payload.child,
        parent: payload.parent,
        family: payload.family,
        expires_in: payload.expires_in,
        started_at: Date.now(),
    });
    return pair;
};

/**
 * Make `role` the active role. The token the axios interceptor may have
 * refreshed for the current role is saved back first, so nothing is lost.
 */
export const activateDemoRole = (role) => {
    const session = readDemoSession();
    if (!session || !session[role]) return null;
    const current = getStoredTokens();
    if (session.role && current.access) {
        session[session.role] = {
            ...session[session.role],
            access: current.access,
            refresh: current.refresh || session[session.role].refresh,
        };
    }
    const pair = session[role];
    storeTokens(pair.access, pair.refresh);
    writeDemoSession({ ...session, role });
    return pair;
};

// ── API ─────────────────────────────────────────────────────────────────────

/**
 * POST /api/demo/start/
 * 201 payload, or a rejected axios error. A 503 body carries message_ar,
 * message_en and retry_after (seconds).
 */
export const startDemo = async () => {
    const { data } = await api.post('/api/demo/start/', {});
    return data;
};

/**
 * POST /api/demo/reset/ ("start over"). Wipes the visitor's own family and
 * re-seeds it. When the lease already ended the token is refused (401, or
 * 409 for a lease that lapses mid-request); callers then fall back to
 * startDemo().
 */
export const resetDemo = async () => {
    const { data } = await api.post('/api/demo/reset/', {});
    return data;
};

/**
 * The landing's "Try" button. A browser that still holds a family starts over
 * inside it instead of leasing a second one, so pressing Try again (or coming
 * back to the landing) never ties up more of the 8 families.
 */
export const startOrRestartDemo = async () => {
    if (readDemoSession() && activateDemoRole('child')) {
        try {
            return await resetDemo();
        } catch {
            // Lease ended or token refused: lease a fresh family below.
        }
    }
    return startDemo();
};

/**
 * "Start over" from inside a demo: wipe and re-seed this visitor's family, or lease a fresh
 * one when the lease already ended (401, 409, or no answer). Returns the payload for
 * AuthContext.startDemoSession. Other failures are thrown for describeDemoError.
 */
export const resetOrStartDemo = async () => {
    try {
        return await resetDemo();
    } catch (err) {
        const status = err?.response?.status;
        if (status === 409 || status === 401 || !err?.response) {
            return startDemo();
        }
        throw err;
    }
};

/**
 * Turn an axios error from startDemo/resetDemo into plain, bilingual copy.
 * kind: 'busy' | 'limit' | 'off' | 'network' | 'unknown'
 */
export const describeDemoError = (err) => {
    const status = err?.response?.status;
    const data = err?.response?.data || {};
    if (status === 503 && data.code === 'demo_busy') {
        return {
            kind: 'busy',
            ar: data.message_ar,
            en: data.message_en,
            retryAfter: Number(data.retry_after) || Number(err.response.headers?.['retry-after']) || 30,
        };
    }
    if (status === 429) {
        return {
            kind: 'limit',
            ar: 'جرّبت عدة مرات في وقت قصير. انتظر قليلًا ثم حاول من جديد.',
            en: 'Too many tries in a short time. Wait a little, then try again.',
            retryAfter: Number(err.response.headers?.['retry-after']) || 60,
        };
    }
    if (status === 404) {
        return {
            kind: 'off',
            ar: 'التجربة المفتوحة غير مفعّلة على هذا الخادم.',
            en: 'The open demo is not switched on for this server.',
            retryAfter: 0,
        };
    }
    if (!err?.response) {
        return {
            kind: 'network',
            ar: 'تعذّر الاتصال بالخادم. تحقّق من الإنترنت ثم حاول من جديد.',
            en: 'Could not reach the server. Check your connection and try again.',
            retryAfter: 0,
        };
    }
    return {
        kind: 'unknown',
        ar: 'حدث خطأ غير متوقع. حاول من جديد.',
        en: 'Something went wrong. Please try again.',
        retryAfter: 0,
    };
};
