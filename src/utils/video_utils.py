"""Video input/output utilities."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any

import cv2


def get_video_info(video_path: str | Path) -> dict[str, int | float]:
    """Return FPS, dimensions, frame count, and duration for a video."""
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {path}")

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError(f"Could not open video file: {path}")

    try:
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_seconds = total_frames / fps if fps > 0 else 0.0
        return {
            "fps": fps,
            "width": width,
            "height": height,
            "total_frames": total_frames,
            "duration_seconds": duration_seconds,
        }
    finally:
        capture.release()


def create_video_writer(output_path: str | Path, fps: float, width: int, height: int) -> cv2.VideoWriter:
    """Create an MP4 video writer and ensure the parent folder exists."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps or 25.0, (int(width), int(height)))
    if not writer.isOpened():
        raise ValueError(f"Could not create video writer: {path}")
    return writer


def read_video_frames(video_path: str | Path) -> Generator[tuple[int, Any], None, None]:
    """Yield frame number and frame for each frame in a video."""
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {path}")

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError(f"Could not open video file: {path}")

    frame_number = 0
    try:
        while True:
            success, frame = capture.read()
            if not success:
                break
            yield frame_number, frame
            frame_number += 1
    finally:
        capture.release()


def save_frame(frame: Any, output_path: str | Path) -> str:
    """Save a video frame as an image and return the saved path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    success = cv2.imwrite(str(path), frame)
    if not success:
        raise ValueError(f"Could not save frame to: {path}")
    return str(path)

