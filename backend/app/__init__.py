"""
MediAssist AI Flask app factory.

create_app() builds the app: config, DB, JWT, ML model, routes, seed data.
All API routes are under /api/ (e.g. /api/auth/login, /api/predict).
"""
from flask import Flask

from backend.config import get_config
from .extensions import db, migrate, jwt


def create_app():
    """Create and configure the Flask app. Called once when the server starts (see backend/run.py)."""
    app = Flask(__name__)
    app.config.from_object(get_config())

    _init_extensions(app)   # DB, migrations, JWT + load models
    _load_ml_model()        # Load symptom classifier for /api/predict
    _register_blueprints(app)  # Auth, symptoms, patient, doctor routes
    _ensure_db_tables(app)   # Create tables if missing
    _seed_if_empty(app)      # Insert sample lab tests & medicines if empty

    @app.get("/health")
    def health_check():
        """GET /health returns {"status": "ok"} for liveness checks."""
        return {"status": "ok"}, 200

    return app


def _init_extensions(app: Flask) -> None:
    """Attach database, migrations, JWT. Load models. Set JWT to resolve token 'sub' to User."""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    from . import models  # noqa: F401  # So SQLAlchemy knows all tables

    # When a request has a valid JWT, turn token "sub" (user id) into a User object
    from .services.auth_service import get_user_by_id

    @jwt.user_lookup_loader
    def _user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data.get("sub")
        if identity is None:
            return None
        return get_user_by_id(int(identity))


def _load_ml_model() -> None:
    """Load the symptom classification model on startup (trains if not persisted)."""
    from .ml.symptom_model import load_model
    load_model()


def _register_blueprints(app: Flask) -> None:
    """Register all API blueprints and their URL prefixes."""
    from .routes.auth import auth_bp
    from .routes.symptoms import symptoms_bp
    from .routes.patient import patient_bp
    from .routes.doctor import doctor_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(symptoms_bp, url_prefix="/api")
    app.register_blueprint(patient_bp, url_prefix="/api/patient")
    app.register_blueprint(doctor_bp, url_prefix="/api/doctor")


def _ensure_db_tables(app: Flask) -> None:
    """Create all tables (users, symptom_reports, etc.) if they don't exist yet."""
    with app.app_context():
        db.create_all()


def _seed_if_empty(app: Flask) -> None:
    """If lab_tests and medicines are empty, insert sample rows for development."""
    from .utils.seed import seed_catalog
    with app.app_context():
        seed_catalog()

