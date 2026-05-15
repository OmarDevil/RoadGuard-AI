"""Model loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_yolo_model(model_path: str | Path) -> Any:
    """Load an Ultralytics YOLO model with a clear dependency error."""
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise ImportError(
            "Ultralytics is required for YOLO inference. Install dependencies with "
            "`pip install -r requirements.txt`."
        ) from exc

    return YOLO(str(model_path))

