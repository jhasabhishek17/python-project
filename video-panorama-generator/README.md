# Video Panorama Generator Studio

A high-performance Computer Vision web application and REST API built with **Python**, **OpenCV**, and **Flask**. This system processes smooth video panning sequences (MP4, MOV, AVI) and synthesizes seamless high-resolution panoramic visual summaries.

---

## 🌟 Key Features

- **Automated Blur Rejection**: Evaluates frame sharpness via Laplacian variance operator (`cv2.Laplacian`) to discard blurry motion frames captured during fast panning.
- **Dual-Mode Stitching Pipeline**:
  - **Primary**: OpenCV `Stitcher` API (uses spherical/cylindrical camera models and multi-band blending).
  - **Fallback**: Feature matching engine using **ORB/SIFT**, **RANSAC** homography estimation (`cv2.findHomography`), and **Linear Feather Gradient Blending** for seamless lighting cross-fades.
- **Automatic ROI Border Trimming**: Detects black margins created by perspective transformations and crops the final output cleanly.
- **Modern Web Dashboard**: Features custom dark UI styling, drag-and-drop video file upload, configurable quality controls, real-time status indicators, processing metrics, and image downloads.
- **RESTful API**: JSON API endpoints (`/api/process`, `/api/health`) for programmatic video stitching integration.

---

## ⚙️ Computer Vision Architecture

```
                    ┌─────────────────────────┐
                    │    Input Video Clip     │
                    └────────────┬────────────┘
                                 │
                   ┌─────────────▼─────────────┐
                   │ Frame Sampling & Downscale │
                   └─────────────┬─────────────┘
                                 │
                   ┌─────────────▼─────────────┐
                   │  Laplacian Blur Filtering │
                   └─────────────┬─────────────┘
                                 │
                   ┌─────────────▼─────────────┐
                   │ Spatial Keyframe Selection │
                   └─────────────┬─────────────┘
                                 │
                ┌────────────────┴────────────────┐
                ▼                                 ▼
   ┌──────────────────────────┐     ┌──────────────────────────┐
   │ OpenCV Stitcher Engine   │     │  Homography & Feature    │
   │ (Multi-band / Spherical) │     │  Matching Engine (RANSAC)│
   └────────────┬─────────────┘     └────────────┬─────────────┘
                │                                 │
                └────────────────┬────────────────┘
                                 │
                   ┌─────────────▼─────────────┐
                   │ Automatic ROI Border Crop │
                   └─────────────┬─────────────┘
                                 │
                   ┌─────────────▼─────────────┐
                   │  High-Res Panorama Output │
                   └───────────────────────────┘
```

---

## 🚀 Quickstart & Installation

### 1. Requirements

Ensure you have Python 3.9+ installed on your system.

### 2. Install Dependencies

Navigate to the project directory and install required Python packages:

```bash
cd video-panorama-generator
pip install -r requirements.txt
```

### 3. Run the Server

Start the application using standard Python:

```bash
python app.py
```

Or from the repository root:

```bash
python video-panorama-generator/python.py
```

Open your web browser and navigate to:
```
http://localhost:8080
```

---

## 📡 REST API Documentation

### 1. Health Check

- **Endpoint**: `GET /api/health`
- **Response**:
```json
{
  "service": "video-panorama-generator",
  "status": "healthy"
}
```

### 2. Process Video API

- **Endpoint**: `POST /api/process`
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `video` *(file, required)*: The target video file (.mp4, .mov, .avi).
  - `mode` *(string, optional)*: `auto`, `opencv`, or `homography`. Default is `auto`.
  - `max_keyframes` *(int, optional)*: Keyframe limit (e.g. `5`, `8`, `12`). Default is `8`.
  - `blur_thresh` *(float, optional)*: Blur score threshold. Default is `40.0`.
  - `resolution` *(int, optional)*: Processing max resolution height (e.g. `720`, `1080`, `1440`). Default is `1080`.

- **Example Response**:
```json
{
  "success": true,
  "result_url": "/outputs/pano_api_a1b2c3d4e5.jpg",
  "metrics": {
    "total_video_frames": 240,
    "sampled_frames": 30,
    "selected_keyframes": 8,
    "stitch_method": "opencv_stitcher",
    "resolution": "3420x1080 px",
    "processing_time_sec": 3.42
  }
}
```

---

## 📂 Directory Structure

```
video-panorama-generator/
├── app.py              # Flask web server, dashboard UI template, and API routes
├── cv_engine.py        # Core Computer Vision pipeline & stitching logic
├── python.py           # Launcher entrypoint script
├── requirements.txt    # Project dependencies
├── README.md           # Documentation
├── uploads/            # Temporary directory for video uploads
└── outputs/            # Output directory for generated panoramas
```

---

## 📄 License

Distributed under the MIT License. Feel free to use and modify for academic or production applications.
