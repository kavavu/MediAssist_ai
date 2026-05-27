import React, { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Menu, X, LogOut } from "lucide-react";
import { getCurrentUser, logout } from "../services/auth.js";

export default function NavBar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [, forceUpdate] = useState(0);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handleAuthChange = () => forceUpdate((n) => n + 1);
    window.addEventListener("auth-change", handleAuthChange);
    return () => window.removeEventListener("auth-change", handleAuthChange);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const user = getCurrentUser();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const isActive = (path) => location.pathname === path;

  const navLinkClass = (path) =>
    `px-3.5 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
      isActive(path)
        ? "bg-white text-slate-900 shadow-sm"
        : "text-slate-200 hover:text-white hover:bg-white/10"
    }`;

  const mobileLinkClass = (path) =>
    `block px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
      isActive(path)
        ? "bg-primary-600 text-white"
        : "text-slate-700 hover:bg-slate-100"
    }`;

  const patientLinks = [
    { to: "/patient/dashboard", label: "Dashboard" },
    { to: "/patient/submit-symptoms", label: "Symptoms" },
    { to: "/patient/lab-tests", label: "Lab Tests" },
    { to: "/patient/medicines", label: "Medicines" },
    { to: "/appointments", label: "Appointments" },
  ];

  const doctorLinks = [
    { to: "/doctor/dashboard", label: "Doctor Dashboard" },
    { to: "/appointments", label: "Appointments" },
  ];

  const adminLinks = [
    { to: "/admin/dashboard", label: "Admin Dashboard" },
  ];

  const getLinks = () => {
    if (!user) return [];
    if (user.role === "patient") return patientLinks;
    if (user.role === "doctor") return doctorLinks;
    if (user.role === "admin") return adminLinks;
    return [];
  };

  const links = getLinks();

  return (
    <header className="sticky top-0 z-50 bg-gradient-to-r from-primary-800 to-clinical-700 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-14">
          {/* Brand */}
          <Link to="/" className="flex items-center gap-2.5 shrink-0">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-300 via-primary-400 to-clinical-500 shadow-md shadow-primary-500/30" />
            <div className="hidden sm:block">
              <div className="text-white font-bold text-base tracking-wide leading-tight">
                MediAssist AI
              </div>
              <div className="text-white/70 text-[0.65rem] uppercase tracking-wider leading-tight">
                Smart clinical assistant
              </div>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {links.map((link) => (
              <Link key={link.to} to={link.to} className={navLinkClass(link.to)}>
                {link.label}
              </Link>
            ))}
          </nav>

          {/* Right side — user info + logout / login buttons */}
          <div className="flex items-center gap-2">
            {!user && (
              <div className="hidden sm:flex items-center gap-2">
                <Link
                  to="/login"
                  className="px-4 py-2 rounded-full text-sm font-medium text-slate-200 border border-white/40 hover:text-white hover:bg-white/10 transition-all"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 rounded-full text-sm font-medium bg-white text-slate-900 hover:bg-slate-100 transition-all shadow-md"
                >
                  Register
                </Link>
              </div>
            )}

            {user && (
              <div className="hidden md:flex items-center gap-2">
                <span className="px-3 py-1.5 rounded-full text-xs font-medium bg-black/20 text-white/90 border border-white/10">
                  {user.email}
                </span>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-white/90 border border-white/40 hover:bg-white/10 transition-all"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Logout
                </button>
              </div>
            )}

            {/* Mobile hamburger */}
            <button
              onClick={() => setMobileOpen((v) => !v)}
              className="md:hidden p-2 rounded-lg text-white hover:bg-white/10 transition-colors"
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <div
        className={`md:hidden overflow-hidden transition-all duration-300 ease-in-out ${
          mobileOpen ? "max-h-96 opacity-100" : "max-h-0 opacity-0"
        }`}
      >
        <div className="px-4 pb-4 pt-1 bg-white/95 backdrop-blur-md border-t border-white/10">
          {/* Mobile nav links */}
          {links.length > 0 && (
            <div className="space-y-1 mb-3">
              {links.map((link) => (
                <Link key={link.to} to={link.to} className={mobileLinkClass(link.to)}>
                  {link.label}
                </Link>
              ))}
            </div>
          )}

          {/* Mobile auth buttons */}
          {!user && (
            <div className="grid grid-cols-2 gap-2">
              <Link
                to="/login"
                className="text-center px-4 py-2.5 rounded-xl text-sm font-medium text-slate-700 border border-slate-200 hover:bg-slate-50 transition-colors"
              >
                Login
              </Link>
              <Link
                to="/register"
                className="text-center px-4 py-2.5 rounded-xl text-sm font-medium bg-primary-600 text-white hover:bg-primary-700 transition-colors"
              >
                Register
              </Link>
            </div>
          )}

          {user && (
            <div className="space-y-2">
              <div className="px-4 py-2 text-xs text-slate-500 truncate">
                Signed in as <span className="font-medium text-slate-700">{user.email}</span>
              </div>
              <button
                onClick={handleLogout}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
