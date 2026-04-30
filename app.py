import sys
import os
from pathlib import Path

# Add the current directory to sys.path so we can import backend
sys.path.append(str(Path(__file__).parent))

from backend.app import app, init_db, FRONTEND_DIR

if __name__ == "__main__":
    init_db()
    print("[startup] Serving frontend from:", FRONTEND_DIR)
    print("[startup] Starting app on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
