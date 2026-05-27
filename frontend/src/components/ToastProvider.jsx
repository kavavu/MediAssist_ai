import React, { createContext, useContext, useReducer, useCallback } from "react";
import Toast from "./Toast.jsx";

const ToastContext = createContext(null);

let toastId = 0;

function toastReducer(state, action) {
  switch (action.type) {
    case "ADD":
      return [...state, { id: ++toastId, ...action.payload }];
    case "REMOVE":
      return state.filter((t) => t.id !== action.id);
    default:
      return state;
  }
}

export function ToastProvider({ children }) {
  const [toasts, dispatch] = useReducer(toastReducer, []);

  const addToast = useCallback((type, message, duration) => {
    dispatch({ type: "ADD", payload: { type, message, duration } });
  }, []);

  const removeToast = useCallback((id) => {
    dispatch({ type: "REMOVE", id });
  }, []);

  const success = useCallback((msg, dur) => addToast("success", msg, dur), [addToast]);
  const error = useCallback((msg, dur) => addToast("error", msg, dur), [addToast]);
  const warning = useCallback((msg, dur) => addToast("warning", msg, dur), [addToast]);
  const info = useCallback((msg, dur) => addToast("info", msg, dur), [addToast]);

  return (
    <ToastContext.Provider value={{ success, error, warning, info }}>
      {children}
      {/* Toast container */}
      <div
        className="fixed top-4 right-4 z-[100] flex flex-col gap-2.5"
        aria-live="polite"
        aria-atomic="true"
      >
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            id={toast.id}
            type={toast.type}
            message={toast.message}
            duration={toast.duration}
            onRemove={removeToast}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return ctx;
}
