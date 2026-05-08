import api from "./api";

export const getAnalytics = () => api.get("/admin/analytics");
export const getPendingDoctors = () => api.get("/admin/doctors/pending");
export const approveDoctor = (id) => api.post(`/admin/doctors/${id}/approve`);
