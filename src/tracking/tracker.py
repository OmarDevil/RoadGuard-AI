"""Tracking wrapper built on Ultralytics YOLO track mode."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.detection.detector import VehicleDetector


class ObjectTracker:
    """Track objects across frames using ByteTrack or another Ultralytics tracker."""

    def __init__(
        self,
        model_path: str | Path,
        tracker_config: str = "bytetrack.yaml",
        confidence_threshold: float = 0.35,
        allowed_classes: set[str] | None = None,
    ) -> None:
        self.tracker_config = tracker_config
        self.detector = VehicleDetector(
            model_path=model_path,
            confidence_threshold=confidence_threshold,
            allowed_classes=allowed_classes,
        )

    def update(self, frame: Any) -> list[dict[str, Any]]:
        """Run one tracking step and return cleaned tracked detections."""
        return self.detector.track(frame, tracker_config=self.tracker_config, persist=True)

