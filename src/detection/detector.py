"""YOLO object detection wrapper used by RoadGuard AI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.detection.model_loader import load_yolo_model
from src.utils.geometry import get_box_center


class VehicleDetector:
    """Run YOLO detection and expose clean traffic-relevant detections."""

    DEFAULT_ALLOWED_CLASSES = {"car", "truck", "bus", "motorcycle", "person", "bicycle"}

    def __init__(
        self,
        model_path: str | Path,
        confidence_threshold: float = 0.35,
        allowed_classes: set[str] | None = None,
    ) -> None:
        self.model_path = str(model_path)
        self.confidence_threshold = confidence_threshold
        self.allowed_classes = allowed_classes or self.DEFAULT_ALLOWED_CLASSES
        self.model = load_yolo_model(self.model_path)

    def detect(self, frame: Any) -> list[dict[str, Any]]:
        """Detect traffic objects in one frame."""
        results = self.model.predict(frame, conf=self.confidence_threshold, verbose=False)
        if not results:
            return []
        return self._convert_result(results[0])

    def track(
        self,
        frame: Any,
        tracker_config: str = "bytetrack.yaml",
        persist: bool = True,
    ) -> list[dict[str, Any]]:
        """Track traffic objects in one frame and return clean dictionaries."""
        results = self.model.track(
            frame,
            conf=self.confidence_threshold,
            tracker=tracker_config,
            persist=persist,
            verbose=False,
        )
        if not results:
            return []
        return self._convert_result(results[0], include_track_id=True)

    def _convert_result(self, result: Any, include_track_id: bool = False) -> list[dict[str, Any]]:
        detections: list[dict[str, Any]] = []
        boxes = getattr(result, "boxes", None)
        if boxes is None or len(boxes) == 0:
            return detections

        names = getattr(result, "names", getattr(self.model, "names", {}))

        for index, box in enumerate(boxes):
            class_id = int(box.cls[0].item())
            class_name = names.get(class_id, str(class_id)) if isinstance(names, dict) else str(class_id)
            if class_name not in self.allowed_classes:
                continue

            confidence = float(box.conf[0].item())
            if confidence < self.confidence_threshold:
                continue

            x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
            center_x, center_y = get_box_center(x1, y1, x2, y2)
            detection: dict[str, Any] = {
                "class_name": class_name,
                "confidence": confidence,
                "bbox": [x1, y1, x2, y2],
                "center": [center_x, center_y],
            }

            if include_track_id:
                track_id = None
                box_ids = getattr(boxes, "id", None)
                if box_ids is not None:
                    track_id = int(box_ids[index].item())
                detection["track_id"] = track_id

            detections.append(detection)

        return detections

