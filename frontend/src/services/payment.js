import api from "./api";

export const createPayment = (payload) =>
  api.post("/payments/create", payload);

export const initiateStkPush = (paymentId, payload) =>
  api.post(`/payments/${paymentId}/stk-push`, payload);

export const getPaymentStatus = (paymentId) =>
  api.get(`/payments/${paymentId}/status`);

export const completePayment = (paymentId) =>
  api.post(`/payments/${paymentId}/complete`);

export const getMyPayments = () =>
  api.get("/payments/my-payments");
