import axios from 'axios';

// Use relative /api so Vite proxy handles it regardless of port (3000 or 3001).
// In production, VITE_API_BASE_URL overrides this (e.g. https://your-backend.onrender.com/api)
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach JWT token from localStorage
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: redirect to /login on 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestUrl = error?.config?.url ?? '';
    const isAuthLoginRequest = typeof requestUrl === 'string' && requestUrl.includes('/auth/login');
    if (error.response && error.response.status === 401 && !isAuthLoginRequest) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
