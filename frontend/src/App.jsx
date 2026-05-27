/**
 * Root layout and routing.
 */
import React from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import NavBar from "./components/NavBar.jsx";
import ErrorBoundary from "./components/ErrorBoundary.jsx";
import DashboardErrorBoundary from "./components/DashboardErrorBoundary.jsx";
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
import { ToastProvider } from "./components/ToastProvider.jsx";

function ProtectedRoute({ roles, children }) {
  const [user, setUser] = React.useState(getCurrentUser);

  React.useEffect(() => {
    const handleAuthChange = () => setUser(getCurrentUser());
    window.addEventListener("auth-change", handleAuthChange);
    return () => window.removeEventListener("auth-change", handleAuthChange);
  }, []);

  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/login" replace />;
  return children;
}

function RootRedirect() {
  const user = getCurrentUser();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "patient") return <Navigate to="/patient/dashboard" replace />;
  if (user.role === "doctor") return <Navigate to="/doctor/dashboard" replace />;
  if (user.role === "admin") return <Navigate to="/admin/dashboard" replace />;
  return <Navigate to="/login" replace />;
}

function Layout({ children }) {
  const location = useLocation();
  const isFullWidth = location.pathname.startsWith("/doctor/dashboard") || location.pathname.startsWith("/patient/dashboard") || location.pathname.startsWith("/admin/dashboard");

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
    <ErrorBoundary>
      <ToastProvider>
        <div className="min-h-screen bg-slate-50">
          <NavBar />
          <Layout>
            <Routes>
            <Route path="/" element={<RootRedirect />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              path="/patient/dashboard"
              element={
                <ProtectedRoute roles={["patient"]}>
                  <DashboardErrorBoundary>
                    <PatientDashboard />
                  </DashboardErrorBoundary>
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
                  <DashboardErrorBoundary>
                    <DoctorDashboard />
                  </DashboardErrorBoundary>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/dashboard"
              element={
                <ProtectedRoute roles={["admin"]}>
                  <DashboardErrorBoundary>
                    <AdminDashboard />
                  </DashboardErrorBoundary>
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
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </div>
    </ToastProvider>
    </ErrorBoundary>
  );
}
