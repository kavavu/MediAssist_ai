/**
 * Auth helpers: login, register, get current user, logout.
 * Session is stored in localStorage (access_token + current_user). Do not change key names.
 */
import api from "./api.js";
import { reconnectSocket } from "./socket.js";

const USER_KEY = "current_user";
const TOKEN_KEY = "access_token";

/** Read the logged-in user from localStorage (id, name, email, role). Returns null if not logged in. */
export function getCurrentUser() {
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

/** Save token and user after successful login. Used only by login(). */
export function setSession(token, user) {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  reconnectSocket();
  window.dispatchEvent(new Event("auth-change"));
}

/** Clear token and user (e.g. when user clicks Logout). */
export function logout() {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
  reconnectSocket();
  // Notify all tabs/components that auth state changed
  window.dispatchEvent(new Event("auth-change"));
}

/** POST /api/auth/login with email & password. Saves token and user, returns user. */
export async function login(email, password) {
  const res = await api.post("/auth/login", { email, password });
  const { access_token, user } = res.data;
  setSession(access_token, user);
  return user;
}

/** POST /api/auth/register with { name, email, password, role? }. Returns response data. */
export async function register(payload) {
  const res = await api.post("/auth/register", payload);
  return res.data;
}

