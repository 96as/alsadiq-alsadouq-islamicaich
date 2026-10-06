import api from './api';
import { jwtDecode } from 'jwt-decode';

// ── Token Helpers ──

export const getStoredTokens = () => ({
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
});

export const storeTokens = (access, refresh) => {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
};

export const clearTokens = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
};

/**
 * Decode the access token to extract user info.
 * Returns null if token is missing or expired.
 */
export const getUserFromToken = () => {
    const { access } = getStoredTokens();
    if (!access) return null;

    try {
        const decoded = jwtDecode(access);

        if (decoded.exp * 1000 < Date.now()) {
            return null;
        }

        return {
            user_id: decoded.user_id,
            username: decoded.username,
            is_parent: decoded.is_parent,
            is_child: decoded.is_child,
        };
    } catch {
        return null;
    }
};

// ── API Calls ──

/**
 * POST /api/auth/login/
 * Returns: { access, refresh, user_id, username, is_parent, is_child }
 */
export const loginUser = async (username, password) => {
    const { data } = await api.post('/api/auth/login/', { username, password });
    storeTokens(data.access, data.refresh);
    return data;
};

/**
 * POST /api/auth/register/parent/
 */
export const registerUser = async (userData) => {
    const { data } = await api.post('/api/auth/register/parent/', userData);
    return data;
};

/**
 * POST /api/auth/token/refresh/
 */
export const refreshToken = async () => {
    const { refresh } = getStoredTokens();
    if (!refresh) throw new Error('No refresh token');

    const { data } = await api.post('/api/auth/token/refresh/', { refresh });
    localStorage.setItem('access_token', data.access);
    if (data.refresh) localStorage.setItem('refresh_token', data.refresh);
    return data;
};

/**
 * GET /api/auth/profile/
 */
export const fetchProfile = async () => {
    const { data } = await api.get('/api/auth/profile/');
    return data;
};

/**
 * PATCH /api/auth/profile/child/ — child updates nickname, birth year, language, profile icon.
 * @param {Record<string, unknown>} payload
 */
export const patchChildProfile = async (payload) => {
    const { data } = await api.patch('/api/auth/profile/child/', payload);
    return data;
};

/**
 * POST /api/auth/profile/child/password/ — child changes their own password.
 */
export const changeChildPassword = async (new_password) => {
    const { data } = await api.post('/api/auth/profile/child/password/', {
        new_password,
    });
    return data;
};

/**
 * POST /api/auth/children/ — parent creates a linked child account.
 */
export const createChild = async (payload) => {
    const { data } = await api.post('/api/auth/children/', payload);
    return data;
};

/**
 * GET /api/conversation/parent/children/:childId/summary/
 */
export const fetchParentChildSummary = async (childId) => {
    const { data } = await api.get(`/api/conversation/parent/children/${childId}/summary/`);
    return data;
};

/**
 * POST /api/auth/logout/
 * Blacklists the refresh token server-side, then clears local tokens.
 */
export const logout = async () => {
    const { refresh } = getStoredTokens();
    if (refresh) {
        try {
            await api.post('/api/auth/logout/', { refresh });
        } catch {
            // Even if blacklisting fails (e.g. token already expired),
            // we still clear local state below.
        }
    }
    clearTokens();
};

// ── Password Reset ──

/**
 * POST /api/auth/password-reset/
 * Request a password-reset email. Always returns 200 (no email enumeration).
 */
export const requestPasswordReset = async (email) => {
    const { data } = await api.post('/api/auth/password-reset/', { email });
    return data;
};

/**
 * POST /api/auth/password-reset/confirm/
 * Set a new password using the uid + token from the reset link.
 */
export const confirmPasswordReset = async (uid, token, new_password) => {
    const { data } = await api.post('/api/auth/password-reset/confirm/', {
        uid,
        token,
        new_password,
    });
    return data;
};
