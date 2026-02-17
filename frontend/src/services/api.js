import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (!window.location.pathname.includes('/login')) {
         window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const auth = {
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
};

export const devices = {
  list: (params) => api.get('/devices', { params }),
  get: (id) => api.get(`/devices/${id}`),
  telemetry: (id, params) => api.get(`/devices/${id}/telemetry`, { params }),
  properties: (id) => api.get(`/devices/${id}/properties`),
};

export const rules = {
  list: (params) => api.get('/rules', { params }),
  create: (data) => api.post('/rules', data),
  update: (id, data) => api.patch(`/rules/${id}`, data),
  delete: (id) => api.delete(`/rules/${id}`),
};

export const alerts = {
  list: (params) => api.get('/alerts', { params }),
  acknowledge: (id) => api.patch(`/alerts/${id}/acknowledge`),
  resolve: (id) => api.patch(`/alerts/${id}/resolve`),
};

export const analytics = {
  jobs: (params) => api.get('/analytics/jobs', { params }),
  start: (data) => api.post('/analytics/jobs', data),
  models: () => api.get('/analytics/models'),
};

export const reports = {
  list: (params) => api.get('/reports', { params }),
  generate: (data) => api.post('/reports', data),
};

export default api;
