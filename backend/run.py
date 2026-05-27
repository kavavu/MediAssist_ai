"""
Entry point to run the Flask backend server with SocketIO support.

Run from project root: python backend/run.py
The server will listen on http://localhost:5000
WebSocket endpoint: ws://localhost:5000/socket.io/
"""
import sys
from pathlib import Path

# --- Load environment variables from .env file automatically ---
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Also check parent directory
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

# --- Add project root to Python path so we can "import backend" ---
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from backend.app import create_app
from backend.app.sockets import socketio

# Create the Flask app using the app factory
app = create_app()

if __name__ == "__main__":
    # Start the development server with WebSocket support
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
