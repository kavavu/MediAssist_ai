import React, { useEffect, useState, useCallback } from "react";
import {
  getDashboardStats,
  getDoctors,
  verifyDoctor,
  unverifyDoctor,
  toggleAvailability,
  getConsultations,
  getPayments,
  getReviews,
} from "../services/admin.js";
import SocketStatusBadge from "../components/SocketStatusBadge.jsx";
import { SkeletonStats, SkeletonTable } from "../components/Skeleton.jsx";
import EmptyState from "../components/EmptyState.jsx";

/* ------------------------------------------------------------------ */
/* Reusable UI primitives                                             */
/* ------------------------------------------------------------------ */

const StatCard = ({ title, value, color, prefix = "" }) => (
  <div className={`bg-white rounded-xl p-5 border-l-4 ${color} shadow-sm`}>
    <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold">{title}</p>
    <p className="text-3xl font-bold text-slate-800 mt-1">
      {prefix}{value}
    </p>
  </div>
);

const SectionTitle = ({ children, count }) => (
  <div className="flex items-center justify-between mb-4">
    <h2 className="text-lg font-bold text-slate-800">{children}</h2>
    {count !== undefined && (
      <span className="text-sm text-slate-500">{count} total</span>
    )}
  </div>
);



const LoadingSpinner = ({ text = "Loading..." }) => (
  <div className="flex items-center justify-center h-96">
    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
    <span className="ml-3 text-slate-500">{text}</span>
  </div>
);

const ErrorBox = ({ message }) => (
  <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
    <p className="text-sm text-red-700">{message}</p>
  </div>
);

const Badge = ({ text, colorClass }) => (
  <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${colorClass}`}>
    {text}
  </span>
);

const PriorityBadge = ({ level }) => {
  const colors = {
    HIGH: "bg-red-100 text-red-700 border-red-200",
    MEDIUM: "bg-amber-100 text-amber-700 border-amber-200",
    LOW: "bg-emerald-100 text-emerald-700 border-emerald-200",
  };
  return <Badge text={level} colorClass={colors[level] || colors.LOW} />;
};

const StatusBadge = ({ status }) => {
  const colors = {
    pending: "bg-amber-100 text-amber-700 border-amber-200",
    responded: "bg-blue-100 text-blue-700 border-blue-200",
    resolved: "bg-emerald-100 text-emerald-700 border-emerald-200",
    scheduled: "bg-blue-100 text-blue-700 border-blue-200",
    completed: "bg-emerald-100 text-emerald-700 border-emerald-200",
    cancelled: "bg-red-100 text-red-700 border-red-200",
    failed: "bg-red-100 text-red-700 border-red-200",
  };
  return <Badge text={status} colorClass={colors[status] || "bg-slate-100 text-slate-700 border-slate-200"} />;
};

/* ------------------------------------------------------------------ */
/* Main Dashboard Component                                           */
/* ------------------------------------------------------------------ */

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [doctors, setDoctors] = useState([]);
  const [consultations, setConsultations] = useState([]);
  const [payments, setPayments] = useState(null);
  const [reviews, setReviews] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState({});
  const [actionError, setActionError] = useState("");

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const results = await Promise.allSettled([
        getDashboardStats(),
        getDoctors(),
        getConsultations(),
        getPayments(),
        getReviews(),
      ]);

      const [sRes, dRes, cRes, pRes, rRes] = results;

      if (sRes.status === "fulfilled") {
        setStats(sRes.value?.data || {});
      }
      if (dRes.status === "fulfilled") {
        setDoctors(dRes.value?.data || []);
      }
      if (cRes.status === "fulfilled") {
        setConsultations(cRes.value?.data || []);
      }
      if (pRes.status === "fulfilled") {
        setPayments(pRes.value?.data || null);
      }
      if (rRes.status === "fulfilled") {
        setReviews(rRes.value?.data || null);
      }

      const failed = results.filter((r) => r.status === "rejected");
      if (failed.length > 0) {
        setError("Some dashboard data could not be loaded. Displaying available information.");
      }
    } catch (err) {
      setError("Failed to load admin dashboard data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const handleVerify = async (id) => {
    setActionLoading((prev) => ({ ...prev, [`verify-${id}`]: true }));
    setActionError("");
    try {
      await verifyDoctor(id);
      setDoctors((prev) =>
        prev.map((d) => (d.id === id ? { ...d, is_verified: true } : d))
      );
    } catch (err) {
      setActionError(err.response?.data?.error || "Failed to verify doctor.");
    } finally {
      setActionLoading((prev) => ({ ...prev, [`verify-${id}`]: false }));
    }
  };

  const handleUnverify = async (id) => {
    setActionLoading((prev) => ({ ...prev, [`unverify-${id}`]: true }));
    setActionError("");
    try {
      await unverifyDoctor(id);
      setDoctors((prev) =>
        prev.map((d) => (d.id === id ? { ...d, is_verified: false } : d))
      );
    } catch (err) {
      setActionError(err.response?.data?.error || "Failed to unverify doctor.");
    } finally {
      setActionLoading((prev) => ({ ...prev, [`unverify-${id}`]: false }));
    }
  };

  const handleToggleAvailability = async (id) => {
    setActionLoading((prev) => ({ ...prev, [`avail-${id}`]: true }));
    setActionError("");
    try {
      const res = await toggleAvailability(id);
      setDoctors((prev) =>
        prev.map((d) => (d.id === id ? { ...d, is_available: res.data.is_available } : d))
      );
    } catch (err) {
      setActionError(err.response?.data?.error || "Failed to toggle availability.");
    } finally {
      setActionLoading((prev) => ({ ...prev, [`avail-${id}`]: false }));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          <SkeletonStats count={6} />
          <SkeletonTable rows={5} cols={5} />
        </div>
      </div>
    );
  }
  if (error && !stats && !doctors.length && !consultations.length && !payments && !reviews) {
    return <div className="p-6"><ErrorBox message={error} /></div>;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-800">Admin Dashboard</h1>
            <p className="text-sm text-slate-500 mt-1">Platform overview and management</p>
          </div>
          <div className="flex items-center gap-3">
            <SocketStatusBadge />
            <button
              onClick={fetchAll}
              className="px-4 py-2 bg-white border border-slate-200 text-slate-700 font-semibold rounded-lg hover:bg-slate-50 transition-colors text-sm"
            >
              Refresh
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4">
            <ErrorBox message={error} />
          </div>
        )}

        {actionError && (
          <div className="mb-4">
            <ErrorBox message={actionError} />
          </div>
        )}

        {/* Analytics Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
            <StatCard title="Total Users" value={stats.total_users ?? 0} color="border-primary-500" />
            <StatCard title="Doctors" value={stats.total_doctors ?? 0} color="border-blue-500" />
            <StatCard title="Patients" value={stats.total_patients ?? 0} color="border-emerald-500" />
            <StatCard title="Revenue" value={typeof stats.total_revenue === "number" ? stats.total_revenue.toLocaleString() : "0"} prefix="KSh " color="border-amber-500" />
            <StatCard title="Consultations" value={stats.total_consultations ?? 0} color="border-purple-500" />
            <StatCard title="Appointments" value={stats.total_appointments ?? 0} color="border-rose-500" />
          </div>
        )}

        {/* Secondary Stats */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm text-center">
              <p className="text-2xl font-bold text-slate-800">{stats.verified_doctors ?? 0}</p>
              <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold mt-1">Verified Doctors</p>
            </div>
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm text-center">
              <p className="text-2xl font-bold text-slate-800">{stats.pending_doctors ?? 0}</p>
              <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold mt-1">Pending Doctors</p>
            </div>
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm text-center">
              <p className="text-2xl font-bold text-slate-800">{stats.active_doctors ?? 0}</p>
              <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold mt-1">Active Doctors</p>
            </div>
            <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm text-center">
              <p className="text-2xl font-bold text-slate-800">{typeof stats.average_doctor_rating === "number" ? stats.average_doctor_rating.toFixed(1) : "—"}</p>
              <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold mt-1">Avg Rating</p>
            </div>
          </div>
        )}

        {/* Doctor Management */}
        <div className="mb-10">
          <SectionTitle count={doctors.length}>Doctor Management</SectionTitle>
          {doctors.length === 0 ? (
            <EmptyState icon="users" title="No doctors found" description="Doctors will appear here after registration." />
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200">
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Name</th>
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Specialization</th>
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Verified</th>
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Availability</th>
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Load</th>
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Rating</th>
                      <th className="text-right px-5 py-3 font-semibold text-slate-600">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {doctors.map((d) => (
                      <tr key={d.id} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="px-5 py-3 font-medium text-slate-800">
                          {d.name}
                          <p className="text-xs text-slate-400 font-normal">{d.email}</p>
                        </td>
                        <td className="px-5 py-3 text-slate-600">{d.specialization || "—"}</td>
                        <td className="px-5 py-3">
                          {d.is_verified ? (
                            <Badge text="Verified" colorClass="bg-emerald-100 text-emerald-700 border-emerald-200" />
                          ) : (
                            <Badge text="Pending" colorClass="bg-amber-100 text-amber-700 border-amber-200" />
                          )}
                        </td>
                        <td className="px-5 py-3">
                          {d.is_available ? (
                            <Badge text="Available" colorClass="bg-blue-100 text-blue-700 border-blue-200" />
                          ) : (
                            <Badge text="Offline" colorClass="bg-slate-100 text-slate-600 border-slate-200" />
                          )}
                        </td>
                        <td className="px-5 py-3 text-slate-600">{d.current_load}</td>
                        <td className="px-5 py-3 text-slate-600">{d.rating || "—"}</td>
                        <td className="px-5 py-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {d.is_verified ? (
                              <button
                                onClick={() => handleUnverify(d.id)}
                                disabled={actionLoading[`unverify-${d.id}`]}
                                className="px-3 py-1.5 bg-white border border-red-200 text-red-600 text-xs font-semibold rounded-lg hover:bg-red-50 disabled:opacity-50 transition-colors"
                              >
                                {actionLoading[`unverify-${d.id}`] ? "..." : "Unverify"}
                              </button>
                            ) : (
                              <button
                                onClick={() => handleVerify(d.id)}
                                disabled={actionLoading[`verify-${d.id}`]}
                                className="px-3 py-1.5 bg-emerald-600 text-white text-xs font-semibold rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors"
                              >
                                {actionLoading[`verify-${d.id}`] ? "..." : "Verify"}
                              </button>
                            )}
                            <button
                              onClick={() => handleToggleAvailability(d.id)}
                              disabled={actionLoading[`avail-${d.id}`]}
                              className="px-3 py-1.5 bg-white border border-slate-200 text-slate-700 text-xs font-semibold rounded-lg hover:bg-slate-50 disabled:opacity-50 transition-colors"
                            >
                              {actionLoading[`avail-${d.id}`] ? "..." : "Toggle"}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Consultation Overview */}
        <div className="mb-10">
          <SectionTitle count={consultations.length}>Consultation Overview</SectionTitle>
          {consultations.length === 0 ? (
            <EmptyState icon="inbox" title="No consultations found" description="Consultations will appear here when patients create them." />
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200">
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Patient</th>
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Doctor</th>
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Condition</th>
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Priority</th>
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Status</th>
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {consultations.slice(0, 50).map((c) => (
                      <tr key={c.id} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="px-5 py-3 text-slate-800">{c.patient_name || "—"}</td>
                        <td className="px-5 py-3 text-slate-800">{c.doctor_name || "—"}</td>
                        <td className="px-5 py-3 text-slate-600">{c.predicted_condition || "—"}</td>
                        <td className="px-5 py-3"><PriorityBadge level={c.priority} /></td>
                        <td className="px-5 py-3"><StatusBadge status={c.status} /></td>
                        <td className="px-5 py-3 text-slate-500">
                          {c.created_at ? new Date(c.created_at).toLocaleDateString() : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Payments Overview */}
        <div className="mb-10">
          <SectionTitle>Payments Overview</SectionTitle>
          {!payments ? (
            <EmptyState icon="inbox" title="No payment data" description="Payment records will appear here after transactions." />
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Payment Stats */}
              <div className="lg:col-span-1 space-y-4">
                <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
                  <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold">Total Revenue</p>
                  <p className="text-2xl font-bold text-slate-800 mt-1">KSh {typeof payments.total_revenue === "number" ? payments.total_revenue.toLocaleString() : "0"}</p>
                </div>
                <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-600">Completed</span>
                    <span className="text-sm font-bold text-emerald-600">{payments.completed}</span>
                  </div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-600">Failed</span>
                    <span className="text-sm font-bold text-red-600">{payments.failed}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">Pending</span>
                    <span className="text-sm font-bold text-amber-600">{payments.pending}</span>
                  </div>
                </div>
              </div>

              {/* Method Breakdown */}
              <div className="lg:col-span-2">
                <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-slate-50 border-b border-slate-200">
                          <th className="text-left px-5 py-3 font-semibold text-slate-600">Method</th>
                          <th className="text-left px-5 py-3 font-semibold text-slate-600">Count</th>
                          <th className="text-left px-5 py-3 font-semibold text-slate-600">Amount</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(payments.method_breakdown || []).length === 0 ? (
                          <tr>
                            <td colSpan={3} className="px-5 py-6 text-center text-slate-500">
                              No completed payment methods to display.
                            </td>
                          </tr>
                        ) : (
                          (payments.method_breakdown || []).map((m, idx) => (
                            <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                              <td className="px-5 py-3 font-medium text-slate-800">{m.method}</td>
                              <td className="px-5 py-3 text-slate-600">{m.count}</td>
                              <td className="px-5 py-3 text-slate-600">KSh {typeof m.amount === "number" ? m.amount.toLocaleString() : "0"}</td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Review Analytics */}
        <div className="mb-10">
          <SectionTitle>Review Analytics</SectionTitle>
          {!reviews ? (
            <EmptyState icon="chat" title="No reviews yet" description="Patient reviews will appear here after consultations are completed." />
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Average Rating */}
              <div className="lg:col-span-1 space-y-4">
                <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm text-center">
                  <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold">Average Platform Rating</p>
                  <p className="text-4xl font-bold text-primary-600 mt-2">{typeof reviews.average_platform_rating === "number" ? reviews.average_platform_rating.toFixed(1) : "—"}</p>
                  <p className="text-sm text-slate-400 mt-1">out of 5</p>
                </div>
                <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
                  <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold mb-3">Top Rated Doctors</p>
                  <div className="space-y-3">
                    {(reviews.top_doctors || []).slice(0, 5).map((doc) => (
                      <div key={doc.id} className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-slate-800">{doc.name}</p>
                          <p className="text-xs text-slate-400">{doc.specialization || "—"}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-bold text-primary-600">{doc.avg_rating}</p>
                          <p className="text-xs text-slate-400">{doc.review_count} reviews</p>
                        </div>
                      </div>
                    ))}
                    {(reviews.top_doctors || []).length === 0 && (
                      <p className="text-sm text-slate-500">No reviews yet.</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Recent Reviews */}
              <div className="lg:col-span-2">
                <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-slate-50 border-b border-slate-200">
                          <th className="text-left px-5 py-3 font-semibold text-slate-600">Patient</th>
                          <th className="text-left px-5 py-3 font-semibold text-slate-600">Doctor</th>
                          <th className="text-left px-5 py-3 font-semibold text-slate-600">Rating</th>
                          <th className="text-left px-5 py-3 font-semibold text-slate-600">Comment</th>
                          <th className="text-left px-5 py-3 font-semibold text-slate-600">Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(reviews.recent_reviews || []).length === 0 ? (
                          <tr>
                            <td colSpan={5} className="px-5 py-6 text-center text-slate-500">
                              No reviews yet.
                            </td>
                          </tr>
                        ) : (
                          reviews.recent_reviews.map((r) => (
                            <tr key={r.id} className="border-b border-slate-100 hover:bg-slate-50">
                              <td className="px-5 py-3 text-slate-800">{r.patient_name || "—"}</td>
                              <td className="px-5 py-3 text-slate-800">{r.doctor_name || "—"}</td>
                              <td className="px-5 py-3">
                                <span className="text-sm font-bold text-primary-600">{r.rating}</span>
                                <span className="text-xs text-slate-400"> /5</span>
                              </td>
                              <td className="px-5 py-3 text-slate-600 max-w-xs truncate">{r.comment || "—"}</td>
                              <td className="px-5 py-3 text-slate-500">
                                {r.created_at ? new Date(r.created_at).toLocaleDateString() : "—"}
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
