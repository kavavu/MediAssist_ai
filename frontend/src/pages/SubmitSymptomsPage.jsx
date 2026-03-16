/**
 * Submit symptoms page.
 *
 * - Textarea for symptom input
 * - POSTs to /api/predict
 * - Renders top-3 predicted conditions as cards
 * - Shows a medical disclaimer under the results
 */
import React, { useState } from "react";
import api from "../services/api.js";

export default function SubmitSymptomsPage() {
  const [symptoms, setSymptoms] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const res = await api.post("/predict", { symptoms_text: symptoms });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.message || "Prediction failed");
    } finally {
      setLoading(false);
    }
  };

  const predictions = result?.predictions || [];

  return (
    <section>
      <h1>Submit Symptoms</h1>
      <p>Describe your symptoms in your own words.</p>
      <form
        onSubmit={handleSubmit}
        style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxWidth: "520px" }}
      >
        <textarea
          value={symptoms}
          onChange={(e) => setSymptoms(e.target.value)}
          required
          rows={5}
          style={{ width: "100%", padding: "0.5rem" }}
          placeholder="e.g. headache, fever, body aches for two days..."
        />
        {error && <p style={{ color: "red" }}>{error}</p>}
        <button type="submit" disabled={loading} style={{ padding: "0.5rem 0.75rem", width: "180px" }}>
          {loading ? "Predicting..." : "Submit & View Possible Conditions"}
        </button>
      </form>

      {result && (
        <div style={{ marginTop: "1.5rem" }}>
          <h2>Possible Conditions</h2>
          {predictions.length === 0 && (
            <p>No confident prediction could be generated. Please consult a doctor.</p>
          )}

          {predictions.length > 0 && (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                gap: "0.75rem",
                marginTop: "0.75rem",
              }}
            >
              {predictions.map((p) => (
                <article
                  key={p.condition}
                  style={{
                    border: "1px solid #ddd",
                    borderRadius: "6px",
                    padding: "0.75rem 0.9rem",
                    background: "#fafafa",
                  }}
                >
                  <h3 style={{ margin: "0 0 0.25rem 0", fontSize: "1rem" }}>{p.condition}</h3>
                  <p style={{ margin: 0 }}>
                    <strong>Confidence:</strong> {(p.confidence * 100).toFixed(1)}%
                  </p>
                </article>
              ))}
            </div>
          )}

          {result.recommendation && (
            <p style={{ marginTop: "1rem", fontWeight: 500 }}>{result.recommendation}</p>
          )}

          <p style={{ marginTop: "0.75rem", fontSize: "0.9rem", color: "#555" }}>
            <strong>Disclaimer:</strong> This AI prediction is not a medical diagnosis. Please consult a qualified
            doctor.
          </p>
        </div>
      )}
    </section>
  );
}
