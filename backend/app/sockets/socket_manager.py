"""
Centralized Socket.IO manager for MediAssist AI.

This module:
- Creates and exposes the SocketIO instance
- Provides init_socketio(app) for Flask app factory integration
- Handles CORS for WebSocket connections

SECURITY NOTE:
- CORS origins should be restricted in production via SOCKET_CORS_ORIGINS env var
- Default "*" is only safe for local development
"""
import os
from flask_socketio import SocketIO

# Read CORS origins from environment (matches HTTP CORS config)
_socket_cors = os.getenv("SOCKET_CORS_ORIGINS", "*")
if isinstance(_socket_cors, str) and _socket_cors != "*":
    _socket_cors = [o.strip() for o in _socket_cors.split(",")]

# Create the SocketIO instance (not bound to an app yet)
socketio = SocketIO(
    cors_allowed_origins=_socket_cors,
    async_mode="threading",
    logger=False,
    engineio_logger=False,
)


def init_socketio(app):
    """Bind SocketIO to the Flask app. Called from create_app()."""
    socketio.init_app(app)
