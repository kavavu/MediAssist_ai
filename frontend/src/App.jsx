/**
 * Root layout and routing.
 */
import React from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import NavBar from "./components/NavBar.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import PatientDashboard from "./pages/PatientDashboard.jsx";
import SubmitSymptomsPage from "./pages/SubmitSymptomsPage.jsx";
import LabTestsPage from "./pages/LabTestsPage.jsx";
import MedicinesPage from "./pages/MedicinesPage.jsx";
import DoctorDashboard from "./pages/DoctorDashboard.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import AppointmentsPage from "./pages/AppointmentsPage.jsx";
import { getCurrentUser } from "./services/auth.js";

function ProtectedRoute({ roles, children }) {
  const user = getCurrentUser();
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/login" replace />;
  return children;
}

function Layout({ children }) {
  const location = useLocation();
  const isFullWidth = location.pathname.startsWith("/doctor/dashboard") || location.pathname.startsWith("/patient/dashboard");
  
  if (isFullWidth) {
    return <>{children}</>;
  }
  return (
    <main className="max-w-5xl mx-auto px-6 py-6">
      {children}
    </main>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50">
      <NavBar />
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
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
          <Route
            path="/doctor/dashboard"
            element={
              <ProtectedRoute roles={["doctor"]}>
                <DoctorDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute roles={["admin"]}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/appointments"
            element={
              <ProtectedRoute roles={["patient", "doctor"]}>
                <AppointmentsPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Layout>
    </div>
  );
}
