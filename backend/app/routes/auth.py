"""
Authentication API: register and login.

- POST /api/auth/register → create new user (name, email, password, role)
- POST /api/auth/login    → returns JWT access_token + user (email, role, etc.)
"""
from flask import Blueprint, request, jsonify

from flask_jwt_extended import create_access_token

from ..services.auth_service import register_user, authenticate_user

auth_bp = Blueprint("auth", __name__)


def _user_payload(user):
    """Strip password; return only id, name, email, role for JSON responses."""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }


@auth_bp.post("/register")
def register():
    """Register: expects JSON { name, email, password, role? }. Returns 201 + user or 400 on error."""
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "patient")

    if not name or not email or not password:
        return jsonify({"message": "Missing name, email, or password"}), 400

    try:
        user = register_user(name=name, email=email, password=password, role=role)
        return jsonify({"message": "Registration successful", "user": _user_payload(user)}), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400


@auth_bp.post("/login")
def login():
    """Login: expects JSON { email, password }. Returns 200 + access_token + user, or 401 if invalid."""
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Missing email or password"}), 400

    user = authenticate_user(email=email, password=password)
    if user is None:
        return jsonify({"message": "Invalid email or password"}), 401

    # identity must be a string for JWT "sub" claim; store user.id as str
    token = create_access_token(identity=str(user.id))
    return jsonify({
        "access_token": token,
        "user": _user_payload(user),
    }), 200
