/**
 * Patient dashboard: fetches GET /api/patient/predictions and shows a table of
 * past symptom reports (date, symptoms, primary condition, confidence).
 */
import React, { useEffect, useState } from "react";
import api from "../services/api.js";

export default function PatientDashboard() {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get("/patient/predictions");
        setPredictions(res.data.predictions || []);
      } catch (err) {
        setError(err.response?.data?.message || "Failed to load prediction history");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <section>
      <h1>Patient Dashboard</h1>
      <p>View your recent symptom checker results.</p>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {!loading && !error && predictions.length === 0 && <p>No predictions yet.</p>}
      {!loading && predictions.length > 0 && (
        <table style={{ width: "100%", borderCollapse: "collapse", marginTop: "1rem" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.4rem" }}>Date</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.4rem" }}>Symptoms</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.4rem" }}>Predicted Condition</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: "0.4rem" }}>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {predictions.map((p) => (
              <tr key={p.id}>
                <td style={{ padding: "0.4rem", borderBottom: "1px solid #f0f0f0" }}>
                  {p.created_at ? new Date(p.created_at).toLocaleString() : "-"}
                </td>
                <td style={{ padding: "0.4rem", borderBottom: "1px solid #f0f0f0" }}>{p.symptoms_text}</td>
                <td style={{ padding: "0.4rem", borderBottom: "1px solid #f0f0f0" }}>
                  {p.predicted_condition || "-"}
                </td>
                <td style={{ padding: "0.4rem", borderBottom: "1px solid #f0f0f0" }}>
                  {p.confidence_score != null ? (p.confidence_score * 100).toFixed(1) + "%" : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

