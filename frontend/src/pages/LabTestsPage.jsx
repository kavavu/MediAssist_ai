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
  const [bookingId, setBookingId] = useState(null);

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
    setBookingId(id);
    setActionMessage("");
    try {
      const res = await api.post("/patient/orders/lab-test", { lab_test_id: id });
      setActionMessage(res.data.message || "Lab test booked successfully");
    } catch (err) {
      setActionMessage(err.response?.data?.message || "Failed to book lab test");
    } finally {
      setBookingId(null);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Lab Tests</h1>
        <p className="text-sm text-slate-500 mt-1">
          Browse available laboratory tests and book appointments online.
        </p>
      </div>

      {/* Alerts */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 mb-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
      {actionMessage && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 mb-4">
          <p className="text-sm text-blue-700">{actionMessage}</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
          <span className="ml-3 text-slate-500 text-sm">Loading lab tests...</span>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && tests.length === 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
          <p className="text-slate-500 text-sm">No lab tests available at the moment.</p>
        </div>
      )}

      {/* Tests Grid */}
      {!loading && tests.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {tests.map((t) => (
            <div
              key={t.id}
              className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col justify-between hover:shadow-md transition-shadow"
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <h3 className="font-bold text-slate-800">{t.name}</h3>
                  <span className="text-sm font-bold text-primary-700 bg-primary-50 px-2.5 py-1 rounded-lg border border-primary-100 whitespace-nowrap">
                    KSh {Number(t.price).toLocaleString("en-KE")}
                  </span>
                </div>
                <p className="text-sm text-slate-500 mt-2 leading-relaxed">{t.description}</p>
              </div>
              <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <span>🧪</span> Laboratory Test
                </span>
                <button
                  onClick={() => handleBook(t.id)}
                  disabled={bookingId === t.id}
                  className="inline-flex items-center bg-primary-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {bookingId === t.id ? (
                    <>
                      <span className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white mr-1.5" />
                      Booking...
                    </>
                  ) : (
                    "Book"
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
