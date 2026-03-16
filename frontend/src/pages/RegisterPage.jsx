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
    role: "patient"
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
    <section>
      <h1>Register</h1>
      <form
        onSubmit={handleSubmit}
        style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxWidth: "360px" }}
      >
        <label>
          <span>Name</span>
          <input
            type="text"
            name="name"
            value={form.name}
            onChange={handleChange}
            required
            style={{ width: "100%", padding: "0.4rem" }}
          />
        </label>
        <label>
          <span>Email</span>
          <input
            type="email"
            name="email"
            value={form.email}
            onChange={handleChange}
            required
            style={{ width: "100%", padding: "0.4rem" }}
          />
        </label>
        <label>
          <span>Password</span>
          <input
            type="password"
            name="password"
            value={form.password}
            onChange={handleChange}
            required
            style={{ width: "100%", padding: "0.4rem" }}
          />
        </label>
        <label>
          <span>Role</span>
          <select
            name="role"
            value={form.role}
            onChange={handleChange}
            style={{ width: "100%", padding: "0.4rem" }}
          >
            <option value="patient">Patient</option>
            <option value="doctor">Doctor</option>
          </select>
        </label>
        {error && <p style={{ color: "red" }}>{error}</p>}
        {message && <p style={{ color: "green" }}>{message}</p>}
        <button type="submit" disabled={loading} style={{ padding: "0.5rem 0.75rem" }}>
          {loading ? "Registering..." : "Register"}
        </button>
      </form>
    </section>
  );
}

