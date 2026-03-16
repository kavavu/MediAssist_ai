/**
 * Lab tests list: GET /api/patient/lab-tests. Each item has a "Book" button that POSTs to /api/patient/orders/lab-test.
 */
import React, { useEffect, useState } from "react";
import api from "../services/api.js";

export default function LabTestsPage() {
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionMessage, setActionMessage] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get("/patient/lab-tests");
        setTests(res.data.lab_tests || []);
      } catch (err) {
        setError(err.response?.data?.message || "Failed to load lab tests");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleBook = async (id) => {
    setActionMessage("");
    try {
      const res = await api.post("/patient/orders/lab-test", { lab_test_id: id });
      setActionMessage(res.data.message || "Lab test booked");
    } catch (err) {
      setActionMessage(err.response?.data?.message || "Failed to book lab test");
    }
  };

  return (
    <section>
      <h1>Lab Tests</h1>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {actionMessage && <p style={{ color: "#0055aa" }}>{actionMessage}</p>}
      {!loading && !error && tests.length === 0 && <p>No lab tests available.</p>}
      {!loading && tests.length > 0 && (
        <ul style={{ listStyle: "none", padding: 0, marginTop: "1rem" }}>
          {tests.map((t) => (
            <li
              key={t.id}
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
                <strong>{t.name}</strong>
                <p style={{ margin: "0.25rem 0", color: "#555" }}>{t.description}</p>
                <p style={{ margin: 0 }}>Price: KSh {Number(t.price).toLocaleString("en-KE")}</p>
              </div>
              <div>
                <button
                  onClick={() => handleBook(t.id)}
                  style={{ padding: "0.4rem 0.75rem", cursor: "pointer" }}
                >
                  Book
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

