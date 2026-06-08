"""
MediAssist AI Flask app factory.

create_app() builds the app: config, DB, JWT, ML model, routes, seed data.
All API routes are under /api/ (e.g. /api/auth/login, /api/predict).

SECURITY NOTES:
- CORS origins are configurable via CORS_ORIGINS env var (default * for dev only)
- Global error handlers catch unhandled exceptions and return JSON (no HTML stack traces)
- JWT tokens expire after 1 hour for security
"""
from flask import Flask, jsonify
from flask_cors import CORS

from backend.config import get_config
from .extensions import db, migrate, jwt


def create_app():
    """Create and configure the Flask app. Called once when the server starts (see backend/run.py)."""
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)
    
    # CORS: Use configured origins. In production, restrict to your frontend domain.
    # Default "*" is only safe for development.
    cors_origins = getattr(config, "CORS_ORIGINS", "*")
    if isinstance(cors_origins, str) and cors_origins != "*":
        cors_origins = [o.strip() for o in cors_origins.split(",")]
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    _init_extensions(app)   # DB, migrations, JWT + load models
    _init_socketio(app)     # WebSocket support
    _load_ml_model()        # Load symptom classifier for /api/predict
    _register_blueprints(app)  # Auth, symptoms, patient, doctor routes
    _ensure_db_tables(app)   # Create tables if missing
    _seed_if_empty(app)      # Insert sample lab tests & medicines if empty
    _register_error_handlers(app)  # Global error handlers for consistent JSON responses

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
    from .routes.consultation import consultation_bp
    from .routes.admin import admin_bp
    from .routes.appointment import appointment_bp
    from .routes.payment import payment_bp
    from .routes.review import review_bp
    from .routes.upload import upload_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(symptoms_bp, url_prefix="/api")
    app.register_blueprint(patient_bp, url_prefix="/api/patient")
    app.register_blueprint(doctor_bp, url_prefix="/api/doctor")
    app.register_blueprint(consultation_bp, url_prefix="/api/consultation")
    app.register_blueprint(appointment_bp, url_prefix="/api/appointments")
    app.register_blueprint(payment_bp, url_prefix="/api/payments")
    app.register_blueprint(review_bp, url_prefix="/api/reviews")
    app.register_blueprint(upload_bp, url_prefix="/api")
    app.register_blueprint(admin_bp)


def _ensure_db_tables(app: Flask) -> None:
    """Create all tables (users, symptom_reports, etc.) if they don't exist yet."""
    with app.app_context():
        db.create_all()


def _init_socketio(app: Flask) -> None:
    """Initialize SocketIO for real-time WebSocket support."""
    from .sockets import init_socketio
    init_socketio(app)


def _seed_if_empty(app: Flask) -> None:
    """If lab_tests and medicines are empty, insert sample rows for development."""
    from .utils.seed import seed_catalog
    with app.app_context():
        seed_catalog()


def _register_error_handlers(app: Flask) -> None:
    """
    Register global error handlers so the API always returns JSON.
    Prevents Flask's default HTML error pages from leaking stack traces.
    """
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request", "message": str(error.description) if hasattr(error, "description") else "Invalid request"}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found", "message": "The requested resource was not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"error": "Method not allowed", "message": "This HTTP method is not allowed for this endpoint"}), 405

    @app.errorhandler(500)
    def internal_error(error):
        # Log the real error but don't expose it to the client
        import logging
        logging.getLogger(__name__).exception("Unhandled 500 error")
        return jsonify({"error": "Internal server error", "message": "Something went wrong. Please try again later."}), 500

    @app.errorhandler(Exception)
    def unhandled_exception(error):
        # Catch-all for any unhandled exception
        import logging
        logging.getLogger(__name__).exception("Unhandled exception")
        return jsonify({"error": "Internal server error", "message": "Something went wrong. Please try again later."}), 500

