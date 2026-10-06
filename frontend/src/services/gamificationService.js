import api from './api';

export const fetchQuests = async () => {
    const { data } = await api.get('/api/gamification/quests/');
    return data;
};

export const completeQuest = async (progressId, proofNote = '') => {
    const { data } = await api.patch(
        `/api/gamification/quests/${progressId}/complete/`,
        proofNote ? { proof_note: proofNote } : {},
    );
    return data;
};

// Parent: list a linked child's quests (optionally filtered by status).
export const fetchChildQuestsAsParent = async (childId, status = '') => {
    const params = status ? { status } : {};
    const { data } = await api.get(
        `/api/gamification/parent/children/${childId}/quests/`,
        { params },
    );
    return data;
};

// Parent: approve or reject a quest awaiting verification.
export const verifyQuest = async (progressId, action) => {
    const { data } = await api.patch(
        `/api/gamification/parent/quests/${progressId}/verify/`,
        { action },
    );
    return data;
};

export const fetchBadges = async () => {
    const { data } = await api.get('/api/gamification/badges/');
    return data;
};

export const fetchLevel = async () => {
    const { data } = await api.get('/api/gamification/level/');
    return data;
};
