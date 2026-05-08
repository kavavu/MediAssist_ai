import api from "./api";

export const createConsultation = (payload) =>
  api.post("/consultation/create", payload);

export const getPatientConsultations = () =>
  api.get("/consultation/patient");

export const getDoctorConsultations = () =>
  api.get("/consultation/doctor");

export const respondToConsultation = (consultationId, payload) =>
  api.post(`/consultation/respond/${consultationId}`, payload);

export const editResponse = (consultationId, payload) =>
  api.post(`/consultation/respond/${consultationId}/edit`, payload);

export const sendFollowUp = (consultationId, payload) =>
  api.post(`/consultation/followup/${consultationId}`, payload);

export const resolveConsultation = (consultationId) =>
  api.post(`/consultation/resolve/${consultationId}`);

export const getDoctorStats = () =>
  api.get("/consultation/stats");

export const getAiResponse = (consultationId) =>
  api.get(`/consultation/ai-response/${consultationId}`);

export const getConsultationHistory = (consultationId) =>
  api.get(`/consultation/history/${consultationId}`);

export const getDoctorsPreview = () =>
  api.get("/consultation/doctors/preview");

export const getDoctorPublicStats = (doctorId) =>
  api.get(`/consultation/doctors/${doctorId}/stats`);

export const getRecommendedDoctor = (condition) =>
  api.get("/consultation/doctors/recommend", { params: { condition } });
