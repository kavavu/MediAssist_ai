/**
 * Socket.IO client for MediAssist AI real-time features.
 *
 * - Initializes socket connection on first access
 * - Sends JWT token for authentication
 * - Handles reconnect with exponential backoff
 * - Provides helper functions for room management
 * - Safe event handling with error boundaries
 * - Connection state tracking for UI feedback
 *
 * Usage:
 *   import { getSocket, joinConsultationRoom, leaveConsultationRoom, joinDoctorRoom } from "./socket.js";
 *
 *   const socket = getSocket();
 *   socket.on("new_message", (data) => { ... });
 *   socket.on("consultation_updated", (data) => { ... });
 */
import { io } from "socket.io-client";

const SOCKET_URL = window.location.origin;

let socket = null;
let _connectionState = "offline";
const _stateListeners = new Set();

function getToken() {
  return window.localStorage.getItem("access_token");
}

function _notifyStateChange(state) {
  _connectionState = state;
  _stateListeners.forEach((cb) => {
    try {
      cb(state);
    } catch {
      /* ignore listener errors */
    }
  });
}

export function subscribeSocketState(callback) {
  _stateListeners.add(callback);
  // Immediately notify with current state
  callback(_connectionState);
  return () => {
    _stateListeners.delete(callback);
  };
}

function createSocket() {
  const token = getToken();

  // Do NOT connect if there is no valid token
  if (!token) {
    _notifyStateChange("offline");
    return null;
  }

  const s = io(SOCKET_URL, {
    transports: ["websocket", "polling"],
    autoConnect: true,
    reconnection: true,
    reconnectionAttempts: 10,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    randomizationFactor: 0.5,
    auth: {
      token,
    },
  });

  s.on("connect", () => {
    _notifyStateChange("connected");
    // Re-join doctor room on connect/reconnect if user is a doctor
    const raw = window.localStorage.getItem("current_user");
    if (raw) {
      try {
        const user = JSON.parse(raw);
        if (user?.role === "doctor" && user?.id) {
          s.emit("join_doctor_room", { doctor_id: user.id });
        }
      } catch {
        /* ignore parse error */
      }
    }
  });

  s.on("disconnect", (reason) => {
    _notifyStateChange("offline");
    /* disconnect is normal, but if it was a server-initiated disconnect we may need to reconnect */
    if (reason === "io server disconnect") {
      // Server forced disconnect — try reconnecting after a short delay
      setTimeout(() => {
        try {
          s.connect();
        } catch {
          /* ignore */
        }
      }, 1000);
    }
  });

  s.on("connect_error", (err) => {
    _notifyStateChange("reconnecting");
    /* connection errors are expected during network issues */
    // If auth error, token may be expired — let the API interceptor handle it
    if (err?.message?.includes("auth") || err?.message?.includes("unauthorized")) {
      // Token likely expired — disconnect and let API interceptor redirect
      try {
        s.disconnect();
      } catch {
        /* ignore */
      }
    }
  });

  s.on("reconnect", (attemptNumber) => {
    _notifyStateChange("connected");
    /* reconnect handled by connect handler */
  });

  s.on("reconnect_attempt", (attemptNumber) => {
    _notifyStateChange("reconnecting");
    /* reconnection in progress */
  });

  s.on("reconnect_failed", () => {
    _notifyStateChange("offline");
    /* all reconnection attempts exhausted */
  });

  return s;
}

// Lazy initialization — socket is created on first access
export function getSocket() {
  if (!socket) {
    socket = createSocket();
  }
  return socket;
}

// Re-initialize socket (e.g., after login/logout)
export function reconnectSocket() {
  if (socket) {
    try {
      socket.disconnect();
    } catch {
      /* ignore */
    }
    socket = null;
  }
  _notifyStateChange("offline");
  return getSocket();
}

// Room management helpers
export function joinConsultationRoom(consultationId) {
  try {
    const s = getSocket();
    if (!s) return;
    s.emit("join_consultation", { consultation_id: consultationId });
  } catch (err) {
    /* ignore */
  }
}

export function leaveConsultationRoom(consultationId) {
  try {
    const s = getSocket();
    if (!s) return;
    s.emit("leave_consultation", { consultation_id: consultationId });
  } catch (err) {
    /* ignore */
  }
}

export function joinDoctorRoom(doctorId) {
  try {
    const s = getSocket();
    if (!s) return;
    s.emit("join_doctor_room", { doctor_id: doctorId });
  } catch (err) {
    /* ignore */
  }
}

export function leaveDoctorRoom(doctorId) {
  try {
    const s = getSocket();
    if (!s) return;
    s.emit("leave_consultation", { consultation_id: doctorId }); // server maps this to doctor room internally
  } catch (err) {
    /* ignore */
  }
}

// Connection status helpers
export function getSocketConnectionStatus() {
  const s = getSocket();
  if (!s) return "offline";
  if (s.connected) return "connected";
  if (s.io?.reconnecting) return "reconnecting";
  return "offline";
}

// NOTE: Do NOT export the raw socket variable directly — it may be null
// before getSocket() is called. Always use getSocket() for reliable access.
