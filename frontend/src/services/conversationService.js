import api from './api';

/**
 * Start a session. textOnly asks for a chat without voice (the app offers it when the
 * voice is resting). The answer carries voice_mode, notice, max_seconds, session_ends_at.
 */
export const startSession = async ({ textOnly = false } = {}) => {
    const { data } = await api.post(
        '/api/conversation/sessions/',
        textOnly ? { text_only: true } : {},
    );
    return data;
};

export const endSession = async (sessionId) => {
    const { data } = await api.post(`/api/conversation/sessions/${sessionId}/end/`);
    return data;
};
