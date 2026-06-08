/**
 * M-Pesa Payment Modal with STK Push integration.
 *
 * Props:
 *   amount          — numeric amount to display (real price)
 *   orderId         — optional order ID
 *   appointmentId   — optional appointment ID
 *   itemName        — display name of the item being paid for
 *   paymentType     — kept for API consistency
 *   onSuccess       — callback when payment completes successfully
 *   onClose         — callback to close the modal
 */
import React, { useState, useCallback, useEffect, useRef } from "react";
import { createPayment, initiateStkPush, getPaymentStatus } from "../services/payment.js";

const STEPS = {
  FORM: "form",
  PROCESSING: "processing",
  STK_SENT: "stk_sent",
  WAITING: "waiting",
  SUCCESS: "success",
  FAILED: "failed",
};

function normalizePhone(phone) {
  let cleaned = (phone || "").trim().replace(/\s+/g, "").replace(/-/g, "");
  if (cleaned.startsWith("+")) cleaned = cleaned.slice(1);
  if (cleaned.startsWith("0")) cleaned = "254" + cleaned.slice(1);
  if (!cleaned.startsWith("254")) cleaned = "254" + cleaned;
  return cleaned;
}

function isValidKenyanPhone(phone) {
  return /^2547\d{8}$/.test(phone) || /^2541\d{8}$/.test(phone);
}

export default function PaymentModal({ amount, orderId, appointmentId, itemName, paymentType, onSuccess, onClose }) {
  const safeAmount = Number.isFinite(Number(amount)) && Number(amount) > 0 ? Number(amount) : 0;
  const [phone, setPhone] = useState("");
  const [step, setStep] = useState(STEPS.FORM);
  const [error, setError] = useState("");
  const [paymentId, setPaymentId] = useState(null);
  const [receipt, setReceipt] = useState(null);
  const pollRef = useRef(null);
  const pollCountRef = useRef(0);

  const clearPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  useEffect(() => {
    return () => clearPolling();
  }, []);

  const startPolling = useCallback((pid) => {
    clearPolling();
    pollCountRef.current = 0;
    pollRef.current = setInterval(async () => {
      pollCountRef.current += 1;
      try {
        const res = await getPaymentStatus(pid);
        const status = res?.data?.payment?.status;
        const p = res?.data?.payment;

        if (status === "success") {
          clearPolling();
          setReceipt({
            transactionId: p.transaction_reference,
            mpesaReceipt: p.mpesa_receipt_number,
            item: itemName || "Service",
            displayedAmount: safeAmount,
            timestamp: p.paid_at || p.updated_at,
            status: "success",
          });
          setStep(STEPS.SUCCESS);
          if (typeof onSuccess === "function") onSuccess();
        } else if (status === "failed" || status === "cancelled") {
          clearPolling();
          setError(p.failure_reason || "Payment was not completed.");
          setStep(STEPS.FAILED);
        }

        // Stop polling after ~2 minutes
        if (pollCountRef.current >= 24) {
          clearPolling();
          setError("We stopped checking automatically. You can retry if needed.");
          setStep(STEPS.FAILED);
        }
      } catch (err) {
        // Silently retry on polling errors
      }
    }, 5000);
  }, [itemName, safeAmount, onSuccess]);

  const handlePay = useCallback(async () => {
    setError("");
    setStep(STEPS.PROCESSING);

    const normalized = normalizePhone(phone || "254712345678");
    if (!isValidKenyanPhone(normalized)) {
      setError("Please enter a valid Kenyan phone number (e.g. 0712345678).");
      setStep(STEPS.FORM);
      return;
    }

    try {
      const payload = {
        amount: safeAmount,
        payment_method: "M-Pesa",
        phone_number: normalized,
      };
      if (orderId) payload.order_id = orderId;
      if (appointmentId) payload.appointment_id = appointmentId;

      const createRes = await createPayment(payload);
      const pid = createRes?.data?.payment?.id;
      if (!pid) {
        throw new Error("Payment creation returned invalid data");
      }
      setPaymentId(pid);

      setStep(STEPS.STK_SENT);

      // Small delay so user sees "STK sent" before switching to waiting
      await new Promise((r) => setTimeout(r, 800));
      setStep(STEPS.WAITING);

      const stkRes = await initiateStkPush(pid, { phone_number: normalized });
      if (!stkRes?.data?.success) {
        throw new Error(stkRes?.data?.message || stkRes?.data?.error || "STK push failed.");
      }

      startPolling(pid);
    } catch (err) {
      const msg =
        err?.response?.data?.error ||
        err?.response?.data?.message ||
        err?.message ||
        "Payment failed. Please try again.";
      setError(msg);
      setStep(STEPS.FAILED);
    }
  }, [safeAmount, phone, orderId, appointmentId, startPolling]);

  const handleRetry = () => {
    setError("");
    setStep(STEPS.FORM);
  };

  const handleClose = useCallback(() => {
    clearPolling();
    if (typeof onClose === "function") {
      onClose();
    }
  }, [onClose]);

  // ---------- Success View ----------
  if (step === STEPS.SUCCESS && receipt) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100">
            <svg className="h-8 w-8 text-emerald-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-lg font-bold text-slate-800">Payment Successful</h3>
          <p className="text-sm text-slate-500 mb-5">Your {receipt.item} payment has been completed.</p>

          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-left space-y-3">
            <div className="flex justify-between">
              <span className="text-xs text-slate-500">Transaction ID</span>
              <span className="text-xs font-semibold text-slate-800">{receipt.transactionId || "N/A"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-slate-500">M-Pesa Receipt</span>
              <span className="text-xs font-semibold text-slate-800">{receipt.mpesaReceipt || "N/A"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-slate-500">Item</span>
              <span className="text-xs font-semibold text-slate-800">{receipt.item}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-slate-500">Amount Paid</span>
              <span className="text-xs font-semibold text-slate-800">KSh {receipt.displayedAmount.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-slate-500">Date</span>
              <span className="text-xs font-semibold text-slate-800">
                {receipt.timestamp ? new Date(receipt.timestamp).toLocaleString() : new Date().toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-slate-500">Status</span>
              <span className="text-xs font-bold text-emerald-600">Success</span>
            </div>
          </div>

          <button
            onClick={handleClose}
            className="mt-5 w-full px-5 py-2.5 bg-emerald-600 text-white font-semibold rounded-xl hover:bg-emerald-700 transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    );
  }

  // ---------- Waiting / STK Sent View ----------
  if (step === STEPS.STK_SENT || step === STEPS.WAITING) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-[#00A650]/10">
            <svg className="h-7 w-7 text-[#00A650]" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17 1H7a2 2 0 00-2 2v18a2 2 0 002 2h10a2 2 0 002-2V3a2 2 0 00-2-2zm-5 19a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm4-5H8V4h8v11z" />
            </svg>
          </div>
          <h3 className="text-base font-bold text-slate-800">Check Your Phone</h3>
          <p className="text-sm text-slate-500 mt-1">
            An M-Pesa STK push has been sent to <span className="font-semibold text-slate-700">{normalizePhone(phone || "254712345678")}</span>.
          </p>
          <p className="text-xs text-slate-400 mt-3">
            Please enter your M-Pesa PIN to complete the payment.
          </p>

          <div className="mt-5 flex items-center justify-center">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-[#00A650] mr-2" />
            <span className="text-sm text-slate-600">
              {step === STEPS.STK_SENT ? "Initiating STK push…" : "Waiting for confirmation…"}
            </span>
          </div>

          <div className="mt-4 rounded-lg bg-amber-50 border border-amber-200 px-3 py-2">
            <p className="text-xs text-amber-700">
              <span className="font-semibold">Demo mode:</span> You will be charged <span className="font-bold">KSh 1</span> regardless of the displayed price.
            </p>
          </div>

          <button
            onClick={handleClose}
            className="mt-4 text-xs text-slate-400 hover:text-slate-600 underline"
          >
            Cancel and close
          </button>
        </div>
      </div>
    );
  }

  // ---------- Failed View ----------
  if (step === STEPS.FAILED) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-red-100">
            <svg className="h-7 w-7 text-red-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h3 className="text-base font-bold text-slate-800">Payment Failed</h3>
          <p className="text-sm text-slate-500 mt-1">{error || "Something went wrong. Please try again."}</p>
          <div className="mt-5 flex gap-3">
            <button
              onClick={handleRetry}
              className="flex-1 px-4 py-2.5 bg-[#00A650] text-white font-semibold rounded-xl hover:bg-[#008f44] transition-colors"
            >
              Retry
            </button>
            <button
              onClick={handleClose}
              className="flex-1 px-4 py-2.5 bg-white border border-slate-200 text-slate-700 font-semibold rounded-xl hover:bg-slate-50 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ---------- Form View ----------
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-[#00A650] flex items-center justify-center">
              <svg className="h-5 w-5 text-white" viewBox="0 0 24 24" fill="currentColor">
                <path d="M17 1H7a2 2 0 00-2 2v18a2 2 0 002 2h10a2 2 0 002-2V3a2 2 0 00-2-2zm-5 19a1.5 1.5 0 110-3 1.5 1.5 0 010 3zm4-5H8V4h8v11z" />
              </svg>
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-800 leading-tight">M-Pesa Payment</h3>
              <p className="text-[10px] text-slate-400 leading-tight">Secure payment via Safaricom</p>
            </div>
          </div>
          <button onClick={handleClose} className="text-slate-400 hover:text-slate-600 text-xl" aria-label="Close">&times;</button>
        </div>

        {/* Amount Card */}
        <div className="rounded-xl bg-gradient-to-br from-[#00A650] to-[#008f44] p-4 mb-5 text-white">
          <p className="text-xs opacity-90">Amount to pay</p>
          <p className="text-2xl font-bold">KSh {safeAmount.toFixed(2)}</p>
          <p className="text-[10px] opacity-80 mt-1">{itemName || "Service"}</p>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-4">
            <p className="text-xs text-red-700">{error}</p>
          </div>
        )}

        {step === STEPS.PROCESSING ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#00A650] mr-2" />
            <span className="text-sm text-slate-600">Processing…</span>
          </div>
        ) : (
          <>
            <label className="block text-xs font-semibold text-slate-700 mb-2">M-Pesa Phone Number</label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="e.g. 0712345678"
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#00A650]/30 focus:border-[#00A650] transition"
            />
            <p className="text-[10px] text-slate-400 mt-1.5">
              Supports: 07XX XXX XXX, 2547XX XXX XXX, +2547XX XXX XXX
            </p>

            <div className="mt-4 flex items-center gap-2 rounded-lg bg-slate-50 border border-slate-100 px-3 py-2">
              <svg className="h-4 w-4 text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span className="text-[10px] text-slate-500">Your transaction is encrypted and secure.</span>
            </div>

            <button
              onClick={handlePay}
              disabled={safeAmount <= 0}
              className="mt-5 w-full px-4 py-3 bg-[#00A650] text-white font-bold rounded-xl hover:bg-[#008f44] disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg shadow-[#00A650]/20"
            >
              Pay KSh {safeAmount.toFixed(2)}
            </button>

            <p className="text-center text-[10px] text-slate-400 mt-3">
              By clicking Pay, you agree to receive an M-Pesa STK push.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
