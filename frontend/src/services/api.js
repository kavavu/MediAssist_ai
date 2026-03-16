/**
 * Axios instance for all API calls to the backend.
 * - baseURL is "/api" so requests go to same origin (Vite proxies /api → backend:5000).
 * - Every request automatically gets Authorization: Bearer <token> if user is logged in.
 */
import axios from "axios";

const api = axios.create({
  baseURL: "/api",
});

// Attach JWT to every request so protected endpoints (predict, patient/*, doctor/*) work
api.interceptors.request.use((config) => {
  const token = window.localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;

