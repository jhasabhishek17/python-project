# Video Panorama Generator

A Computer Vision web application built with Python, OpenCV, and Flask that converts uploaded video clips into seamless panoramic image visual summaries.

## How It Works

1. **Frame Extraction**: Reads incoming video streams and extracts frames at uniform interval samples.
2. **Scene Change Detection**: Calculates absolute difference scores between adjacent frames to analyze camera motion and visual variance.
3. **Keyframe Selection**: Sorts and selects optimal keyframe candidate images representing the entire video span.
4. **Panoramic Image Stitching**:
   - Uses OpenCV `Stitcher` to align, warp, and stitch keyframes into a continuous panorama.
   - Includes a custom feather-blending algorithm as a fallback for low-overlap videos.
5. **Interactive Web UI**: Built with Flask, featuring drag-and-drop uploads, progress indicators, preview displays, and download links.

## Installation

1. Navigate to the project directory:
   ```bash
   cd video-panorama-generator
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Start the web application:
```bash
python app.py
```
Or run from the repository root:
```bash
python python.py
```

Open your browser and navigate to:
```
http://localhost:8080
```

Upload a panning video clip (MP4, AVI, MOV), click **Generate Panorama**, and download the resulting high-resolution panoramic image.

## Dependencies

- `flask`
- `opencv-python`
- `numpy`
