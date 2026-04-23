/**
 * Register page: form for name, email, password, role. POSTs to /api/auth/register.
 * On success, shows message and redirects to /login (user must then log in).
 */
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { register } from "../services/auth.js";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "patient",
    specialization: "",
  });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);
    try {
      await register(form);
      setMessage("Registration successful. You can now log in.");
      setTimeout(() => navigate("/login"), 1200);
    } catch (err) {
      const msg = err.response?.data?.message;
      if (msg) setError(msg);
      else if (err.code === "ERR_NETWORK" || !err.response) setError("Cannot reach server. Is the backend running? Start it with: python backend\\run.py");
      else if (err.response?.status === 500) setError("Server error (500). Check the backend terminal for the error.");
      else setError(`Registration failed (${err.response?.status || "error"}). Check backend is running on port 5000.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-lg border border-slate-200 p-8">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-slate-800">Create Account</h1>
          <p className="text-sm text-slate-500 mt-1">Register to access MediAssist AI</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
            <input
              type="text"
              name="name"
              value={form.name}
              onChange={handleChange}
              required
              placeholder="Enter your full name"
              className="w-full px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              required
              placeholder="you@example.com"
              className="w-full px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
              placeholder="Create a password"
              className="w-full px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Role</label>
            <select
              name="role"
              value={form.role}
              onChange={handleChange}
              className="w-full px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
            >
              <option value="patient">Patient</option>
              <option value="doctor">Doctor</option>
            </select>
          </div>

          {form.role === "doctor" && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Specialization</label>
              <select
                name="specialization"
                value={form.specialization}
                onChange={handleChange}
                required={form.role === "doctor"}
                className="w-full px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              >
                <option value="">Select specialization...</option>
                <option value="General Doctor">General Doctor</option>
                <option value="Endocrinologist">Endocrinologist</option>
                <option value="Pulmonologist">Pulmonologist</option>
                <option value="Cardiologist">Cardiologist</option>
                <option value="Neurologist">Neurologist</option>
                <option value="Dermatologist">Dermatologist</option>
                <option value="Gastroenterologist">Gastroenterologist</option>
                <option value="Orthopedic">Orthopedic</option>
                <option value="Nephrologist">Nephrologist</option>
                <option value="Psychiatrist">Psychiatrist</option>
                <option value="Oncologist">Oncologist</option>
              </select>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}
          {message && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3">
              <p className="text-sm text-emerald-700">{message}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-600 text-white font-semibold py-2.5 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Registering..." : "Register"}
          </button>
        </form>

        <p className="text-center text-sm text-slate-500 mt-6">
          Already have an account?{" "}
          <a href="/login" className="text-primary-600 font-medium hover:underline">
            Log in
          </a>
        </p>
      </div>
    </div>
  );
}
