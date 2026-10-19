/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
    loginUser,
    registerUser,
    logout as logoutService,
    getUserFromToken,
    fetchProfile,
} from '../services/authService';
import {
    activateDemoRole,
    clearDemoSession,
    installDemoPayload,
} from '../services/demoService';

const AuthContext = createContext(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(() => getUserFromToken());
    const [loading, setLoading] = useState(() => Boolean(getUserFromToken()));

    const refreshProfile = useCallback(async (baseUser = null) => {
        const tokenUser = baseUser || getUserFromToken();
        if (!tokenUser) return;
        try {
            const profileData = await fetchProfile();
            setUser((currentUser) => ({
                ...(currentUser || {}),
                ...tokenUser,
                email: profileData.email,
                first_name: profileData.first_name,
                last_name: profileData.last_name,
                profile: profileData.profile,
                children: profileData.children,
            }));
        } catch {
            setUser((currentUser) => currentUser || tokenUser);
        }
    }, []);

    useEffect(() => {
        let mounted = true;
        const savedUser = getUserFromToken();
        if (savedUser) {
            fetchProfile()
                .then((profileData) => {
                    if (!mounted) return;
                    setUser({
                        ...savedUser,
                        email: profileData.email,
                        first_name: profileData.first_name,
                        last_name: profileData.last_name,
                        profile: profileData.profile,
                        children: profileData.children,
                    });
                })
                .catch(() => {})
                .finally(() => {
                    if (mounted) setLoading(false);
                });
        }
        return () => {
            mounted = false;
        };
    }, []);

    const login = async (username, password) => {
        await loginUser(username, password);
        // A real sign-in ends any demo in this browser (no demo bar, no role flip).
        clearDemoSession();
        const tokenUser = getUserFromToken();
        if (!tokenUser) {
            throw new Error('Login succeeded but user session could not be initialized. Please try again.');
        }

        try {
            const profileData = await fetchProfile();
            const fullUser = {
                ...tokenUser,
                email: profileData.email,
                first_name: profileData.first_name,
                last_name: profileData.last_name,
                profile: profileData.profile,
                children: profileData.children,
            };
            setUser(fullUser);
            return fullUser;
        } catch {
            // Profile fetch failed — fall back to JWT-only data
            setUser(tokenUser);
            return tokenUser;
        }
    };

    const register = async (userData) => {
        return await registerUser(userData);
    };

    const logout = async () => {
        try {
            await logoutService();
        } catch {
            // Even if server-side blacklist fails, clear local state
        }
        clearDemoSession();
        setUser(null);
    };

    // Demo only: adopt the tokens from /api/demo/start (or /reset) for one role.
    const adoptTokens = async () => {
        const tokenUser = getUserFromToken();
        if (!tokenUser) {
            throw new Error('Demo session could not be initialized.');
        }
        try {
            const profileData = await fetchProfile();
            const fullUser = {
                ...tokenUser,
                email: profileData.email,
                first_name: profileData.first_name,
                last_name: profileData.last_name,
                profile: profileData.profile,
                children: profileData.children,
            };
            setUser(fullUser);
            return fullUser;
        } catch {
            setUser(tokenUser);
            return tokenUser;
        }
    };

    const startDemoSession = async (payload, role = 'child') => {
        installDemoPayload(payload, role);
        return adoptTokens();
    };

    const switchDemoRole = async (role) => {
        if (!activateDemoRole(role)) {
            throw new Error('No demo session to switch.');
        }
        return adoptTokens();
    };

    const value = {
        user,
        loading,
        login,
        register,
        refreshProfile,
        logout,
        startDemoSession,
        switchDemoRole,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};
