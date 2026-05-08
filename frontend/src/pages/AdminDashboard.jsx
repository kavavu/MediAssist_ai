import React, { useEffect, useState } from "react";
import { getAnalytics, getPendingDoctors, approveDoctor } from "../services/admin.js";

const StatCard = ({ title, value, color }) => (
  <div className={`bg-white rounded-xl p-5 border-l-4 ${color} shadow-sm`}>
    <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold">{title}</p>
    <p className="text-3xl font-bold text-slate-800 mt-1">{value}</p>
  </div>
);

export default function AdminDashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [pendingDoctors, setPendingDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [approvingId, setApprovingId] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [aRes, dRes] = await Promise.all([
          getAnalytics(),
          getPendingDoctors(),
        ]);
        setAnalytics(aRes.data);
        setPendingDoctors(dRes.data || []);
      } catch (err) {
        setError(err.response?.data?.error || "Failed to load admin data.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleApprove = async (id) => {
    setApprovingId(id);
    try {
      await approveDoctor(id);
      setPendingDoctors((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      alert(err.response?.data?.error || "Failed to approve doctor.");
    } finally {
      setApprovingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
        <span className="ml-3 text-slate-500">Loading admin dashboard...</span>
      </div>
    );
  }

  if (error) return <p className="text-red-500 p-6">{error}</p>;

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-6xl mx-auto px-6 py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl font-bold text-slate-800">Admin Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">Platform overview and doctor approvals</p>
        </div>

        {/* Analytics Cards */}
        {analytics && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <StatCard title="Total Users" value={analytics.total_users} color="border-primary-500" />
            <StatCard title="Doctors" value={analytics.total_doctors} color="border-blue-500" />
            <StatCard title="Patients" value={analytics.total_patients} color="border-emerald-500" />
            <StatCard title="Consultations" value={analytics.total_consultations} color="border-amber-500" />
          </div>
        )}

        {/* Pending Doctors */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-slate-800">Pending Doctor Approvals</h2>
            <span className="text-sm text-slate-500">{pendingDoctors.length} pending</span>
          </div>

          {pendingDoctors.length === 0 ? (
            <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
              <p className="text-slate-500 text-sm">No pending doctor approvals.</p>
              <p className="text-slate-400 text-xs mt-1">All doctors have been verified.</p>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200">
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Name</th>
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Email</th>
                      <th className="text-left px-5 py-3 font-semibold text-slate-600">Specialization</th>
                      <th className="text-right px-5 py-3 font-semibold text-slate-600">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingDoctors.map((d) => (
                      <tr key={d.id} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="px-5 py-3 font-medium text-slate-800">{d.name}</td>
                        <td className="px-5 py-3 text-slate-600">{d.email}</td>
                        <td className="px-5 py-3 text-slate-600">{d.specialization || "—"}</td>
                        <td className="px-5 py-3 text-right">
                          <button
                            onClick={() => handleApprove(d.id)}
                            disabled={approvingId === d.id}
                            className="px-4 py-1.5 bg-emerald-600 text-white text-xs font-semibold rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            {approvingId === d.id ? "Approving..." : "Approve"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
