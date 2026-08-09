import os
import sys

# Ensure module path includes video-panorama-generator folder
dir_path = os.path.dirname(os.path.abspath(__file__))
sub_path = os.path.join(dir_path, "video-panorama-generator")
if sub_path not in sys.path:
    sys.path.insert(0, sub_path)

from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting Video Panorama Web Server on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)