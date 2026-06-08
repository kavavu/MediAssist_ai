"""
Authentication API: register and login.

- POST /api/auth/register → create new user (name, email, password)
  SECURITY: Role is ALWAYS "patient" from registration. Admin/doctor accounts
  must be created by an existing admin through the admin dashboard.
- POST /api/auth/login    → returns JWT access_token + user (email, role, etc.)
"""
from flask import Blueprint, request, jsonify
import re

from flask_jwt_extended import create_access_token
from sqlalchemy.exc import SQLAlchemyError

from ..services.auth_service import register_user, authenticate_user

auth_bp = Blueprint("auth", __name__)

# Email validation regex (simple but effective)
_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def _user_payload(user):
    """Strip password; return only id, name, email, role, specialization for JSON responses."""
    payload = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "specialization": user.specialization,
    }
    if user.role == "doctor":
        payload["is_available"] = user.is_available
        payload["current_load"] = user.current_load
        payload["is_verified"] = user.is_verified
    return payload


def _validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    Returns (is_valid, error_message).
    Requirements: min 8 chars, at least 1 letter, at least 1 digit.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isalpha() for c in password):
        return False, "Password must contain at least one letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, ""


@auth_bp.post("/register")
def register():
    """
    Register: expects JSON { name, email, password }.
    SECURITY FIX: Role is ALWAYS forced to "patient".
    Admin and doctor accounts can only be created by an existing admin.
    Returns 201 + user or 400 on error.
    """
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    # Validate required fields
    if not name or not email or not password:
        return jsonify({"error": "Missing name, email, or password"}), 400
    
    # Validate name length
    if len(name.strip()) < 2:
        return jsonify({"error": "Name must be at least 2 characters"}), 400
    
    # Validate email format
    if not _EMAIL_REGEX.match(email.strip()):
        return jsonify({"error": "Invalid email format"}), 400
    
    # Validate password strength
    pwd_valid, pwd_error = _validate_password(password)
    if not pwd_valid:
        return jsonify({"error": pwd_error}), 400

    # SECURITY: Always force role to "patient" — prevents role escalation attacks
    # where a malicious user registers as "admin" or "doctor"
    try:
        user = register_user(
            name=name,
            email=email,
            password=password,
            role="patient",  # ALWAYS patient from public registration
            specialization=None,
        )
        return jsonify({"message": "Registration successful", "user": _user_payload(user)}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except SQLAlchemyError:
        return jsonify({"error": "Database error. Please try again."}), 500


@auth_bp.post("/login")
def login():
    """Login: expects JSON { email, password }. Returns 200 + access_token + user, or 401 if invalid."""
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    user = authenticate_user(email=email, password=password)
    if user is None:
        return jsonify({"error": "Invalid email or password"}), 401

    # identity must be a string for JWT "sub" claim; store user.id as str
    token = create_access_token(identity=str(user.id))
    return jsonify({
        "access_token": token,
        "user": _user_payload(user),
    }), 200
