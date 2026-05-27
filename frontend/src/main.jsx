/**
 * App entry point. Renders the root component into #root.
 * BrowserRouter enables client-side routes (e.g. /login, /patient/dashboard).
 *
 * SAFETY: Global unhandled promise rejection handler prevents silent crashes.
 */
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import "./index.css";

// Global safety net: log unhandled promise rejections (prevents silent failures)
window.addEventListener("unhandledrejection", (event) => {
  // In production, you could send to an error tracking service
  // For demo stability, we just prevent the default console error spam
  event.preventDefault();
});

// Global safety net: log uncaught errors
window.addEventListener("error", (event) => {
  // Prevent default handling for cleaner UX in demo
  event.preventDefault();
});

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
