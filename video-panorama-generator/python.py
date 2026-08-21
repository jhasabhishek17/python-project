"""
Video Panorama Launcher Entrypoint
-----------------------------------
Provides a root-level executable script for launching the Flask web server.
"""

import os
import sys

# Ensure the module search path includes the video-panorama-generator directory
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"==================================================")
    print(f" Video Panorama Generator Web Server")
    print(f" Running on http://localhost:{port}")
    print(f"==================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
