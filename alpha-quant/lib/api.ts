import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
    timeout: 15000,
    headers: {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true', // Bypass Ngrok free-tier warning
    },
});

// Request Interceptor: Attach Token
api.interceptors.request.use(
    (config) => {
        if (typeof window !== 'undefined') {
            const token = localStorage.getItem('token');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response Interceptor: Handle 401
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            // Ignore 401s from Login Endpoint itself to avoid reload loop on wrong password
            if (error.config.url?.includes('/login')) {
                return Promise.reject(error);
            }

            if (typeof window !== 'undefined') {
                localStorage.removeItem('token');
                window.location.reload();
            }
        }
        return Promise.reject(error);
    }
);

export const apiService = {
    get: api.get,
    post: api.post,
    put: api.put,
    delete: api.delete,
    // Helper for consistent error handling if needed
    // ...
};

export default api;
