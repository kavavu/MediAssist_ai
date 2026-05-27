import api from "./api";

export const getDashboardStats = () => api.get("/admin/dashboard");
export const getDoctors = () => api.get("/admin/doctors");
export const verifyDoctor = (id) => api.post(`/admin/doctors/${id}/verify`);
export const unverifyDoctor = (id) => api.post(`/admin/doctors/${id}/unverify`);
export const toggleAvailability = (id) => api.post(`/admin/doctors/${id}/availability`);
export const getConsultations = () => api.get("/admin/consultations");
export const getPayments = () => api.get("/admin/payments");
export const getReviews = () => api.get("/admin/reviews");


