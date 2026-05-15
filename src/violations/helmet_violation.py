"""Helmet violation rule helpers."""

from __future__ import annotations

from typing import Any, Sequence

from src.detection.helmet_detector import HelmetDetector
from src.utils.logger import get_logger

LOGGER = get_logger(__name__)


def detect_helmet_violation(
    frame: Any,
    motorcycle_bbox: Sequence[float],
    helmet_model: HelmetDetector | None,
) -> dict[str, float | str | bool | None]:
    """Detect no-helmet violations within a motorcycle/rider crop."""
    if helmet_model is None or not getattr(helmet_model, "available", False):
        LOGGER.warning("Helmet model unavailable. Skipping helmet violation detection.")
        return {"is_violation": False, "confidence": None, "violation_type": "NO_HELMET"}

    height, width = frame.shape[:2]
    x1, y1, x2, y2 = [int(round(value)) for value in motorcycle_bbox[:4]]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(width, x2), min(height, y2)
    if x2 <= x1 or y2 <= y1:
        return {"is_violation": False, "confidence": None, "violation_type": "NO_HELMET"}

    crop = frame[y1:y2, x1:x2]
    detections = helmet_model.detect(crop)
    no_helmet_detections = [item for item in detections if item["class_name"] == "no_helmet"]
    if not no_helmet_detections:
        return {"is_violation": False, "confidence": None, "violation_type": "NO_HELMET"}

    confidence = max(float(item["confidence"]) for item in no_helmet_detections)
    return {"is_violation": True, "confidence": confidence, "violation_type": "NO_HELMET"}

