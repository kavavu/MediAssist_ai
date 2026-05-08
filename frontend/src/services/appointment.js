import api from "./api";

export const getAvailableSlots = (doctorId, date) =>
  api.get(`/appointments/doctor/${doctorId}/available-slots`, { params: { date } });

export const bookAppointment = (payload) =>
  api.post("/appointments/book", payload);

export const getPatientAppointments = () =>
  api.get("/appointments/patient");

export const getDoctorAppointments = () =>
  api.get("/appointments/doctor");

export const cancelAppointment = (appointmentId) =>
  api.post(`/appointments/${appointmentId}/cancel`);
