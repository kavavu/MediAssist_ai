/**
 * Doctor dashboard: GET /api/doctor/symptom-reports.
 *
 * Shows a table of all patient symptom reports, including:
 * - Patient name and email
 * - Symptoms
 * - Primary prediction + confidence
 * - Optional top predictions list
 * - An in-UI "Mark as reviewed" action (client-side flag for now)
 */
import React, { useEffect, useState } from "react";
import api from "../services/api.js";

export default function DoctorDashboard() {
  const [reports, setReports] = useState([]);
  const [reviewedIds, setReviewedIds] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get("/doctor/symptom-reports");
        setReports(res.data.symptom_reports || []);
      } catch (err) {
        setError(err.response?.data?.message || "Failed to load symptom reports");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const markReviewed = (id) => {
    setReviewedIds((prev) => new Set(prev).add(id));
  };

  const isReviewed = (id) => reviewedIds.has(id);

  return (
    <section>
      <h1>Doctor Dashboard</h1>
      <p>View patient symptom reports and AI predictions.</p>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {!loading && !error && reports.length === 0 && <p>No symptom reports yet.</p>}
      {!loading && reports.length > 0 && (
        <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "1rem" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.4rem" }}>Date</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.4rem" }}>Patient</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.4rem" }}>Symptoms</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.4rem" }}>Prediction</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.4rem" }}>Confidence</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.4rem" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((r) => {
              const topPreds = r.top_predictions || null;
              return (
                <tr key={r.id}>
                  <td style={{ padding: "0.4rem", borderBottom: "1px solid #f0f0f0" }}>
                    {r.created_at ? new Date(r.created_at).toLocaleString() : "-"}
                  </td>
                  <td style={{ padding: "0.4rem", borderBottom: "1px solid #f0f0f0" }}>
                    {r.patient_name || "Unknown"} <br />
                    <span style={{ color: "#555", fontSize: "0.85rem" }}>{r.patient_email}</span>
                  </td>
                  <td style={{ padding: "0.4rem", borderBottom: "1px solid #f0f0f0" }}>{r.symptoms_text}</td>
                  <td style={{ padding: "0.4rem", borderBottom: "1px solid #f0f0f0" }}>
                    {r.predicted_condition || "-"}
                    {topPreds && (
                      <div style={{ marginTop: "0.25rem", fontSize: "0.85rem", color: "#555" }}>
                        {Object.entries(topPreds).map(([cond, conf]) => (
                          <div key={cond}>
                            {cond}: {(conf * 100).toFixed(1)}%
                          </div>
                        ))}
                      </div>
                    )}
                  </td>
                  <td style={{ padding: "0.4rem", borderBottom: "1px solid #f0f0f0" }}>
                    {r.confidence_score != null ? (r.confidence_score * 100).toFixed(1) + "%" : "-"}
                  </td>
                  <td style={{ padding: "0.4rem", borderBottom: "1px solid #f0f0f0" }}>
                    <button
                      type="button"
                      onClick={() => markReviewed(r.id)}
                      disabled={isReviewed(r.id)}
                      style={{
                        padding: "0.25rem 0.6rem",
                        fontSize: "0.85rem",
                        cursor: isReviewed(r.id) ? "default" : "pointer",
                      }}
                    >
                      {isReviewed(r.id) ? "Reviewed" : "Mark as reviewed"}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}

