/**
 * Medicines list: GET /api/patient/medicines. "Order" button POSTs to /api/patient/orders/medicine. Shows stock and prescription flag.
 */
import React, { useEffect, useState } from "react";
import api from "../services/api.js";

export default function MedicinesPage() {
  const [medicines, setMedicines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionMessage, setActionMessage] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get("/patient/medicines");
        setMedicines(res.data.medicines || []);
      } catch (err) {
        setError(err.response?.data?.message || "Failed to load medicines");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleOrder = async (id) => {
    setActionMessage("");
    try {
      const res = await api.post("/patient/orders/medicine", { medicine_id: id });
      setActionMessage(res.data.message || "Medicine ordered");
    } catch (err) {
      setActionMessage(err.response?.data?.message || "Failed to order medicine");
    }
  };

  return (
    <section>
      <h1>Medicines</h1>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {actionMessage && <p style={{ color: "#0055aa" }}>{actionMessage}</p>}
      {!loading && !error && medicines.length === 0 && <p>No medicines available.</p>}
      {!loading && medicines.length > 0 && (
        <ul style={{ listStyle: "none", padding: 0, marginTop: "1rem" }}>
          {medicines.map((m) => (
            <li
              key={m.id}
              style={{
                border: "1px solid #eee",
                borderRadius: "6px",
                padding: "0.75rem",
                marginBottom: "0.5rem",
                display: "flex",
                justifyContent: "space-between",
                gap: "1rem"
              }}
            >
              <div>
                <strong>{m.name}</strong>
                <p style={{ margin: "0.25rem 0", color: "#555" }}>{m.manufacturer}</p>
                <p style={{ margin: 0 }}>
                  Price: KSh {Number(m.price).toLocaleString("en-KE")}{" "}
                  {m.requires_prescription && (
                    <span style={{ color: "#aa0000" }}>(Prescription required)</span>
                  )}
                </p>
                <p style={{ margin: 0 }}>In stock: {m.stock_level}</p>
              </div>
              <div>
                <button
                  onClick={() => handleOrder(m.id)}
                  disabled={m.stock_level < 1}
                  style={{ padding: "0.4rem 0.75rem", cursor: m.stock_level < 1 ? "not-allowed" : "pointer" }}
                >
                  {m.stock_level < 1 ? "Out of stock" : "Order"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

