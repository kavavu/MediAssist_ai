/**
 * Shared PaymentModal component used by AppointmentsPage, LabTestsPage, and MedicinesPage.
 *
 * Props:
 *   amount          — numeric amount to charge
 *   orderId         — optional order ID (for lab/medicine payments)
 *   appointmentId   — optional appointment ID (for appointment payments)
 *   itemName        — display name of the item being paid for
 *   paymentType     — kept for API consistency and future use
 *   onSuccess       — callback when payment completes successfully
 *   onClose         — callback to close the modal
 */
import React, { useState, useCallback } from "react";
import { createPayment, completePayment } from "../services/payment.js";

export default function PaymentModal({ amount, orderId, appointmentId, itemName, paymentType, onSuccess, onClose }) {
  // Defensive: ensure amount is a valid number
  const safeAmount = Number.isFinite(Number(amount)) && Number(amount) > 0 ? Number(amount) : 0;
  const [method, setMethod] = useState("M-Pesa");
  const [step, setStep] = useState("form");
  const [error, setError] = useState("");

  const handlePay = useCallback(async () => {
    setError("");
    setStep("processing");
    try {
      const payload = {
        amount: safeAmount,
        payment_method: method,
      };
      if (orderId) payload.order_id = orderId;
      if (appointmentId) payload.appointment_id = appointmentId;

      const createRes = await createPayment(payload);
      const paymentId = createRes?.data?.payment?.id;
      if (!paymentId) {
        throw new Error("Payment creation returned invalid data");
      }

      // Simulate processing delay for demo
      await new Promise((r) => setTimeout(r, 1200));

      await completePayment(paymentId);
      setStep("success");
      if (typeof onSuccess === "function") {
        onSuccess();
      }
    } catch (err) {
      const msg =
        err?.response?.data?.error ||
        err?.response?.data?.message ||
        err?.message ||
        "Payment failed. Please try again.";
      setError(msg);
      setStep("form");
    }
  }, [safeAmount, method, orderId, appointmentId, onSuccess]);

  const handleClose = useCallback(() => {
    if (typeof onClose === "function") {
      onClose();
    }
  }, [onClose]);

  if (step === "success") {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
        <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6 text-center">
          <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-2xl mx-auto mb-3">✓</div>
          <h3 className="text-lg font-bold text-slate-800 mb-1">Payment Successful</h3>
          <p className="text-sm text-slate-500 mb-4">Your {itemName || "payment"} has been completed.</p>
          <button
            onClick={handleClose}
            className="px-5 py-2 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-slate-800">Complete Payment</h3>
          <button onClick={handleClose} className="text-slate-400 hover:text-slate-600 text-lg" aria-label="Close">&times;</button>
        </div>

        <div className="bg-slate-50 rounded-lg p-3 mb-4 border border-slate-100">
          <p className="text-xs text-slate-500">Amount due</p>
          <p className="text-sm font-semibold text-slate-800 mt-0.5">KSh {safeAmount.toFixed(2)}</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-3">
            <p className="text-xs text-red-700">{error}</p>
          </div>
        )}

        {step === "processing" ? (
          <div className="flex items-center justify-center py-6">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mr-2" />
            <span className="text-sm text-slate-600">Processing payment...</span>
          </div>
        ) : (
          <>
            <label className="block text-xs font-medium text-slate-700 mb-2">Payment Method</label>
            <div className="space-y-2 mb-4">
              {["M-Pesa", "Card", "Cash"].map((m) => (
                <button
                  key={m}
                  onClick={() => setMethod(m)}
                  className={`w-full text-left px-3 py-2 rounded-lg border text-sm font-medium transition-colors ${
                    method === m
                      ? "bg-primary-50 border-primary-500 text-primary-700"
                      : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  {m === "M-Pesa" ? "📱" : m === "Card" ? "💳" : "💵"} {m}
                </button>
              ))}
            </div>
            <button
              onClick={handlePay}
              disabled={safeAmount <= 0 || step === "processing"}
              className="w-full px-4 py-2.5 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Pay KSh {safeAmount.toFixed(2)}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
