import axios from 'axios';
import { config } from '../config';

const http = axios.create({
    baseURL: config.api.baseUrl,
    withCredentials: true,
});

http.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            try {
                await axios.post(`${config.api.baseUrl}/auth/refresh`, {}, { withCredentials: true });
                return http(originalRequest);
            } catch (err) {
                // If refresh fails, we might want to redirect to login or let the auth context handle it
                return Promise.reject(err);
            }
        }
        return Promise.reject(error);
    }
);

export default http;
