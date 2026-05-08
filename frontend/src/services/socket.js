/**
 * Socket.IO client for MediAssist AI real-time features.
 *
 * - Initializes socket connection on first import
 * - Sends JWT token for authentication
 * - Handles reconnect with exponential backoff
 * - Provides helper functions for room management
 * - Safe event handling with error boundaries
 *
 * Usage:
 *   import { getSocket, joinConsultationRoom, leaveConsultationRoom, joinDoctorRoom } from "./socket";
 *
 *   const socket = getSocket();
 *   socket.on("new_message", (data) => { ... });
 *   socket.on("consultation_updated", (data) => { ... });
 */
import { io } from "socket.io-client";

const SOCKET_URL = window.location.origin; // Same origin (Vite proxies /socket.io)

let socket = null;

function getToken() {
  return window.localStorage.getItem("access_token");
}

function createSocket() {
  const token = getToken();

  const s = io(SOCKET_URL, {
    transports: ["websocket", "polling"], // fallback to polling if websocket fails
    autoConnect: true,
    reconnection: true,
    reconnectionAttempts: 10,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    randomizationFactor: 0.5,
    auth: {
      token: token || "",
    },
  });

  s.on("connect", () => {
    console.log("[Socket] Connected:", s.id);
    // Authenticate immediately after connect
    const t = getToken();
    if (t) {
      s.emit("authenticate", { token: t });
    }
  });

  s.on("disconnect", (reason) => {
    console.log("[Socket] Disconnected:", reason);
  });

  s.on("connect_error", (err) => {
    console.error("[Socket] Connection error:", err.message);
  });

  s.on("reconnect", (attemptNumber) => {
    console.log("[Socket] Reconnected after", attemptNumber, "attempts");
    // Re-authenticate after reconnect
    const t = getToken();
    if (t) {
      s.emit("authenticate", { token: t });
    }
  });

  s.on("reconnect_attempt", (attemptNumber) => {
    console.log("[Socket] Reconnect attempt", attemptNumber);
  });

  // Handle server-side errors gracefully
  s.on("error", (data) => {
    console.error("[Socket] Server error:", data?.message || data);
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
    socket.disconnect();
    socket.removeAllListeners();
    socket = null;
  }
  return getSocket();
}

// Room management helpers
export function joinConsultationRoom(consultationId) {
  try {
    const s = getSocket();
    s.emit("join_consultation", { consultation_id: consultationId });
  } catch (err) {
    console.error("[Socket] Failed to join consultation room:", err);
  }
}

export function leaveConsultationRoom(consultationId) {
  try {
    const s = getSocket();
    s.emit("leave_consultation", { consultation_id: consultationId });
  } catch (err) {
    console.error("[Socket] Failed to leave consultation room:", err);
  }
}

export function joinDoctorRoom(doctorId) {
  try {
    const s = getSocket();
    s.emit("join_doctor_room", { doctor_id: doctorId });
  } catch (err) {
    console.error("[Socket] Failed to join doctor room:", err);
  }
}

// Export the socket instance for direct event binding
export { socket };
