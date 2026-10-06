import api from './api';

export const fetchChildInsights = async (childId) => {
    const { data } = await api.get(`/api/reporting/insights/${childId}/`);
    return data;
};

export const fetchChildDashboard = async (childId) => {
    const { data } = await api.get(`/api/reporting/dashboard/${childId}/`);
    return data;
};
