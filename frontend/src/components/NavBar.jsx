/**
 * Top navigation bar. Shows different links depending on login state and role.
 * - Not logged in: Login, Register
 * - Patient: Dashboard, Submit Symptoms, Lab Tests, Medicines
 * - Doctor: Doctor Dashboard
 * - All logged-in: email + Logout button
 */
import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getCurrentUser, logout } from "../services/auth.js";

export default function NavBar() {
  const navigate = useNavigate();
  const [, forceUpdate] = useState(0);

  // Re-read user when auth state changes across tabs/components
  useEffect(() => {
    const handleAuthChange = () => forceUpdate((n) => n + 1);
    window.addEventListener("auth-change", handleAuthChange);
    return () => window.removeEventListener("auth-change", handleAuthChange);
  }, []);

  const user = getCurrentUser();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const headerStyle = {
    background: "linear-gradient(90deg, #0f766e, #2563eb)",
    color: "#f9fafb",
    padding: "0.9rem 1.75rem",
    boxShadow: "0 10px 30px rgba(15, 23, 42, 0.25)",
    position: "sticky",
    top: 0,
    zIndex: 50
  };

  const containerStyle = {
    maxWidth: "1120px",
    margin: "0 auto",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "1.5rem"
  };

  const brandStyle = {
    display: "flex",
    alignItems: "center",
    gap: "0.6rem"
  };

  const brandLogoStyle = {
    width: "30px",
    height: "30px",
    borderRadius: "999px",
    background:
      "radial-gradient(circle at 30% 20%, #a7f3d0 0, #22c55e 20%, #0ea5e9 50%, #1d4ed8 100%)",
    boxShadow: "0 0 20px rgba(59, 130, 246, 0.6)"
  };

  const brandTextPrimaryStyle = {
    fontWeight: 700,
    letterSpacing: "0.05em",
    fontSize: "1.1rem"
  };

  const brandTextSecondaryStyle = {
    fontSize: "0.7rem",
    opacity: 0.9,
    textTransform: "uppercase"
  };

  const navStyle = {
    display: "flex",
    alignItems: "center",
    gap: "1rem",
    fontSize: "0.9rem"
  };

  const linkBaseStyle = {
    color: "#e5e7eb",
    textDecoration: "none",
    padding: "0.45rem 0.8rem",
    borderRadius: "999px",
    transition:
      "background-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease",
    fontWeight: 500
  };

  const primaryButtonStyle = {
    ...linkBaseStyle,
    backgroundColor: "#f9fafb",
    color: "#0f172a",
    boxShadow: "0 8px 20px rgba(15, 23, 42, 0.35)"
  };

  const secondaryButtonStyle = {
    ...linkBaseStyle,
    border: "1px solid rgba(249, 250, 251, 0.6)",
    backgroundColor: "rgba(15, 23, 42, 0.1)"
  };

  const pillsContainerStyle = {
    display: "flex",
    gap: "0.35rem",
    padding: "0.2rem",
    backgroundColor: "rgba(15, 23, 42, 0.25)",
    borderRadius: "999px",
    backdropFilter: "blur(12px)"
  };

  const userInfoStyle = {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
    fontSize: "0.8rem"
  };

  const logoutButtonStyle = {
    ...secondaryButtonStyle,
    border: "1px solid rgba(248, 250, 252, 0.9)",
    cursor: "pointer"
  };

  return (
    <header style={headerStyle}>
      <div style={containerStyle}>
        <div style={brandStyle}>
          <div style={brandLogoStyle} />
          <div>
            <div style={brandTextPrimaryStyle}>MediAssist AI</div>
            <div style={brandTextSecondaryStyle}>Smart clinical assistant</div>
          </div>
        </div>

        <nav style={navStyle}>
          {user && (user.role === "patient" || user.role === "doctor") && (
            <div style={pillsContainerStyle}>
              {user.role === "patient" && (
                <>
                  <Link to="/patient/dashboard" style={linkBaseStyle}>
                    Dashboard
                  </Link>
                  <Link to="/patient/submit-symptoms" style={linkBaseStyle}>
                    Symptoms
                  </Link>
                  <Link to="/patient/lab-tests" style={linkBaseStyle}>
                    Lab Tests
                  </Link>
                  <Link to="/patient/medicines" style={linkBaseStyle}>
                    Medicines
                  </Link>
                </>
              )}
              {user.role === "doctor" && (
                <Link to="/doctor/dashboard" style={linkBaseStyle}>
                  Doctor Dashboard
                </Link>
              )}
            </div>
          )}

          {!user && (
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <Link to="/login" style={secondaryButtonStyle}>
                Login
              </Link>
              <Link to="/register" style={primaryButtonStyle}>
                Register
              </Link>
            </div>
          )}

          {user && (
            <div style={userInfoStyle}>
              <span
                style={{
                  padding: "0.25rem 0.6rem",
                  borderRadius: "999px",
                  backgroundColor: "rgba(15, 23, 42, 0.35)",
                  border: "1px solid rgba(248, 250, 252, 0.15)"
                }}
              >
                {user.email}
              </span>
              <button onClick={handleLogout} style={logoutButtonStyle}>
                Logout
              </button>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}

