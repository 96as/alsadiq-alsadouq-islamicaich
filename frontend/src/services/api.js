import axios from 'axios';

// Axios Instance
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Showcase build (VITE_SHOWCASE=1): there is no backend. Refuse every request up front.
if (import.meta.env.VITE_SHOWCASE === '1') {
    api.interceptors.request.use(() => Promise.reject(new Error('Showcase build: no backend calls')));
}

const PUBLIC_AUTH_PATHS = [
    '/api/auth/login/',
    '/api/auth/register/parent/',
    '/api/auth/token/refresh/',
    '/api/auth/password-reset/',
    '/api/auth/password-reset/confirm/',
];

const isPublicAuthRequest = (url = '') => {
    try {
        const path = new URL(url, API_BASE_URL).pathname;
        return PUBLIC_AUTH_PATHS.includes(path);
    } catch {
        return PUBLIC_AUTH_PATHS.some((path) => url.includes(path));
    }
};

// Request Interceptor — attach JWT token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token && !isPublicAuthRequest(config.url)) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response Interceptor — handle 401 + refresh
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach(({ resolve, reject }) => {
        if (error) {
            reject(error);
        } else {
            resolve(token);
        }
    });
    failedQueue = [];
};

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Only attempt refresh on 401 and if we haven't already retried
        if (error.response?.status !== 401 || originalRequest._retry) {
            return Promise.reject(error);
        }

        // Never refresh auth endpoints that should surface their own errors
        if (isPublicAuthRequest(originalRequest.url)) {
            return Promise.reject(error);
        }

        // If already refreshing, queue this request
        if (isRefreshing) {
            return new Promise((resolve, reject) => {
                failedQueue.push({ resolve, reject });
            }).then((token) => {
                originalRequest.headers.Authorization = `Bearer ${token}`;
                return api(originalRequest);
            });
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (!refreshToken) {
                throw new Error('No refresh token');
            }

            const { data } = await axios.post(`${API_BASE_URL}/api/auth/token/refresh/`, {
                refresh: refreshToken,
            });

            localStorage.setItem('access_token', data.access);
            // The server rotates refresh tokens and blacklists the old one; keep the new one or the
            // next refresh fails with a blacklisted token and the user is signed out.
            if (data.refresh) localStorage.setItem('refresh_token', data.refresh);
            processQueue(null, data.access);

            originalRequest.headers.Authorization = `Bearer ${data.access}`;
            return api(originalRequest);
        } catch (refreshError) {
            processQueue(refreshError, null);
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            return Promise.reject(refreshError);
        } finally {
            isRefreshing = false;
        }
    }
);

export default api;
