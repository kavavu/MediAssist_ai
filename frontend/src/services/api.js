/**
 * Axios instance for all API calls to the backend.
 * 
 * SECURITY & STABILITY FEATURES:
 * - baseURL is "/api" so requests go to same origin (Vite proxies /api → backend:5000).
 * - Every request automatically gets Authorization: Bearer <token> if user is logged in.
 * - Response interceptor handles 401 (expired/invalid JWT) by clearing session and redirecting to login.
 * - Request deduplication: same pending request won't be fired twice.
 * - Network error handling with user-friendly messages.
 * - 30-second timeout prevents hanging requests.
 */
import axios from "axios";
import { logout } from "./auth.js";
import { reconnectSocket } from "./socket.js";

const api = axios.create({
  baseURL: "/api",
  timeout: 30000, // 30s global timeout to prevent hanging requests
  headers: {
    "Content-Type": "application/json",
  },
});

// Track pending requests for deduplication
const pendingRequests = new Map();

/**
 * Generate a unique key for a request to enable deduplication.
 * Same method + URL + params + body = same key.
 */
function getRequestKey(config) {
  const { method, url, params, data } = config;
  return `${method}:${url}:${JSON.stringify(params || {})}:${JSON.stringify(data || {})}`;
}

// Attach JWT to every request so protected endpoints work
api.interceptors.request.use(
  (config) => {
    const token = window.localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Request deduplication for GET requests
    if (config.method?.toLowerCase() === "get" && config.dedupe !== false) {
      const key = getRequestKey(config);
      if (pendingRequests.has(key)) {
        // Return the existing promise instead of making a new request
        config.adapter = () => pendingRequests.get(key);
      } else {
        const promise = new Promise((resolve, reject) => {
          config._resolveDuplicate = resolve;
          config._rejectDuplicate = reject;
        });
        pendingRequests.set(key, promise);
        config._dedupeKey = key;
      }
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle 401 responses globally to prevent infinite loops and stale sessions
api.interceptors.response.use(
  (response) => {
    // Clean up deduplication tracking on success
    const key = response.config._dedupeKey;
    if (key) {
      pendingRequests.delete(key);
    }
    return response;
  },
  (error) => {
    // Clean up deduplication tracking on error
    const key = error.config?._dedupeKey;
    if (key) {
      pendingRequests.delete(key);
    }
    
    // Handle network errors gracefully
    if (!error.response) {
      // Network error or timeout — attach a friendly message
      error.isNetworkError = true;
      error.userMessage = "Network error. Please check your connection and try again.";
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
    
    // Attach user-friendly error messages for common status codes
    if (error.response.status === 403) {
      error.userMessage = "You don't have permission to perform this action.";
    } else if (error.response.status === 404) {
      error.userMessage = "The requested resource was not found.";
    } else if (error.response.status === 422) {
      error.userMessage = "Invalid input. Please check your data and try again.";
    } else if (error.response.status >= 500) {
      error.userMessage = "Server error. Please try again later.";
    }

    return Promise.reject(error);
  }
);

export default api;
