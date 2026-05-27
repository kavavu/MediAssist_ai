import api from "./api";

export const createPayment = (payload) =>
  api.post("/payments/create", payload);

export const completePayment = (paymentId) =>
  api.post(`/payments/${paymentId}/complete`);

export const getMyPayments = () =>
  api.get("/payments/my-payments");
