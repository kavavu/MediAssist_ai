"""
Appointment business logic (no HTTP here).

- Generate mock available slots
- Create / cancel appointments
- Fetch patient or doctor appointments
"""
from datetime import date, datetime
from typing import List, Optional

from ..extensions import db
from ..models import Appointment, User

# Mock daily slots
DEFAULT_SLOTS = [
    "09:00 AM",
    "10:00 AM",
    "11:00 AM",
    "02:00 PM",
    "03:00 PM",
]


def get_available_slots(doctor_id: int, appointment_date: date) -> List[str]:
    """
    Return mock slots for a doctor on a given date,
    excluding slots already booked (status != cancelled).
    """
    booked = (
        Appointment.query.filter_by(doctor_id=doctor_id, appointment_date=appointment_date)
        .filter(Appointment.status != "cancelled")
        .with_entities(Appointment.appointment_time)
        .all()
    )
    booked_times = {b[0] for b in booked}
    return [slot for slot in DEFAULT_SLOTS if slot not in booked_times]


def create_appointment(
    patient_id: int,
    doctor_id: int,
    appointment_date: date,
    appointment_time: str,
    notes: Optional[str] = None,
) -> Appointment:
    """
    Book an appointment for a patient with a doctor.
    Raises ValueError if doctor missing, slot taken, or patient is not a patient.
    """
    doctor = User.query.get(doctor_id)
    if doctor is None:
        raise ValueError("Doctor not found")
    if doctor.role != "doctor":
        raise ValueError("Selected user is not a doctor")

    patient = User.query.get(patient_id)
    if patient is None or patient.role != "patient":
        raise ValueError("Invalid patient")

    existing = (
        Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
        )
        .filter(Appointment.status != "cancelled")
        .first()
    )
    if existing:
        raise ValueError("This slot is already booked")

    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        status="scheduled",
        notes=(notes or "").strip() or None,
    )
    db.session.add(appointment)
    db.session.commit()
    db.session.refresh(appointment)
    return appointment


def get_patient_appointments(patient_id: int) -> List[Appointment]:
    """Return all appointments for a patient, newest first."""
    return (
        Appointment.query.filter_by(patient_id=patient_id)
        .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
        .all()
    )


def get_doctor_appointments(doctor_id: int) -> List[Appointment]:
    """Return all appointments for a doctor, newest first."""
    return (
        Appointment.query.filter_by(doctor_id=doctor_id)
        .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
        .all()
    )


def cancel_appointment(appointment_id: int, user_id: int, user_role: str) -> Appointment:
    """
    Cancel an appointment.
    Patients may only cancel their own appointments.
    Doctors may only cancel their own appointments.
    Raises ValueError if not found or not authorized.
    """
    appointment = Appointment.query.get(appointment_id)
    if appointment is None:
        raise ValueError("Appointment not found")

    if user_role == "patient" and appointment.patient_id != user_id:
        raise ValueError("Not authorized to cancel this appointment")
    if user_role == "doctor" and appointment.doctor_id != user_id:
        raise ValueError("Not authorized to cancel this appointment")

    appointment.status = "cancelled"
    db.session.commit()
    db.session.refresh(appointment)
    return appointment
