/**
 * Root layout and routing.
 * - Public: /login, /register
 * - Patient-only: /patient/dashboard, /patient/submit-symptoms, /patient/lab-tests, /patient/medicines
 * - Doctor-only: /doctor/dashboard
 * ProtectedRoute redirects to /login if not logged in or wrong role.
 */
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import NavBar from "./components/NavBar.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import PatientDashboard from "./pages/PatientDashboard.jsx";
import SubmitSymptomsPage from "./pages/SubmitSymptomsPage.jsx";
import LabTestsPage from "./pages/LabTestsPage.jsx";
import MedicinesPage from "./pages/MedicinesPage.jsx";
import DoctorDashboard from "./pages/DoctorDashboard.jsx";
import { getCurrentUser } from "./services/auth.js";

/** Wrapper: only show children if user is logged in and has one of the allowed roles. */
function ProtectedRoute({ roles, children }) {
  const user = getCurrentUser();
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <div style={{ fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" }}>
      <NavBar />
      <main style={{ maxWidth: "960px", margin: "0 auto", padding: "1.5rem" }}>
        <Routes>
          {/* Default path goes to login */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Patient routes: require role "patient" */}
          <Route
            path="/patient/dashboard"
            element={
              <ProtectedRoute roles={["patient"]}>
                <PatientDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patient/submit-symptoms"
            element={
              <ProtectedRoute roles={["patient"]}>
                <SubmitSymptomsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patient/lab-tests"
            element={
              <ProtectedRoute roles={["patient"]}>
                <LabTestsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/patient/medicines"
            element={
              <ProtectedRoute roles={["patient"]}>
                <MedicinesPage />
              </ProtectedRoute>
            }
          />

          {/* Doctor route: require role "doctor" */}
          <Route
            path="/doctor/dashboard"
            element={
              <ProtectedRoute roles={["doctor"]}>
                <DoctorDashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </div>
  );
}

