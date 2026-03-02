import axios from 'axios';

// TODO: Move base URL to an env variable (import.meta.env.VITE_API_URL)
const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
});

// --- Request interceptor: attach access token ---
apiClient.interceptors.request.use((config) => {
  // TODO: Read access token from authStore (Zustand) or localStorage
  // const token = useAuthStore.getState().accessToken;
  // if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// --- Response interceptor: handle token refresh on 401 ---
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      // TODO: Call POST /auth/refresh with the stored refresh token
      // TODO: Update authStore with the new access token
      // TODO: Retry the original request with the new token
      // TODO: If refresh fails, call authStore.logout() and redirect to /login
    }
    return Promise.reject(error);
  },
);

export default apiClient;
