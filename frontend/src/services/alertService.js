import api from './api';

export const fetchAlerts = async () => {
    const { data } = await api.get('/api/alerts/');
    return data;
};

export const markAlertRead = async (id) => {
    const { data } = await api.patch(`/api/alerts/${id}/read/`);
    return data;
};
