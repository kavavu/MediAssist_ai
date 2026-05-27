/**
 * Medicines list: GET /api/patient/medicines. "Order" button POSTs to /api/patient/orders/medicine. Shows stock and prescription flag.
 * After ordering, user can pay for the order.
 */
import React, { useEffect, useState } from "react";
import api from "../services/api.js";
import PaymentModal from "../components/PaymentModal.jsx";



export default function MedicinesPage() {
  const [medicines, setMedicines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [orderingId, setOrderingId] = useState(null);
  const [payOrder, setPayOrder] = useState(null);
  const [payItemName, setPayItemName] = useState("");

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
    setOrderingId(id);
    setActionMessage("");
    try {
      const res = await api.post("/patient/orders/medicine", { medicine_id: id });
      const order = res.data.order;
      setActionMessage(res.data.message || "Medicine ordered successfully");
      if (order) {
        setPayOrder(order);
        const med = medicines.find((m) => m.id === id);
        setPayItemName(med?.name || "Medicine");
      }
    } catch (err) {
      setActionMessage(err.response?.data?.message || "Failed to order medicine");
    } finally {
      setOrderingId(null);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Medicines</h1>
        <p className="text-sm text-slate-500 mt-1">
          Browse available medicines and place orders online.
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
          <span className="ml-3 text-slate-500 text-sm">Loading medicines...</span>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && medicines.length === 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
          <p className="text-slate-500 text-sm">No medicines available at the moment.</p>
        </div>
      )}

      {/* Medicines Grid */}
      {!loading && medicines.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {medicines.map((m) => {
            const outOfStock = m.stock_level < 1;
            return (
              <div
                key={m.id}
                className={`bg-white rounded-xl border shadow-sm p-5 flex flex-col justify-between hover:shadow-md transition-shadow ${
                  outOfStock ? "border-slate-200 opacity-70" : "border-slate-200"
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="font-bold text-slate-800">{m.name}</h3>
                    <span className="text-sm font-bold text-primary-700 bg-primary-50 px-2.5 py-1 rounded-lg border border-primary-100 whitespace-nowrap">
                      KSh {Number(m.price).toLocaleString("en-KE")}
                    </span>
                  </div>
                  <p className="text-sm text-slate-500 mt-1">{m.manufacturer}</p>

                  {m.requires_prescription && (
                    <div className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-red-600 bg-red-50 px-2 py-1 rounded border border-red-100">
                      <span>📝</span> Prescription required
                    </div>
                  )}

                  <div className="mt-3 flex items-center gap-3 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <span>📦</span> In stock:{" "}
                      <span className={outOfStock ? "text-red-600 font-bold" : "text-emerald-600 font-bold"}>
                        {m.stock_level}
                      </span>
                    </span>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <span>💊</span> Pharmaceutical
                  </span>
                  <button
                    onClick={() => handleOrder(m.id)}
                    disabled={outOfStock || orderingId === m.id}
                    className={`inline-flex items-center text-sm font-semibold px-4 py-2 rounded-lg transition-colors ${
                      outOfStock
                        ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                        : "bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    }`}
                  >
                    {orderingId === m.id ? (
                      <>
                        <span className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white mr-1.5" />
                        Ordering...
                      </>
                    ) : outOfStock ? (
                      "Out of Stock"
                    ) : (
                      "Order"
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {payOrder && (
        <PaymentModal
          amount={Number(payOrder.total_amount || payOrder.price || 0)}
          orderId={payOrder.id}
          appointmentId={null}
          itemName={payItemName || "Medicine"}
          paymentType="medicine"
          onSuccess={() => { setPayOrder(null); setPayItemName(""); setActionMessage("Payment completed successfully!"); }}
          onClose={() => { setPayOrder(null); setPayItemName(""); }}
        />
      )}
    </div>
  );
}
