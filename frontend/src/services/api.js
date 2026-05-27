/**
 * Axios instance for all API calls to the backend.
 * - baseURL is "/api" so requests go to same origin (Vite proxies /api → backend:5000).
 * - Every request automatically gets Authorization: Bearer <token> if user is logged in.
 * - Response interceptor handles 401 (expired/invalid JWT) by clearing session and redirecting to login.
 * - Enhanced with request/response logging suppression for production stability.
 */
import axios from "axios";
import { logout } from "./auth.js";
import { reconnectSocket } from "./socket.js";

const api = axios.create({
  baseURL: "/api",
  timeout: 30000, // 30s global timeout to prevent hanging requests
});

// Attach JWT to every request so protected endpoints work
api.interceptors.request.use(
  (config) => {
    const token = window.localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle 401 responses globally to prevent infinite loops and stale sessions
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle network errors gracefully
    if (!error.response) {
      // Network error or timeout — let the caller handle it
      return Promise.reject(error);
    }

    if (error.response.status === 401) {
      const token = window.localStorage.getItem("access_token");
      // Only act if we actually had a token (avoid redirecting on public 401s)
      if (token) {
        // Prevent infinite redirect loops: only redirect if not already on /login
        const isLoginPage = window.location.pathname === "/login";
        if (!isLoginPage) {
          logout();
          reconnectSocket();
          window.location.replace("/login");
        }
      }
    }

    // Handle 403 forbidden — could be role mismatch, just reject
    // Handle 500 errors — just reject, let components show fallback UI
    return Promise.reject(error);
  }
);

export default api;
