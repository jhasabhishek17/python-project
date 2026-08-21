"""
Video Panorama Flask Web Application & REST API
-----------------------------------------------
Provides an interactive web dashboard and REST API endpoints for uploading
panning videos, configuring stitching parameters, and viewing/downloading high-res panoramas.
"""

import os
import uuid
import logging
import cv2
from flask import Flask, request, render_template_string, send_from_directory, jsonify
from cv_engine import process_video_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Target folders for video uploads and generated panorama image outputs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB maximum video file upload limit


# -----------------------------------------------------------------------------
# DASHBOARD HTML / CSS / JS TEMPLATE
# -----------------------------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Panorama Generator Studio</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #090d16;
            --card-bg: #131b2e;
            --card-border: #1e293b;
            --accent-blue: #38bdf8;
            --accent-indigo: #6366f1;
            --accent-green: #10b981;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            background: rgba(19, 27, 46, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--card-border);
            padding: 18px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 800;
            font-size: 22px;
            background: linear-gradient(135deg, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .container {
            max-width: 1100px;
            margin: 40px auto;
            padding: 0 20px;
            flex: 1;
            width: 100%;
        }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 35px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
            margin-bottom: 30px;
        }

        .hero-title {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .hero-subtitle {
            color: var(--text-muted);
            font-size: 15px;
            margin-bottom: 25px;
        }

        /* Config grid */
        .config-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
            background: #0d1322;
            padding: 20px;
            border-radius: 14px;
            border: 1px solid #1e293b;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .form-group label {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .form-control {
            background: #182238;
            border: 1px solid #334155;
            color: var(--text-main);
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 14px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s ease;
        }

        .form-control:focus {
            border-color: var(--accent-blue);
        }

        /* Drop Zone */
        .drop-zone {
            border: 2px dashed #334155;
            border-radius: 16px;
            padding: 45px;
            text-align: center;
            cursor: pointer;
            background: #0d1322;
            transition: all 0.25s ease;
            position: relative;
        }

        .drop-zone:hover {
            border-color: var(--accent-blue);
            background: #111a2e;
        }

        .drop-icon {
            font-size: 42px;
            margin-bottom: 12px;
            display: block;
        }

        .file-info {
            margin-top: 15px;
            font-weight: 600;
            color: var(--accent-blue);
            font-size: 14px;
        }

        .btn-submit {
            background: linear-gradient(135deg, #2563eb, #4f46e5);
            color: white;
            border: none;
            padding: 14px 36px;
            font-size: 16px;
            font-weight: 700;
            border-radius: 10px;
            cursor: pointer;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            width: 100%;
            margin-top: 25px;
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
        }

        .btn-submit:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4);
        }

        /* Progress Bar */
        .progress-box {
            display: none;
            margin-top: 20px;
        }

        .progress-bar-bg {
            background: #1e293b;
            height: 10px;
            border-radius: 10px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #38bdf8, #818cf8);
            transition: width 0.3s ease;
        }

        .status-msg {
            text-align: center;
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 8px;
        }

        /* Results Display */
        .results-container {
            margin-top: 35px;
            padding-top: 30px;
            border-top: 1px solid var(--card-border);
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }

        .metric-card {
            background: #0d1322;
            padding: 16px;
            border-radius: 12px;
            border: 1px solid #1e293b;
            text-align: center;
        }

        .metric-value {
            font-size: 20px;
            font-weight: 800;
            color: var(--accent-blue);
            margin-top: 4px;
        }

        .metric-label {
            font-size: 12px;
            color: var(--text-muted);
            text-transform: uppercase;
        }

        .pano-viewer {
            width: 100%;
            max-height: 500px;
            object-fit: contain;
            border-radius: 12px;
            border: 1px solid var(--card-border);
            margin-top: 15px;
            background: #000;
        }

        .download-btn {
            display: inline-block;
            background: var(--accent-green);
            color: white;
            padding: 14px 28px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 700;
            margin-top: 20px;
            transition: background 0.2s ease;
        }

        .download-btn:hover {
            background: #059669;
        }

        .error-card {
            background: #450a0a;
            border: 1px solid #991b1b;
            color: #fca5a5;
            padding: 16px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 14px;
        }

        footer {
            text-align: center;
            padding: 25px;
            color: var(--text-muted);
            font-size: 13px;
            border-top: 1px solid var(--card-border);
        }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            📷 Video Panorama Studio
        </div>
        <div style="font-size: 13px; color: var(--text-muted);">OpenCV & Computer Vision Engine</div>
    </header>

    <div class="container">
        <div class="card">
            <div class="hero-title">Synthesize Panoramic Imagery</div>
            <div class="hero-subtitle">Upload a panning video clip to extract keyframes, align perspectives, and assemble a high-resolution panorama.</div>

            {% if error %}
            <div class="error-card">
                ⚠️ <strong>Error processing video:</strong> {{ error }}
            </div>
            {% endif %}

            <form action="/process" method="post" enctype="multipart/form-data" onsubmit="onFormSubmit()">
                <!-- Parameter Configurations -->
                <div class="config-grid">
                    <div class="form-group">
                        <label for="mode">Stitching Algorithm</label>
                        <select name="mode" id="mode" class="form-control">
                            <option value="auto" selected>Auto (OpenCV + Homography Fallback)</option>
                            <option value="opencv">OpenCV Stitcher (Scans/Panoramas)</option>
                            <option value="homography">Feature Matching (ORB + RANSAC)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="max_keyframes">Max Keyframes</label>
                        <select name="max_keyframes" id="max_keyframes" class="form-control">
                            <option value="5">5 Keyframes (Fast)</option>
                            <option value="8" selected>8 Keyframes (Balanced)</option>
                            <option value="12">12 Keyframes (High Detail)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="blur_thresh">Blur Rejection Filter</label>
                        <select name="blur_thresh" id="blur_thresh" class="form-control">
                            <option value="40" selected>Moderate (Recommended)</option>
                            <option value="60">Strict (Drop Moderate Blur)</option>
                            <option value="0">Off (Use All Frames)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="resolution">Max Processing Resolution</label>
                        <select name="resolution" id="resolution" class="form-control">
                            <option value="720">720p (Ultra Fast)</option>
                            <option value="1080" selected>1080p (Full HD Quality)</option>
                            <option value="1440">1440p (2K Ultra Quality)</option>
                        </select>
                    </div>
                </div>

                <!-- Video Drop Zone -->
                <div class="drop-zone" onclick="document.getElementById('videoFile').click()">
                    <span class="drop-icon">🎬</span>
                    <div style="font-size: 16px; font-weight: 700;">Drag and drop video file here, or click to browse</div>
                    <div style="font-size: 13px; color: var(--text-muted); margin-top: 6px;">Supports MP4, MOV, AVI (Max 200 MB)</div>
                    <input type="file" id="videoFile" name="video" accept="video/*" style="display:none;" required onchange="handleFileSelect()">
                    <div class="file-info" id="fileInfo"></div>
                </div>

                <button type="submit" class="btn-submit" id="submitBtn">Synthesize Panorama</button>

                <!-- Processing Progress -->
                <div class="progress-box" id="progressBox">
                    <div class="progress-bar-bg">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <div class="status-msg" id="statusMsg">Analyzing video frames and selecting keyframes...</div>
                </div>
            </form>

            <!-- Stitched Result & Performance Metrics -->
            {% if result %}
            <div class="results-container">
                <h3 style="font-size: 20px; font-weight: 700; margin-bottom: 15px;">Panorama Output Result</h3>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Total Video Frames</div>
                        <div class="metric-value">{{ metrics.total_video_frames }}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Keyframes Used</div>
                        <div class="metric-value">{{ metrics.selected_keyframes }}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Processing Time</div>
                        <div class="metric-value">{{ metrics.processing_time_sec }}s</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Output Resolution</div>
                        <div class="metric-value" style="font-size: 15px; margin-top: 8px;">{{ metrics.resolution }}</div>
                    </div>
                </div>

                <img src="/outputs/{{ result }}" class="pano-viewer" alt="Generated Panorama Result">
                
                <div style="text-align: center;">
                    <a href="/outputs/{{ result }}" download="panorama_result.jpg" class="download-btn">
                        ⬇ Download High-Res Panorama
                    </a>
                </div>
            </div>
            {% endif %}
        </div>
    </div>

    <footer>
        Video Panorama Generator • Computer Vision Pipeline Engine
    </footer>

    <script>
        function handleFileSelect() {
            const fileInput = document.getElementById('videoFile');
            const fileInfo = document.getElementById('fileInfo');
            if (fileInput.files.length > 0) {
                const file = fileInput.files[0];
                const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                fileInfo.innerText = `Selected: ${file.name} (${sizeMB} MB)`;
            }
        }

        function onFormSubmit() {
            const submitBtn = document.getElementById('submitBtn');
            const progressBox = document.getElementById('progressBox');
            const progressFill = document.getElementById('progressFill');
            const statusMsg = document.getElementById('statusMsg');

            submitBtn.disabled = true;
            submitBtn.style.opacity = '0.6';
            submitBtn.innerText = 'Processing Video...';
            progressBox.style.display = 'block';

            let width = 10;
            const messages = [
                "Sampling video frame sequences...",
                "Running Laplacian blur detection...",
                "Filtering keyframes & matching feature points...",
                "Warping perspective & blending seams...",
                "Cropping final ROI boundaries..."
            ];

            let step = 0;
            const interval = setInterval(() => {
                width += 15;
                if (width > 90) {
                    clearInterval(interval);
                } else {
                    progressFill.style.width = width + '%';
                    if (step < messages.length) {
                        statusMsg.innerText = messages[step];
                        step++;
                    }
                }
            }, 600);
        }
    </script>
</body>
</html>
"""


# -----------------------------------------------------------------------------
# FLASK WEB ROUTES
# -----------------------------------------------------------------------------

@app.route("/")
def home():
    """Renders the main web dashboard."""
    return render_template_string(HTML_TEMPLATE)


@app.route("/process", methods=["POST"])
def process_video_web():
    """Form handler for web video upload and panorama processing."""
    if "video" not in request.files:
        return render_template_string(HTML_TEMPLATE, error="No video file uploaded.")

    file = request.files["video"]
    if file.filename == "":
        return render_template_string(HTML_TEMPLATE, error="Selected video file is empty.")

    # Parse configurable parameters from form
    mode = request.form.get("mode", "auto")
    max_keyframes = int(request.form.get("max_keyframes", 8))
    blur_thresh = float(request.form.get("blur_thresh", 40.0))
    resolution = int(request.form.get("resolution", 1080))

    # Save uploaded video with unique identifier to prevent collisions
    ext = os.path.splitext(file.filename)[1] or ".mp4"
    temp_video_filename = f"{uuid.uuid4().hex}{ext}"
    video_path = os.path.join(UPLOAD_FOLDER, temp_video_filename)
    file.save(video_path)

    try:
        panorama_img, metrics = process_video_pipeline(
            video_path,
            sample_interval=8,
            max_keyframes=max_keyframes,
            min_blur_score=blur_thresh,
            mode=mode,
            max_resolution=resolution
        )

        # Save output panorama image
        output_filename = f"panorama_{uuid.uuid4().hex[:10]}.jpg"
        save_path = os.path.join(OUTPUT_FOLDER, output_filename)
        cv2.imwrite(save_path, panorama_img)

        # Clean up temporary uploaded video file
        if os.path.exists(video_path):
            os.remove(video_path)

        return render_template_string(HTML_TEMPLATE, result=output_filename, metrics=metrics)

    except Exception as exc:
        logging.error("Failed to process uploaded video: %s", exc, exc_info=True)
        if os.path.exists(video_path):
            os.remove(video_path)
        return render_template_string(HTML_TEMPLATE, error=str(exc))


@app.route("/outputs/<filename>")
def serve_output_file(filename):
    """Serves output panorama images."""
    return send_from_directory(OUTPUT_FOLDER, filename)


# -----------------------------------------------------------------------------
# REST API ENDPOINTS
# -----------------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def api_health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "video-panorama-generator"}), 200


@app.route("/api/process", methods=["POST"])
def api_process_video():
    """REST API endpoint to process videos asynchronously or synchronously via POST."""
    if "video" not in request.files:
        return jsonify({"error": "Missing 'video' file parameter in request."}), 400

    file = request.files["video"]
    mode = request.form.get("mode", "auto")
    max_keyframes = int(request.form.get("max_keyframes", 8))
    blur_thresh = float(request.form.get("blur_thresh", 40.0))
    resolution = int(request.form.get("resolution", 1080))

    ext = os.path.splitext(file.filename)[1] or ".mp4"
    video_path = os.path.join(UPLOAD_FOLDER, f"api_{uuid.uuid4().hex}{ext}")
    file.save(video_path)

    try:
        panorama_img, metrics = process_video_pipeline(
            video_path,
            sample_interval=8,
            max_keyframes=max_keyframes,
            min_blur_score=blur_thresh,
            mode=mode,
            max_resolution=resolution
        )

        output_filename = f"pano_api_{uuid.uuid4().hex[:10]}.jpg"
        save_path = os.path.join(OUTPUT_FOLDER, output_filename)
        cv2.imwrite(save_path, panorama_img)

        if os.path.exists(video_path):
            os.remove(video_path)

        return jsonify({
            "success": True,
            "result_url": f"/outputs/{output_filename}",
            "metrics": metrics
        }), 200

    except Exception as exc:
        if os.path.exists(video_path):
            os.remove(video_path)
        return jsonify({"success": False, "error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Server starting on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
