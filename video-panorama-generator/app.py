import os
import sys
import warnings
warnings.filterwarnings("ignore")

import cv2
import numpy as np
import logging
import uuid
from flask import Flask, request, render_template_string, send_from_directory

logging.basicConfig(level=logging.INFO)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB upload limit


# ------------------------------------------------
# COMPUTER VISION PIPELINE
# ------------------------------------------------

def extract_frames(video_path, skip=10):
    cap = cv2.VideoCapture(video_path)
    frames = []
    frame_id = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_id % skip == 0 and frame is not None:
            frames.append(frame)
        frame_id += 1

    cap.release()
    return frames


def detect_scene_changes(frames):
    scores = []
    prev = None

    for i, frame in enumerate(frames):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev is not None:
            diff = cv2.absdiff(gray, prev)
            score = float(np.mean(diff))
            scores.append((score, i))
        prev = gray

    return scores


def select_keyframes(frames, k=5):
    if len(frames) <= k:
        return frames

    scores = detect_scene_changes(frames)
    if not scores:
        return frames[:k]

    scores.sort(reverse=True, key=lambda x: x[0])
    indices = [x[1] for x in scores[:k]]
    indices.sort()

    return [frames[i] for i in indices]


def feather_panorama(frames):
    if not frames:
        return None
    if len(frames) == 1:
        return frames[0]

    base = frames[0]

    for img in frames[1:]:
        h = min(base.shape[0], img.shape[0])
        w_base = max(1, int(base.shape[1] * h / base.shape[0]))
        w_img = max(1, int(img.shape[1] * h / img.shape[0]))

        base = cv2.resize(base, (w_base, h))
        img = cv2.resize(img, (w_img, h))

        overlap = min(60, base.shape[1] // 2, img.shape[1] // 2)
        if overlap < 5:
            base = np.hstack([base, img])
            continue

        left = base[:, :-overlap]
        right = img[:, overlap:]

        blend1 = base[:, -overlap:].astype(np.float32)
        blend2 = img[:, :overlap].astype(np.float32)

        alpha = np.linspace(0, 1, overlap).reshape(1, overlap, 1)
        blended = (1 - alpha) * blend1 + alpha * blend2

        base = np.hstack([left, blended.astype(np.uint8), right])

    return base.astype(np.uint8)


def build_panorama(frames):
    if not frames:
        return None

    try:
        stitcher = cv2.Stitcher_create()
        status, pano = stitcher.stitch(frames)
        if status == 0 and pano is not None:
            return pano
    except Exception as e:
        logging.warning(f"OpenCV stitcher exception: {e}. Falling back to feather blending.")

    return feather_panorama(frames)


def process_video(video_path):
    frames = extract_frames(video_path)
    if not frames:
        raise ValueError("Could not extract valid video frames. Please check your video file format.")

    keyframes = select_keyframes(frames)
    pano = build_panorama(keyframes)

    if pano is None:
        raise ValueError("Failed to generate panorama from video.")

    filename = f"{uuid.uuid4().hex}.jpg"
    save_path = os.path.join(OUTPUT_FOLDER, filename)
    cv2.imwrite(save_path, pano)

    return filename


# ------------------------------------------------
# WEB INTERFACE TEMPLATE
# ------------------------------------------------

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Panorama Generator</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: #0f172a;
            color: #f8fafc;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 40px;
            background: #1e293b;
            border-bottom: 1px solid #334155;
        }
        .logo {
            font-weight: 700;
            font-size: 20px;
            color: #38bdf8;
        }
        .subtitle {
            color: #94a3b8;
            font-size: 14px;
        }
        .container {
            max-width: 850px;
            margin: 40px auto;
            padding: 0 20px;
            flex: 1;
        }
        .card {
            background: #1e293b;
            padding: 40px;
            border-radius: 16px;
            border: 1px solid #334155;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        }
        .hero {
            text-align: center;
            margin-bottom: 30px;
        }
        .hero h1 {
            font-size: 32px;
            margin: 0 0 10px 0;
            color: #f8fafc;
        }
        .hero p {
            color: #94a3b8;
            margin: 0;
            font-size: 15px;
        }
        .drop-zone {
            border: 2px dashed #475569;
            padding: 40px;
            border-radius: 12px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            background: #0f172a;
        }
        .drop-zone:hover {
            border-color: #38bdf8;
            background: #131e32;
        }
        .file-preview {
            display: none;
            align-items: center;
            justify-content: space-between;
            background: #1e293b;
            padding: 12px 20px;
            border-radius: 8px;
            margin-top: 15px;
            border: 1px solid #334155;
        }
        .remove-btn {
            cursor: pointer;
            color: #ef4444;
            font-weight: bold;
            font-size: 18px;
        }
        .submit-btn {
            padding: 14px 32px;
            background: #2563eb;
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 16px;
            font-weight: 600;
            margin-top: 25px;
            cursor: pointer;
            transition: background 0.2s ease;
        }
        .submit-btn:hover {
            background: #1d4ed8;
        }
        .progress-bar {
            width: 100%;
            background: #334155;
            height: 10px;
            border-radius: 10px;
            margin-top: 20px;
            overflow: hidden;
            display: none;
        }
        .progress-fill {
            height: 100%;
            width: 0%;
            background: #38bdf8;
            transition: width 0.3s ease;
        }
        .error-alert {
            background: #450a0a;
            border: 1px solid #991b1b;
            color: #fca5a5;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .result-section {
            margin-top: 35px;
            padding-top: 25px;
            border-top: 1px solid #334155;
            text-align: center;
        }
        .result-img {
            max-width: 100%;
            border-radius: 10px;
            border: 1px solid #475569;
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
            margin-top: 15px;
        }
        footer {
            text-align: center;
            padding: 25px;
            color: #64748b;
            font-size: 14px;
            border-top: 1px solid #1e293b;
        }
    </style>
</head>
<body>
    <nav>
        <div class="logo">🎥 PanoramaAI</div>
        <div class="subtitle">Computer Vision Video Panorama Generator</div>
    </nav>

    <div class="container">
        <div class="card">
            <div class="hero">
                <h1>Video Panorama Generator</h1>
                <p>Upload a panning video to synthesize a high-resolution panoramic image visual summary.</p>
            </div>

            {% if error %}
            <div class="error-alert">
                ⚠️ {{ error }}
            </div>
            {% endif %}

            <form action="/process" method="post" enctype="multipart/form-data" onsubmit="startProgress()">
                <div class="drop-zone" onclick="document.getElementById('file').click()">
                    <p id="uploadText">
                        <strong>Click to select video file</strong><br>
                        <span style="color:#64748b; font-size:13px;">Supports MP4, AVI, MOV</span>
                    </p>
                    <input id="file" type="file" name="video" accept="video/*" required style="display:none" onchange="showFile()">
                    <div class="file-preview" id="filePreview">
                        <span id="fileName"></span>
                        <span class="remove-btn" onclick="removeFile(event)">✖</span>
                    </div>
                </div>

                <div style="text-align: center;">
                    <button type="submit" class="submit-btn" id="submitBtn">Generate Panorama</button>
                </div>

                <div class="progress-bar" id="progressBar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
            </form>

            {% if result %}
            <div class="result-section">
                <h2>Generated Panorama Result</h2>
                <img class="result-img" src="/outputs/{{result}}" alt="Panorama Result">
                <br><br>
                <a href="/outputs/{{result}}" download="panorama_result.jpg">
                    <button class="submit-btn" style="background:#059669;">⬇ Download High-Res Image</button>
                </a>
            </div>
            {% endif %}
        </div>
    </div>

    <footer>
        Made by Group-6.3 • Computer Vision & Video Processing Project
    </footer>

    <script>
        function showFile() {
            let file = document.getElementById("file").files[0];
            if (file) {
                document.getElementById("fileName").innerText = file.name;
                document.getElementById("filePreview").style.display = "flex";
                document.getElementById("uploadText").style.display = "none";
            }
        }

        function removeFile(e) {
            e.stopPropagation();
            document.getElementById("file").value = "";
            document.getElementById("filePreview").style.display = "none";
            document.getElementById("uploadText").style.display = "block";
        }

        function startProgress() {
            document.getElementById("progressBar").style.display = "block";
            document.getElementById("submitBtn").disabled = true;
            document.getElementById("submitBtn").innerText = "Processing Video...";
            
            let fill = document.getElementById("progressFill");
            let width = 0;
            let interval = setInterval(function() {
                if (width >= 90) {
                    clearInterval(interval);
                } else {
                    width += 5;
                    fill.style.width = width + "%";
                }
            }, 300);
        }
    </script>
</body>
</html>
"""


# ------------------------------------------------
# ROUTES
# ------------------------------------------------

@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/process", methods=["POST"])
def process():
    if "video" not in request.files:
        return render_template_string(HTML, error="No video file selected.")

    file = request.files["video"]
    if file.filename == "":
        return render_template_string(HTML, error="No file chosen.")

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    try:
        result = process_video(save_path)
        return render_template_string(HTML, result=result)
    except Exception as e:
        logging.error(f"Error processing video: {e}")
        return render_template_string(HTML, error=str(e))


@app.route("/outputs/<filename>")
def output_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting Video Panorama Web Server on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
