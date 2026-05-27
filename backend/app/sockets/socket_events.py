"""
Socket.IO event handlers for MediAssist AI.

Handles:
- Connection / disconnection (with mandatory JWT auth)
- Room joining (consultation rooms, doctor rooms) with authorization
- Error handling and safe error emission

SECURITY NOTES:
- All connections MUST provide a valid JWT token on connect
- Room joins are validated against DB (user must be part of consultation)
- All handlers are wrapped in try/except to prevent crashes
- Disconnect cleanup is defensive against missing session data

NOTE: No business logic here. Emissions are done via emitters.py from the service layer.
"""
import logging

from flask import request
from flask_socketio import join_room, leave_room, disconnect

from .socket_manager import socketio

logger = logging.getLogger(__name__)

# In-memory mapping of sid -> user info (populated on connect)
_socket_sessions = {}


def _get_sid() -> str:
    return request.sid


def _room_consultation(consultation_id: int) -> str:
    return f"consultation_{consultation_id}"


def _room_doctor(doctor_id: int) -> str:
    return f"doctor_{doctor_id}"


def _emit_error(message: str) -> None:
    """Emit a safe error message to the current client."""
    try:
        socketio.emit("error", {"message": message}, room=_get_sid())
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Connection / Disconnection
# ---------------------------------------------------------------------------

@socketio.on("connect")
def handle_connect():
    """
    Handle client connection.

    SECURITY: Extract and validate JWT token immediately from auth payload.
    If token is missing or invalid -> disconnect immediately.

    The client should pass the token via the 'auth' option:
      io({ auth: { token: "<jwt>" } })
    """
    sid = _get_sid()

    try:
        # Extract token from auth payload (sent by client during handshake)
        token = (request.auth or {}).get("token", "")

        if not token:
            logger.warning(f"[Socket] Connection rejected for {sid}: no token")
            disconnect(sid)
            return

        # Validate JWT token
        from flask_jwt_extended import decode_token
        from ..services.auth_service import get_user_by_id

        decoded = decode_token(token)
        user_id = int(decoded.get("sub"))
        user = get_user_by_id(user_id)

        if not user:
            logger.warning(f"[Socket] Connection rejected for {sid}: user not found")
            disconnect(sid)
            return

        # Store authenticated session
        _socket_sessions[sid] = {
            "user_id": user_id,
            "role": user.role,
            "rooms": set(),
        }

        # Auto-join doctor room if user is a doctor
        if user.role == "doctor":
            doctor_room = _room_doctor(user_id)
            join_room(doctor_room)
            _socket_sessions[sid]["rooms"].add(doctor_room)
            logger.info(f"[Socket] Doctor {user_id} auto-joined room {doctor_room}")

        logger.info(f"[Socket] Authenticated connect: user_id={user_id}, role={user.role}, sid={sid}")

    except Exception as e:
        logger.error(f"[Socket] Connection rejected for {sid}: {e}")
        try:
            disconnect(sid)
        except Exception:
            pass


@socketio.on("disconnect")
def handle_disconnect():
    """Clean up session on disconnect."""
    sid = _get_sid()
    try:
        session = _socket_sessions.pop(sid, None)
        if session:
            user_id = session.get("user_id")
            rooms = list(session.get("rooms", set()))
            for room in rooms:
                try:
                    leave_room(room, sid=sid)
                except Exception:
                    pass
            logger.info(f"[Socket] Disconnected: user_id={user_id}, sid={sid}, rooms_left={len(rooms)}")
        else:
            logger.info(f"[Socket] Disconnected: unauthenticated sid={sid}")
    except Exception as e:
        logger.error(f"[Socket] Error during disconnect for {sid}: {e}")


# ---------------------------------------------------------------------------
# Authentication (fallback for clients that connect then authenticate)
# ---------------------------------------------------------------------------

@socketio.on("authenticate")
def handle_authenticate(data):
    """
    Fallback authentication for clients that couldn't send token during handshake.

    Expected data: { token: "<jwt_access_token>" }

    If the client is already authenticated (from connect handler), this is a no-op.
    """
    sid = _get_sid()
    session = _socket_sessions.get(sid, {})

    # Already authenticated during connect
    if session.get("user_id"):
        logger.debug(f"[Socket] Authenticate called but already authenticated: sid={sid}")
        return

    token = (data or {}).get("token", "")

    if not token:
        logger.warning(f"[Socket] Auth failed for {sid}: no token provided")
        _emit_error("Authentication required: no token provided")
        disconnect(sid)
        return

    try:
        from flask_jwt_extended import decode_token
        from ..services.auth_service import get_user_by_id

        decoded = decode_token(token)
        user_id = int(decoded.get("sub"))
        user = get_user_by_id(user_id)

        if not user:
            logger.warning(f"[Socket] Auth failed for {sid}: user not found")
            _emit_error("Authentication failed: user not found")
            disconnect(sid)
            return

        _socket_sessions[sid] = {
            "user_id": user_id,
            "role": user.role,
            "rooms": set(),
        }

        if user.role == "doctor":
            doctor_room = _room_doctor(user_id)
            join_room(doctor_room)
            _socket_sessions[sid]["rooms"].add(doctor_room)
            logger.info(f"[Socket] Doctor {user_id} auto-joined room {doctor_room}")

        logger.info(f"[Socket] Authenticated via event: user_id={user_id}, role={user.role}, sid={sid}")

    except Exception as e:
        logger.error(f"[Socket] Auth failed for {sid}: {e}")
        _emit_error("Authentication failed: invalid token")
        try:
            disconnect(sid)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Room Management (with authorization)
# ---------------------------------------------------------------------------

@socketio.on("join_consultation")
def handle_join_consultation(data):
    """
    Join a consultation room.
    Expected data: { consultation_id: <int> }

    AUTHORIZATION: Validates that the authenticated user is part of the consultation.
    Rejects if user is neither the patient nor the assigned doctor.
    """
    sid = _get_sid()

    try:
        session = _socket_sessions.get(sid, {})
        user_id = session.get("user_id")

        if not user_id:
            logger.warning(f"[Socket] join_consultation rejected: not authenticated, sid={sid}")
            _emit_error("Not authenticated")
            return

        consultation_id = (data or {}).get("consultation_id")
        if not consultation_id:
            _emit_error("consultation_id is required")
            return

        try:
            consultation_id = int(consultation_id)
        except (ValueError, TypeError):
            _emit_error("Invalid consultation_id")
            return

        # Validate user is part of this consultation
        from ..services.consultation_service import get_consultation_by_id

        consultation = get_consultation_by_id(consultation_id)
        if not consultation:
            logger.warning(f"[Socket] join_consultation rejected: consultation {consultation_id} not found")
            _emit_error("Consultation not found")
            return

        if consultation.patient_id != user_id and consultation.doctor_id != user_id:
            logger.warning(
                f"[Socket] join_consultation rejected: user {user_id} not part of "
                f"consultation {consultation_id} (patient={consultation.patient_id}, doctor={consultation.doctor_id})"
            )
            _emit_error("Not authorized to join this consultation")
            return

        room = _room_consultation(consultation_id)
        join_room(room)
        session.setdefault("rooms", set()).add(room)
        logger.info(f"[Socket] User {user_id} joined room {room}")

    except Exception as e:
        logger.error(f"[Socket] Error in join_consultation for sid={sid}: {e}")
        _emit_error("Failed to join consultation room")


@socketio.on("leave_consultation")
def handle_leave_consultation(data):
    """Leave a consultation room. Expected data: { consultation_id: <int> }"""
    sid = _get_sid()

    try:
        consultation_id = (data or {}).get("consultation_id")
        if not consultation_id:
            return

        try:
            consultation_id = int(consultation_id)
        except (ValueError, TypeError):
            return

        room = _room_consultation(consultation_id)
        leave_room(room)
        _socket_sessions.get(sid, {}).setdefault("rooms", set()).discard(room)
        logger.info(f"[Socket] Client {sid} left room {room}")

    except Exception as e:
        logger.error(f"[Socket] Error in leave_consultation for sid={sid}: {e}")


@socketio.on("join_doctor_room")
def handle_join_doctor_room(data):
    """
    Join a doctor room.
    Expected data: { doctor_id: <int> }

    AUTHORIZATION: Only doctors can join their own room.
    Validates role == "doctor" AND user_id == doctor_id.
    """
    sid = _get_sid()

    try:
        session = _socket_sessions.get(sid, {})
        user_id = session.get("user_id")
        role = session.get("role")

        if not user_id:
            logger.warning(f"[Socket] join_doctor_room rejected: not authenticated, sid={sid}")
            _emit_error("Not authenticated")
            return

        doctor_id = (data or {}).get("doctor_id")
        if not doctor_id:
            _emit_error("doctor_id is required")
            return

        try:
            doctor_id = int(doctor_id)
        except (ValueError, TypeError):
            _emit_error("Invalid doctor_id")
            return

        # Only doctors can join their own room
        if role != "doctor":
            logger.warning(f"[Socket] join_doctor_room rejected: user {user_id} is not a doctor")
            _emit_error("Only doctors can join doctor rooms")
            return

        if user_id != doctor_id:
            logger.warning(f"[Socket] join_doctor_room rejected: user {user_id} != doctor {doctor_id}")
            _emit_error("Not authorized to join this doctor room")
            return

        room = _room_doctor(doctor_id)
        join_room(room)
        session.setdefault("rooms", set()).add(room)
        logger.info(f"[Socket] Doctor {doctor_id} joined room {room}")

    except Exception as e:
        logger.error(f"[Socket] Error in join_doctor_room for sid={sid}: {e}")
        _emit_error("Failed to join doctor room")
