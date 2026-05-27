/**
 * Subtle socket connection status badge.
 * Shows: Connected (green), Reconnecting (amber), Offline (red).
 */
import React, { useEffect, useState } from "react";
import { getSocket, getSocketConnectionStatus } from "../services/socket.js";

export default function SocketStatusBadge() {
  const [status, setStatus] = useState(() => getSocketConnectionStatus());

  useEffect(() => {
    const socket = getSocket();
    if (!socket) {
      setStatus("offline");
      return;
    }

    const onConnect = () => setStatus("connected");
    const onDisconnect = () => setStatus("offline");
    const onReconnectAttempt = () => setStatus("reconnecting");
    const onReconnect = () => setStatus("connected");

    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);
    socket.on("reconnect_attempt", onReconnectAttempt);
    socket.on("reconnect", onReconnect);

    // Initial state
    setStatus(getSocketConnectionStatus());

    return () => {
      try {
        socket.off("connect", onConnect);
        socket.off("disconnect", onDisconnect);
        socket.off("reconnect_attempt", onReconnectAttempt);
        socket.off("reconnect", onReconnect);
      } catch {
        /* ignore */
      }
    };
  }, []);

  const styles = {
    connected: "bg-emerald-100 text-emerald-700 border-emerald-200",
    reconnecting: "bg-amber-100 text-amber-700 border-amber-200",
    offline: "bg-red-100 text-red-700 border-red-200",
  };

  const labels = {
    connected: "● Connected",
    reconnecting: "● Reconnecting",
    offline: "● Offline",
  };

  return (
    <span
      className={`inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full border ${styles[status] || styles.offline}`}
      title={`Socket: ${status}`}
    >
      {labels[status] || "● Offline"}
    </span>
  );
}
