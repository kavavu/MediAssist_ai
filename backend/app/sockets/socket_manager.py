"""
Centralized Socket.IO manager for MediAssist AI.

This module:
- Creates and exposes the SocketIO instance
- Provides init_socketio(app) for Flask app factory integration
- Handles CORS for WebSocket connections
"""
from flask_socketio import SocketIO

# Create the SocketIO instance (not bound to an app yet)
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",
    logger=False,
    engineio_logger=False,
)


def init_socketio(app):
    """Bind SocketIO to the Flask app. Called from create_app()."""
    socketio.init_app(app)
