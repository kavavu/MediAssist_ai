import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Eye, EyeOff, Shield, Lock, Wifi, HeartPulse } from "lucide-react";
import { login } from "../services/auth.js";
import { useToast } from "../components/ToastProvider.jsx";
import "./AuthPages.css";

export default function LoginPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

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
      if (user.role === "patient") navigate("/patient/dashboard");
      else if (user.role === "doctor") navigate("/doctor/dashboard");
      else if (user.role === "admin") navigate("/admin/dashboard");
      else navigate("/login");
    } catch (err) {
      setError(err.response?.data?.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      {/* Left Panel — Illustration & Branding */}
      <div className="auth-left">
        <div className="auth-illustration auth-animate-in">
          <svg viewBox="0 0 280 280" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Background circle */}
            <circle cx="140" cy="140" r="120" fill="url(#grad1)" opacity="0.15" />
            <circle cx="140" cy="140" r="90" fill="url(#grad2)" opacity="0.1" />
            {/* Medical cross */}
            <rect x="120" y="70" width="40" height="100" rx="8" fill="url(#grad3)" />
            <rect x="90" y="100" width="100" height="40" rx="8" fill="url(#grad3)" />
            {/* Heartbeat line */}
            <path d="M50 180 L80 180 L95 140 L115 220 L135 160 L155 200 L175 170 L230 170" 
              stroke="url(#grad3)" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" fill="none" />
            {/* Small decorative circles */}
            <circle cx="60" cy="100" r="8" fill="#22c1c3" opacity="0.3" />
            <circle cx="220" cy="80" r="6" fill="#1da2ff" opacity="0.3" />
            <circle cx="230" cy="200" r="10" fill="#22c1c3" opacity="0.2" />
            <circle cx="70" cy="230" r="5" fill="#1da2ff" opacity="0.25" />
            <defs>
              <linearGradient id="grad1" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#1da2ff" />
                <stop offset="100%" stopColor="#22c1c3" />
              </linearGradient>
              <linearGradient id="grad2" x1="1" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22c1c3" />
                <stop offset="100%" stopColor="#1da2ff" />
              </linearGradient>
              <linearGradient id="grad3" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#1da2ff" />
                <stop offset="100%" stopColor="#22c1c3" />
              </linearGradient>
            </defs>
          </svg>
        </div>

        <div className="auth-tagline auth-animate-in auth-delay-1">
          <h2>Your Health, Our Priority</h2>
          <p>Access AI-powered symptom analysis, connect with verified doctors, and manage your healthcare journey — all in one secure platform.</p>
        </div>

        <div className="auth-trust-badges auth-animate-in auth-delay-2">
          <span className="auth-trust-badge">
            <Shield className="w-3.5 h-3.5" /> HIPAA Compliant
          </span>
          <span className="auth-trust-badge">
            <Lock className="w-3.5 h-3.5" /> 256-bit Encryption
          </span>
          <span className="auth-trust-badge">
            <Wifi className="w-3.5 h-3.5" /> Secure Connection
          </span>
        </div>
      </div>

      {/* Right Panel — Form */}
      <div className="auth-right">
        <div className="auth-card">
          <div className="auth-header auth-animate-in">
            <div className="auth-header-icon">
              <HeartPulse className="w-7 h-7 text-white" />
            </div>
            <h1>Welcome Back</h1>
            <p>Sign in to your MediAssist AI account</p>
          </div>

          {error && (
            <div className="auth-alert auth-alert-error auth-animate-in auth-delay-1" role="alert">
              {error}
            </div>
          )}

          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <div className="auth-field auth-animate-in auth-delay-2">
              <label htmlFor="email" className="auth-label">Email</label>
              <input
                id="email"
                type="email"
                className="auth-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>

            <div className="auth-field auth-animate-in auth-delay-3">
              <label htmlFor="password" className="auth-label">Password</label>
              <div className="auth-input-wrap">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  className="auth-input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="auth-password-toggle"
                  onClick={() => setShowPassword((v) => !v)}
                  tabIndex={-1}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div className="auth-row auth-animate-in auth-delay-4">
              <label className="auth-remember">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                <span>Remember me</span>
              </label>
              <button
                type="button"
                className="auth-link-button"
                onClick={() => toast.info("Password reset is coming soon.")}
              >
                Forgot password?
              </button>
            </div>

            <button
              type="submit"
              className="auth-button auth-animate-in auth-delay-5"
              disabled={loading}
            >
              {loading && <span className="auth-spinner" aria-hidden="true" />}
              <span>{loading ? "Signing in..." : "Sign in"}</span>
            </button>
          </form>

          <p className="auth-footer auth-animate-in auth-delay-5">
            Don't have an account?{" "}
            <Link to="/register">Create one</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
