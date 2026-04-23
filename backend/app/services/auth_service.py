"""
Authentication business logic (no HTTP here).

- Hash/verify passwords
- Find user by email or id
- Register new user (and PatientProfile if role=patient)
- Check email+password (authenticate)
"""
from werkzeug.security import generate_password_hash, check_password_hash

from ..extensions import db
from ..models import User, PatientProfile

# Allowed values for User.role
VALID_ROLES = ("patient", "doctor", "admin")


def hash_password(password: str) -> str:
    """Turn plain password into a secure hash before storing in DB."""
    return generate_password_hash(password, method="scrypt")


def verify_password(password_hash: str, password: str) -> bool:
    """Return True if the given password matches the hash."""
    return check_password_hash(password_hash, password)


def get_user_by_email(email: str) -> User | None:
    """Return the User with the given email, or None."""
    return User.query.filter_by(email=email.strip().lower()).first()


def get_user_by_id(user_id: int) -> User | None:
    """Return the User with the given id, or None."""
    return User.query.get(user_id)


def register_user(
    name: str,
    email: str,
    password: str,
    role: str = "patient",
    specialization: str | None = None,
) -> User:
    """
    Create User (and PatientProfile if role is patient). Commit to DB.
    Raises ValueError if email already exists or role is not in VALID_ROLES.
    """
    email = email.strip().lower()
    if get_user_by_email(email):
        raise ValueError("Email already registered")
    if role not in VALID_ROLES:
        raise ValueError("Invalid role")

    user = User(
        name=name.strip(),
        email=email,
        password_hash=hash_password(password),
        role=role,
        specialization=(specialization or "").strip() or None,
    )
    db.session.add(user)
    db.session.flush()
    if role == "patient":
        profile = PatientProfile(user_id=user.id)
        db.session.add(profile)
    db.session.commit()
    db.session.refresh(user)
    return user


def authenticate_user(email: str, password: str) -> User | None:
    """Check email + password. Return the User if valid, else None."""
    user = get_user_by_email(email)
    if user is None:
        return None
    if not verify_password(user.password_hash, password):
        return None
    return user
