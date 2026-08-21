"""
Video Panorama Computer Vision Engine
------------------------------------
This module handles all core image processing and computer vision algorithms
for generating seamless panoramic images from video sequences.

Key capabilities:
1. Video frame sampling and keyframe extraction.
2. Motion blur detection via Laplacian variance analysis.
3. Dual-mode panorama stitching:
   - Primary: OpenCV Stitcher API (cylindrical/spherical warping).
   - Fallback: Custom Homography matching (ORB/SIFT + RANSAC) with linear gradient seam blending.
4. Automatic ROI black border trimming.
"""

import time
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


def compute_sharpness_score(image_gray):
    """
    Computes image sharpness using the variance of the Laplacian operator.
    Higher values indicate a sharper image; lower values signal motion blur.
    """
    return cv2.Laplacian(image_gray, cv2.CV_64F).var()


def extract_video_frames(video_path, sample_interval=10, max_resolution=1080):
    """
    Reads a video file and samples frames at regular intervals.
    Optionally resizes frames to max_resolution (height) to speed up matching.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Unable to open video file: {video_path}")

    frames = []
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % sample_interval == 0 and frame is not None:
            height, width = frame.shape[:2]
            if height > max_resolution:
                scale = max_resolution / float(height)
                new_width = int(width * scale)
                frame = cv2.resize(frame, (new_width, max_resolution), interpolation=cv2.INTER_AREA)

            frames.append(frame)

        frame_count += 1

    cap.release()
    return frames, frame_count


def filter_blur_and_select_keyframes(frames, max_keyframes=8, min_blur_score=50.0):
    """
    Filters out motion-blurred frames and selects representative keyframes
    spaced across the video panning sequence.
    """
    if not frames:
        return []

    # Score frames based on sharpness and inter-frame motion variance
    scored_frames = []
    prev_gray = None

    for idx, frame in enumerate(frames):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur_score = compute_sharpness_score(gray)

        # Skip severely blurred frames unless min_blur_score threshold is zero
        if min_blur_score > 0 and blur_score < min_blur_score:
            continue

        # Calculate visual difference from previous frame to ensure motion diversity
        motion_score = 0.0
        if prev_gray is not None:
            diff = cv2.absdiff(gray, prev_gray)
            motion_score = float(np.mean(diff))

        scored_frames.append({
            'index': idx,
            'frame': frame,
            'blur_score': blur_score,
            'motion_score': motion_score
        })
        prev_gray = gray

    # If strict blur filtering discarded all frames, fall back to unfiltered frames
    if not scored_frames:
        scored_frames = [{'index': i, 'frame': f, 'blur_score': 100.0, 'motion_score': 1.0} for i, f in enumerate(frames)]

    # Limit keyframe selection based on spatial spread
    if len(scored_frames) <= max_keyframes:
        return [item['frame'] for item in scored_frames]

    # Uniformly select keyframes across the timeline
    step = len(scored_frames) / float(max_keyframes)
    selected_indices = [int(i * step) for i in range(max_keyframes)]
    return [scored_frames[i]['frame'] for i in selected_indices if i < len(scored_frames)]


def blend_two_images_feather(img_left, img_right):
    """
    Custom homography fallback blender.
    Performs linear gradient alpha blending (feathering) across overlapping regions
    to avoid harsh lighting and exposure transitions between adjacent frames.
    """
    h1, w1 = img_left.shape[:2]
    h2, w2 = img_right.shape[:2]

    target_h = max(h1, h2)
    img_left = cv2.resize(img_left, (int(w1 * target_h / h1), target_h))
    img_right = cv2.resize(img_right, (int(w2 * target_h / h2), target_h))

    w1_res = img_left.shape[1]
    w2_res = img_right.shape[1]

    overlap = min(80, w1_res // 3, w2_res // 3)
    if overlap < 10:
        return np.hstack([img_left, img_right])

    left_part = img_left[:, :-overlap]
    right_part = img_right[:, overlap:]

    blend_left = img_left[:, -overlap:].astype(np.float32)
    blend_right = img_right[:, :overlap].astype(np.float32)

    # Construct linear alpha ramp: 0.0 -> 1.0
    alpha = np.linspace(0.0, 1.0, overlap).reshape(1, overlap, 1)
    blended_middle = (1.0 - alpha) * blend_left + alpha * blend_right

    panorama = np.hstack([left_part, blended_middle.astype(np.uint8), right_part])
    return panorama


def stitch_homography_fallback(frames):
    """
    Feature matching and homography matrix estimation (RANSAC).
    Used as a fallback when OpenCV Stitcher fails to find enough feature matches.
    """
    if not frames:
        return None
    if len(frames) == 1:
        return frames[0]

    current_pano = frames[0]
    orb = cv2.ORB_create(nfeatures=2000)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    for i in range(1, len(frames)):
        next_frame = frames[i]
        try:
            kp1, des1 = orb.detectAndCompute(current_pano, None)
            kp2, des2 = orb.detectAndCompute(next_frame, None)

            if des1 is None or des2 is None or len(des1) < 10 or len(des2) < 10:
                current_pano = blend_two_images_feather(current_pano, next_frame)
                continue

            matches = bf.match(des1, des2)
            matches = sorted(matches, key=lambda x: x.distance)

            if len(matches) > 10:
                src_pts = np.float32([kp1[m.queryIdx].pt for m in matches[:30]]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches[:30]]).reshape(-1, 1, 2)

                H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)
                if H is not None:
                    h1, w1 = current_pano.shape[:2]
                    h2, w2 = next_frame.shape[:2]

                    # Warp right frame onto perspective of left frame
                    warped = cv2.warpPerspective(next_frame, H, (w1 + w2, max(h1, h2)))
                    warped[0:h1, 0:w1] = current_pano
                    current_pano = warped
                else:
                    current_pano = blend_two_images_feather(current_pano, next_frame)
            else:
                current_pano = blend_two_images_feather(current_pano, next_frame)
        except Exception as err:
            logger.warning("Homography step failed: %s. Using linear blending.", err)
            current_pano = blend_two_images_feather(current_pano, next_frame)

    return current_pano


def crop_black_borders(image):
    """
    Trims black margins around the stitched panorama generated by perspective warping.
    """
    if image is None or image.size == 0:
        return image

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        c = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c)
        if w > 20 and h > 20:
            return image[y:y+h, x:x+w]

    return image


def process_video_pipeline(video_path, sample_interval=10, max_keyframes=8, min_blur_score=40.0, mode="auto", max_resolution=1080):
    """
    Main Computer Vision orchestration pipeline.
    
    Returns:
        tuple: (stitched_image_numpy, metrics_dict)
    """
    start_time = time.time()

    # Step 1: Read video and sample frames
    raw_frames, total_video_frames = extract_video_frames(
        video_path,
        sample_interval=sample_interval,
        max_resolution=max_resolution
    )

    if not raw_frames:
        raise ValueError("No readable video frames found. Please verify video format and codec.")

    # Step 2: Blur rejection & keyframe selection
    keyframes = filter_blur_and_select_keyframes(
        raw_frames,
        max_keyframes=max_keyframes,
        min_blur_score=min_blur_score
    )

    if not keyframes:
        keyframes = raw_frames[:max_keyframes]

    stitched_result = None
    stitch_method_used = "opencv_stitcher"

    # Step 3: Stitch keyframes into panorama
    if mode in ["auto", "opencv"]:
        try:
            stitcher = cv2.Stitcher_create(cv2.Stitcher_PANORAMA)
            status, pano = stitcher.stitch(keyframes)
            if status == cv2.Stitcher_OK and pano is not None:
                stitched_result = pano
            else:
                logger.info("OpenCV Stitcher status code %s. Falling back to Homography.", status)
        except Exception as e:
            logger.warning("OpenCV Stitcher exception: %s. Switching to fallback engine.", e)

    if stitched_result is None or mode == "homography":
        stitch_method_used = "homography_feather"
        stitched_result = stitch_homography_fallback(keyframes)

    if stitched_result is None:
        raise ValueError("Panorama construction failed. Ensure the video contains smooth, overlapping horizontal movement.")

    # Step 4: Crop black background borders
    final_panorama = crop_black_borders(stitched_result)
    elapsed_time = round(time.time() - start_time, 2)

    height, width = final_panorama.shape[:2]
    metrics = {
        "total_video_frames": total_video_frames,
        "sampled_frames": len(raw_frames),
        "selected_keyframes": len(keyframes),
        "stitch_method": stitch_method_used,
        "resolution": f"{width}x{height} px",
        "processing_time_sec": elapsed_time
    }

    return final_panorama, metrics
