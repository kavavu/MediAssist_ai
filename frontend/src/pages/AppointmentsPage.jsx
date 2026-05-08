import React, { useEffect, useState, useCallback } from "react";
import { getCurrentUser } from "../services/auth.js";
import {
  getAvailableSlots,
  bookAppointment,
  getPatientAppointments,
  getDoctorAppointments,
  cancelAppointment,
} from "../services/appointment.js";
import api from "../services/api.js";

/* ------------------------------------------------------------------ */
/* Helper Components                                                  */
/* ------------------------------------------------------------------ */

const StatusBadge = ({ status }) => {
  const colors = {
    scheduled: "bg-blue-100 text-blue-700 border-blue-200",
    completed: "bg-emerald-100 text-emerald-700 border-emerald-200",
    cancelled: "bg-red-100 text-red-700 border-red-200",
  };
  return (
    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${colors[status] || colors.scheduled}`}>
      {status}
    </span>
  );
};

const SectionTitle = ({ children }) => (
  <h2 className="text-lg font-bold text-slate-800 mb-4">{children}</h2>
);

const Alert = ({ type, message, onClose }) => {
  if (!message) return null;
  const styles = {
    success: "bg-emerald-50 border-emerald-200 text-emerald-800",
    error: "bg-red-50 border-red-200 text-red-800",
  };
  return (
    <div className={`rounded-lg px-4 py-3 border mb-4 flex items-start justify-between ${styles[type] || styles.error}`}>
      <span className="text-sm">{message}</span>
      {onClose && (
        <button onClick={onClose} className="text-sm font-bold ml-4 hover:opacity-70">&times;</button>
      )}
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Patient Booking Section                                            */
/* ------------------------------------------------------------------ */

const PatientBooking = ({ onBooked }) => {
  const [doctors, setDoctors] = useState([]);
  const [selectedDoctor, setSelectedDoctor] = useState("");
  const [selectedDate, setSelectedDate] = useState("");
  const [slots, setSlots] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState("");
  const [notes, setNotes] = useState("");
  const [loadingDoctors, setLoadingDoctors] = useState(true);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [booking, setBooking] = useState(false);
  const [alert, setAlert] = useState(null);

  const fetchDoctors = useCallback(async () => {
    try {
      const res = await api.get("/consultation/doctors/preview");
      setDoctors(res.data.doctors || []);
    } catch (err) {
      setAlert({ type: "error", message: "Failed to load doctors." });
    } finally {
      setLoadingDoctors(false);
    }
  }, []);

  useEffect(() => {
    fetchDoctors();
  }, [fetchDoctors]);

  useEffect(() => {
    if (!selectedDoctor || !selectedDate) {
      setSlots([]);
      setSelectedSlot("");
      return;
    }
    let cancelled = false;
    const load = async () => {
      setLoadingSlots(true);
      try {
        const res = await getAvailableSlots(selectedDoctor, selectedDate);
        if (!cancelled) setSlots(res.data.slots || []);
      } catch (err) {
        if (!cancelled) setAlert({ type: "error", message: err.response?.data?.error || "Failed to load slots" });
      } finally {
        if (!cancelled) setLoadingSlots(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [selectedDoctor, selectedDate]);

  const handleBook = async () => {
    if (!selectedDoctor || !selectedDate || !selectedSlot) {
      setAlert({ type: "error", message: "Please select a doctor, date, and time slot." });
      return;
    }
    setBooking(true);
    try {
      await bookAppointment({
        doctor_id: selectedDoctor,
        appointment_date: selectedDate,
        appointment_time: selectedSlot,
        notes,
      });
      setAlert({ type: "success", message: "Appointment booked successfully!" });
      setSelectedSlot("");
      setNotes("");
      onBooked();
    } catch (err) {
      setAlert({ type: "error", message: err.response?.data?.error || "Booking failed" });
    } finally {
      setBooking(false);
    }
  };

  const today = new Date().toISOString().split("T")[0];

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-6">
      <SectionTitle>Book an Appointment</SectionTitle>
      <Alert type={alert?.type} message={alert?.message} onClose={() => setAlert(null)} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Select Doctor</label>
          {loadingDoctors ? (
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600" />
              Loading doctors...
            </div>
          ) : (
            <select
              value={selectedDoctor}
              onChange={(e) => setSelectedDoctor(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
            >
              <option value="">-- Choose a doctor --</option>
              {doctors.map((d) => (
                <option key={d.id} value={d.id}>
                  Dr. {d.name} {d.specialization ? `(${d.specialization})` : ""}
                </option>
              ))}
            </select>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Select Date</label>
          <input
            type="date"
            min={today}
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="w-full px-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      {selectedDoctor && selectedDate && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-slate-700 mb-2">Available Slots</label>
          {loadingSlots ? (
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600" />
              Loading slots...
            </div>
          ) : slots.length === 0 ? (
            <p className="text-sm text-slate-500">No available slots for this date.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {slots.map((slot) => (
                <button
                  key={slot}
                  onClick={() => setSelectedSlot(slot)}
                  className={`px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${
                    selectedSlot === slot
                      ? "bg-primary-600 text-white border-primary-600"
                      : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                  }`}
                >
                  {slot}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {selectedSlot && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-slate-700 mb-1">Notes (optional)</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            placeholder="Any additional notes for the doctor..."
            className="w-full px-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      )}

      <button
        onClick={handleBook}
        disabled={booking || !selectedSlot}
        className="px-5 py-2.5 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
      >
        {booking ? "Booking..." : "Book Appointment"}
      </button>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Appointment List                                                   */
/* ------------------------------------------------------------------ */

const AppointmentList = ({ appointments, loading, onCancel, role }) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        <span className="ml-3 text-slate-500 text-sm">Loading appointments...</span>
      </div>
    );
  }

  if (appointments.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
        <p className="text-slate-500 text-sm">No appointments yet.</p>
        <p className="text-slate-400 text-xs mt-1">
          {role === "patient" ? "Book your first appointment above." : "Appointments will appear here when patients book."}
        </p>
      </div>
    );
  }

  const formatDate = (iso) => {
    if (!iso) return "";
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { weekday: "short", year: "numeric", month: "short", day: "numeric" });
  };

  return (
    <div className="space-y-3">
      {appointments.map((appt) => (
        <div
          key={appt.id}
          className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3"
        >
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <StatusBadge status={appt.status} />
              <span className="text-xs text-slate-400">{formatDate(appt.appointment_date)}</span>
              <span className="text-xs text-slate-500 font-medium">{appt.appointment_time}</span>
            </div>
            <p className="text-sm text-slate-800">
              {role === "patient" ? (
                <>
                  <span className="font-semibold">Dr. {appt.doctor_name}</span>
                  <span className="text-slate-500"> — Appointment</span>
                </>
              ) : (
                <>
                  <span className="font-semibold">{appt.patient_name}</span>
                  <span className="text-slate-500"> — Appointment</span>
                </>
              )}
            </p>
            {appt.notes && (
              <p className="text-xs text-slate-500 mt-1 italic">Notes: {appt.notes}</p>
            )}
          </div>
          {appt.status === "scheduled" && (
            <button
              onClick={() => onCancel(appt.id)}
              className="px-3 py-1.5 bg-white border border-red-200 text-red-600 text-xs font-semibold rounded-lg hover:bg-red-50 transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
      ))}
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Main Page                                                          */
/* ------------------------------------------------------------------ */

export default function AppointmentsPage() {
  const user = getCurrentUser();
  const role = user?.role;

  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState(null);

  const fetchAppointments = useCallback(async () => {
    setLoading(true);
    try {
      if (role === "patient") {
        const res = await getPatientAppointments();
        setAppointments(res.data.appointments || []);
      } else if (role === "doctor") {
        const res = await getDoctorAppointments();
        setAppointments(res.data.appointments || []);
      }
    } catch (err) {
      setAlert({ type: "error", message: err.response?.data?.error || "Failed to load appointments" });
    } finally {
      setLoading(false);
    }
  }, [role]);

  useEffect(() => {
    fetchAppointments();
  }, [fetchAppointments]);

  const handleCancel = async (id) => {
    if (!window.confirm("Are you sure you want to cancel this appointment?")) return;
    try {
      await cancelAppointment(id);
      setAlert({ type: "success", message: "Appointment cancelled." });
      fetchAppointments();
    } catch (err) {
      setAlert({ type: "error", message: err.response?.data?.error || "Failed to cancel appointment" });
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-6">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-slate-800">Appointments</h1>
        <p className="text-sm text-slate-500 mt-1">
          {role === "patient"
            ? "Book and manage your appointments with doctors"
            : "View your upcoming patient appointments"}
        </p>
      </div>

      <Alert type={alert?.type} message={alert?.message} onClose={() => setAlert(null)} />

      {role === "patient" && <PatientBooking onBooked={fetchAppointments} />}

      <SectionTitle>{role === "patient" ? "My Appointments" : "Upcoming Appointments"}</SectionTitle>
      <AppointmentList appointments={appointments} loading={loading} onCancel={handleCancel} role={role} />
    </div>
  );
}
