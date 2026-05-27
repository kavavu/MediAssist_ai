import React, { useState, useMemo } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Eye, EyeOff, HeartPulse, User, Stethoscope } from "lucide-react";
import { register } from "../services/auth.js";
import { useToast } from "../components/ToastProvider.jsx";
import "./AuthPages.css";

const SPECIALIZATIONS = [
  "General Doctor",
  "Endocrinologist",
  "Pulmonologist",
  "Cardiologist",
  "Neurologist",
  "Dermatologist",
  "Gastroenterologist",
  "Orthopedic",
  "Nephrologist",
  "Psychiatrist",
  "Oncologist",
];

function getPasswordStrength(pw) {
  let score = 0;
  if (pw.length >= 8) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  return score;
}

export default function RegisterPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "patient",
    specialization: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const strength = useMemo(() => getPasswordStrength(form.password), [form.password]);
  const strengthLabel = strength <= 1 ? "Weak" : strength === 2 ? "Medium" : "Strong";
  const strengthClass = strength <= 1 ? "weak" : strength === 2 ? "medium" : "strong";

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");

    if (!form.name.trim()) {
      setError("Please enter your full name.");
      return;
    }
    if (!form.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      setError("Please enter a valid email address.");
      return;
    }
    if (form.password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    if (form.role === "doctor" && !form.specialization) {
      setError("Please select a specialization.");
      return;
    }

    setLoading(true);
    try {
      await register(form);
      setMessage("Registration successful. You can now log in.");
      toast.success("Account created successfully!");
      setTimeout(() => navigate("/login"), 1500);
    } catch (err) {
      const msg = err.response?.data?.message;
      if (msg) setError(msg);
      else if (err.code === "ERR_NETWORK" || !err.response)
        setError("Cannot reach server. Is the backend running?");
      else if (err.response?.status === 500) setError("Server error (500).");
      else setError(`Registration failed. Check backend is running on port 5000.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      {/* Left Panel */}
      <div className="auth-left">
        <div className="auth-illustration auth-animate-in">
          <svg viewBox="0 0 280 280" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="140" cy="140" r="120" fill="url(#rg1)" opacity="0.15" />
            <circle cx="140" cy="140" r="90" fill="url(#rg2)" opacity="0.1" />
            {/* Stethoscope illustration */}
            <path d="M90 180 C90 120, 110 100, 140 100 C170 100, 190 120, 190 160" 
              stroke="url(#rg3)" strokeWidth="6" strokeLinecap="round" fill="none" />
            <circle cx="140" cy="95" r="12" fill="url(#rg3)" />
            <circle cx="90" cy="180" r="10" stroke="url(#rg3)" strokeWidth="4" fill="none" />
            <circle cx="190" cy="160" r="10" stroke="url(#rg3)" strokeWidth="4" fill="none" />
            {/* Small decorative elements */}
            <circle cx="60" cy="100" r="8" fill="#22c1c3" opacity="0.3" />
            <circle cx="220" cy="80" r="6" fill="#1da2ff" opacity="0.3" />
            <circle cx="230" cy="200" r="10" fill="#22c1c3" opacity="0.2" />
            <circle cx="70" cy="230" r="5" fill="#1da2ff" opacity="0.25" />
            <defs>
              <linearGradient id="rg1" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#1da2ff" />
                <stop offset="100%" stopColor="#22c1c3" />
              </linearGradient>
              <linearGradient id="rg2" x1="1" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22c1c3" />
                <stop offset="100%" stopColor="#1da2ff" />
              </linearGradient>
              <linearGradient id="rg3" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#1da2ff" />
                <stop offset="100%" stopColor="#22c1c3" />
              </linearGradient>
            </defs>
          </svg>
        </div>

        <div className="auth-tagline auth-animate-in auth-delay-1">
          <h2>Join MediAssist AI</h2>
          <p>Get AI-powered health insights, connect with verified specialists, and take control of your wellbeing with our intelligent healthcare platform.</p>
        </div>

        <div className="auth-trust-badges auth-animate-in auth-delay-2">
          <span className="auth-trust-badge">🔒 Secure Registration</span>
          <span className="auth-trust-badge">✓ Verified Doctors</span>
          <span className="auth-trust-badge">⚡ Instant Access</span>
        </div>
      </div>

      {/* Right Panel — Form */}
      <div className="auth-right">
        <div className="auth-card">
          <div className="auth-header auth-animate-in">
            <div className="auth-header-icon">
              <HeartPulse className="w-7 h-7 text-white" />
            </div>
            <h1>Create Account</h1>
            <p>Register to access MediAssist AI</p>
          </div>

          {error && (
            <div className="auth-alert auth-alert-error auth-animate-in auth-delay-1" role="alert">
              {error}
            </div>
          )}
          {message && (
            <div className="auth-alert auth-alert-success auth-animate-in auth-delay-1" role="alert">
              {message}
            </div>
          )}

          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <div className="auth-field auth-animate-in auth-delay-1">
              <label htmlFor="name" className="auth-label">Full Name</label>
              <input
                id="name"
                type="text"
                name="name"
                className="auth-input"
                value={form.name}
                onChange={handleChange}
                placeholder="Enter your full name"
                autoComplete="name"
              />
            </div>

            <div className="auth-field auth-animate-in auth-delay-2">
              <label htmlFor="email" className="auth-label">Email</label>
              <input
                id="email"
                type="email"
                name="email"
                className="auth-input"
                value={form.email}
                onChange={handleChange}
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
                  name="password"
                  className="auth-input"
                  value={form.password}
                  onChange={handleChange}
                  placeholder="Create a password"
                  autoComplete="new-password"
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
              {form.password && (
                <>
                  <div className="auth-strength-bar">
                    {[1, 2, 3, 4].map((s) => (
                      <div
                        key={s}
                        className={`auth-strength-segment ${strength >= s ? strengthClass : ""}`}
                      />
                    ))}
                  </div>
                  <div className={`auth-strength-label ${strengthClass}`}>
                    {strengthLabel}
                  </div>
                </>
              )}
            </div>

            <div className="auth-field auth-animate-in auth-delay-4">
              <label className="auth-label">I am a</label>
              <div className="auth-role-cards">
                <div
                  className={`auth-role-card ${form.role === "patient" ? "selected" : ""}`}
                  onClick={() => setForm((f) => ({ ...f, role: "patient", specialization: "" }))}
                >
                  <User className="w-6 h-6" />
                  <span>Patient</span>
                </div>
                <div
                  className={`auth-role-card ${form.role === "doctor" ? "selected" : ""}`}
                  onClick={() => setForm((f) => ({ ...f, role: "doctor" }))}
                >
                  <Stethoscope className="w-6 h-6" />
                  <span>Doctor</span>
                </div>
              </div>
            </div>

            {form.role === "doctor" && (
              <div className="auth-field auth-animate-in">
                <label htmlFor="specialization" className="auth-label">Specialization</label>
                <select
                  id="specialization"
                  name="specialization"
                  className="auth-input"
                  value={form.specialization}
                  onChange={handleChange}
                  required
                >
                  <option value="">Select specialization...</option>
                  {SPECIALIZATIONS.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
            )}

            <button
              type="submit"
              className="auth-button auth-animate-in auth-delay-5"
              disabled={loading}
            >
              {loading && <span className="auth-spinner" aria-hidden="true" />}
              <span>{loading ? "Registering..." : "Create Account"}</span>
            </button>
          </form>

          <p className="auth-footer auth-animate-in auth-delay-5">
            Already have an account?{" "}
            <Link to="/login">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
