"""
Role-based access: use @role_required("patient") or @role_required("doctor") on routes.
Must be used together with @jwt_required(). Returns 403 if user's role is not in the list.
"""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_current_user, verify_jwt_in_request


def role_required(*allowed_roles: str):
    """Use after @jwt_required(). Ensures current user's role is in allowed_roles; else 403."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = get_current_user()
            if user is None:
                return jsonify({"message": "User not found"}), 404
            if user.role not in allowed_roles:
                return jsonify({"message": "Insufficient permissions"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
