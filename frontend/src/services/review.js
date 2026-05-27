import api from "./api";

export const createReview = (payload) =>
  api.post("/reviews/create", payload);

export const getDoctorReviews = (doctorId) =>
  api.get(`/reviews/doctor/${doctorId}`);

export const getDoctorRatingSummary = (doctorId) =>
  api.get(`/reviews/doctor/${doctorId}/summary`);
