"""
Entry point to run the Flask backend server.

Run from project root: python backend/run.py
The server will listen on http://localhost:5000
"""
import sys
from pathlib import Path

# --- Add project root to Python path so we can "import backend" ---
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from backend.app import create_app

# Create the Flask app using the app factory
app = create_app()

if __name__ == "__main__":
    # Start the development server (for local use only)
    app.run(host="0.0.0.0", port=5000, debug=True)

