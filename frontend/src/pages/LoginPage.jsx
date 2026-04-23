/**
 * Login page: email + password form. Calls login() from auth.js (POST /api/auth/login),
 * stores token in localStorage, then redirects by role (patient → /patient/dashboard, doctor → /doctor/dashboard).
 */
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { login, logout } from "../services/auth.js";
import "./LoginPage.css";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Clear any stale auth data when visiting login page
  useEffect(() => {
    logout();
  }, []);

  const isValidEmail = (value) => {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailPattern.test(value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!email || !isValidEmail(email)) {
      setError("Please enter a valid email address.");
      return;
    }
    if (!password) {
      setError("Please enter your password.");
      return;
    }

    setLoading(true);
    try {
      const user = await login(email, password);
      if (user.role === "patient") {
        navigate("/patient/dashboard");
      } else if (user.role === "doctor") {
        navigate("/doctor/dashboard");
      } else if (user.role === "admin") {
        navigate("/admin/dashboard");
      } else {
        navigate("/login");
      }
    } catch (err) {
      setError(err.response?.data?.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-gradient" />
      <div className="login-wrapper">
        <div className="login-card">
          <div className="login-header">
            <div className="login-icon" aria-hidden="true">
              <svg
                viewBox="0 0 48 48"
                className="login-icon-svg"
                role="presentation"
              >
                <defs>
                  <linearGradient id="med-cross" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#1da2ff" />
                    <stop offset="100%" stopColor="#22c1c3" />
                  </linearGradient>
                </defs>
                <path
                  fill="url(#med-cross)"
                  d="M20 6c0-1.1.9-2 2-2h4c1.1 0 2 .9 2 2v10h10c1.1 0 2 .9 2 2v4c0 1.1-.9 2-2 2H28v10c0 1.1-.9 2-2 2h-4c-1.1 0-2-.9-2-2V24H10c-1.1 0-2-.9-2-2v-4c0-1.1.9-2 2-2h10V6z"
                />
              </svg>
            </div>
            <div className="login-title-block">
              <h1 className="login-title">MediAssist AI</h1>
              <p className="login-subtitle">
                Secure access to your intelligent healthcare dashboard.
              </p>
            </div>
          </div>

          {error && (
            <div className="login-alert" role="alert">
              {error}
            </div>
          )}

          <form className="login-form" onSubmit={handleSubmit} noValidate>
            <div className="login-field">
              <label htmlFor="email" className="login-label">
                Email
              </label>
              <input
                id="email"
                type="email"
                className="login-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>

            <div className="login-field">
              <label htmlFor="password" className="login-label">
                Password
              </label>
              <input
                id="password"
                type="password"
                className="login-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                autoComplete="current-password"
              />
            </div>

            <div className="login-row">
              <label className="login-remember">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                <span>Remember me</span>
              </label>
              <button
                type="button"
                className="login-link-button"
                onClick={() => {}}
              >
                Forgot password?
              </button>
            </div>

            <button
              type="submit"
              className="login-button"
              disabled={loading}
            >
              {loading && <span className="login-spinner" aria-hidden="true" />}
              <span>{loading ? "Signing in..." : "Sign in"}</span>
            </button>
          </form>
        </div>

        <p className="login-footer">
          MediAssist AI © 2026 – Intelligent Healthcare Support- Ryan kavavu Nzioki
        </p>
      </div>
    </div>
  );
}

