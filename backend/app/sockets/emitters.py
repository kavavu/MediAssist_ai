"""
Reusable socket emitters for MediAssist AI.

All socket emissions go through this module to ensure:
- Consistent room targeting
- Single source of truth for event names
- No duplication

These functions are called from the SERVICE LAYER only.
"""
import logging

from .socket_manager import socketio

logger = logging.getLogger(__name__)


def _room_consultation(consultation_id: int) -> str:
    return f"consultation_{consultation_id}"


def _room_doctor(doctor_id: int) -> str:
    return f"doctor_{doctor_id}"


# ---------------------------------------------------------------------------
# Chat / Follow-up Messages
# ---------------------------------------------------------------------------

def emit_new_message(consultation_id: int, message_data: dict) -> None:
    """
    Emit a new follow-up message to everyone in the consultation room.
    Called from consultation_service.add_followup().

    Duplicate protection: The message_data already contains a unique DB id.
    Frontend checks message.id before adding to state.
    """
    try:
        room = _room_consultation(consultation_id)
        socketio.emit(
            "new_message",
            {"consultation_id": consultation_id, "message": message_data},
            room=room,
        )
        logger.debug(f"[Socket] Emitted new_message to room {room}, msg_id={message_data.get('id')}")
    except Exception as e:
        logger.error(f"[Socket] Failed to emit new_message for consultation {consultation_id}: {e}")


# ---------------------------------------------------------------------------
# Consultation Lifecycle
# ---------------------------------------------------------------------------

def emit_new_consultation(doctor_id: int, consultation_data: dict) -> None:
    """
    Emit a new consultation assignment to the doctor's room.
    Called from consultation_service.create_consultation().

    This is emitted ONCE per consultation creation, immediately after DB commit.
    """
    try:
        room = _room_doctor(doctor_id)
        socketio.emit(
            "new_consultation",
            {"consultation": consultation_data},
            room=room,
        )
        logger.debug(f"[Socket] Emitted new_consultation to room {room}, consultation_id={consultation_data.get('id')}")
    except Exception as e:
        logger.error(f"[Socket] Failed to emit new_consultation for doctor {doctor_id}: {e}")


def emit_consultation_update(consultation_id: int, update_data: dict) -> None:
    """
    Emit a consultation status/response update to the consultation room.
    Called from:
      - consultation_service.respond_to_consultation()
      - consultation_service.edit_response()
      - consultation_service.resolve_consultation()

    This is emitted ONCE per update, immediately after DB commit.
    Frontend updates the consultation in-place by id.
    """
    try:
        room = _room_consultation(consultation_id)
        socketio.emit(
            "consultation_updated",
            {"consultation_id": consultation_id, "data": update_data},
            room=room,
        )
        logger.debug(f"[Socket] Emitted consultation_updated to room {room}, status={update_data.get('status')}")
    except Exception as e:
        logger.error(f"[Socket] Failed to emit consultation_update for consultation {consultation_id}: {e}")
