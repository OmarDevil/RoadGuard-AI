"""Helmet/no-helmet YOLO detector."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.detection.model_loader import load_yolo_model
from src.utils.geometry import get_box_center
from src.utils.logger import get_logger

LOGGER = get_logger(__name__)


class HelmetDetector:
    """Run helmet detection on motorcycle/rider crops."""

    HELMET_CLASSES = {"helmet", "no_helmet", "rider"}

    def __init__(self, model_path: str | Path, confidence_threshold: float = 0.35) -> None:
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.model: Any | None = None
        self.available = False
        self._load_model()

    def _load_model(self) -> None:
        if not self.model_path.exists():
            LOGGER.warning("Helmet model not found at %s. Helmet violation detection is disabled.", self.model_path)
            return
        self.model = load_yolo_model(self.model_path)
        self.available = True

    def detect(self, crop: Any) -> list[dict[str, Any]]:
        """Detect helmet classes in a cropped motorcycle/rider image."""
        if not self.available or self.model is None or crop is None or crop.size == 0:
            return []

        results = self.model.predict(crop, conf=self.confidence_threshold, verbose=False)
        if not results:
            return []

        detections: list[dict[str, Any]] = []
        result = results[0]
        names = getattr(result, "names", getattr(self.model, "names", {}))
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            return detections

        for box in boxes:
            class_id = int(box.cls[0].item())
            class_name = names.get(class_id, str(class_id)) if isinstance(names, dict) else str(class_id)
            if class_name not in self.HELMET_CLASSES:
                continue
            confidence = float(box.conf[0].item())
            x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
            detections.append(
                {
                    "class_name": class_name,
                    "confidence": confidence,
                    "bbox": [x1, y1, x2, y2],
                    "center": list(get_box_center(x1, y1, x2, y2)),
                }
            )
        return detections

