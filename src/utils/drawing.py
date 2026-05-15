"""OpenCV drawing helpers for annotated traffic videos."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import cv2
import numpy as np

BGRColor = tuple[int, int, int]

GREEN: BGRColor = (68, 214, 44)
RED: BGRColor = (56, 56, 230)
YELLOW: BGRColor = (49, 215, 242)
BLUE: BGRColor = (230, 129, 46)
WHITE: BGRColor = (245, 245, 245)
DARK: BGRColor = (24, 28, 35)


def draw_detection_box(frame: Any, bbox: Sequence[float], label: str, color: BGRColor = GREEN) -> Any:
    """Draw a bounding box and label."""
    x1, y1, x2, y2 = _int_bbox(bbox)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    _draw_label(frame, label, (x1, max(18, y1 - 8)), color)
    return frame


def draw_track_id(frame: Any, bbox: Sequence[float], track_id: int | str | None) -> Any:
    """Draw a tracker id near a bounding box."""
    if track_id is None:
        return frame
    x1, _, x2, y2 = _int_bbox(bbox)
    _draw_label(frame, f"ID {track_id}", (x1, min(frame.shape[0] - 8, y2 + 22)), BLUE)
    return frame


def draw_lane_polygons(frame: Any, lanes: Mapping[str, Any]) -> Any:
    """Draw all configured lane polygons."""
    for index, (lane_id, lane_config) in enumerate(lanes.items()):
        polygon = lane_config.get("points", lane_config) if isinstance(lane_config, Mapping) else lane_config
        color = (40 + index * 50 % 180, 190, 220)
        _draw_polygon(frame, polygon, color=color, alpha=0.18)
        points = np.asarray(polygon, dtype=np.int32)
        label_position = tuple(points[0].tolist())
        _draw_label(frame, lane_id, label_position, color)
    return frame


def draw_zone_polygon(frame: Any, polygon: Sequence[Sequence[float]], label: str, color: BGRColor = YELLOW) -> Any:
    """Draw a named zone polygon."""
    _draw_polygon(frame, polygon, color=color, alpha=0.12)
    if polygon:
        _draw_label(frame, label, tuple(map(int, polygon[0])), color)
    return frame


def draw_violation_label(frame: Any, bbox: Sequence[float], violation_type: str) -> Any:
    """Draw an alert label on a violating object."""
    x1, y1, x2, y2 = _int_bbox(bbox)
    cv2.rectangle(frame, (x1, y1), (x2, y2), RED, 3)
    _draw_label(frame, violation_type, (x1, max(22, y1 - 12)), RED)
    return frame


def draw_dashboard_overlay(frame: Any, stats: Mapping[str, Any]) -> Any:
    """Draw compact frame-level analytics in the top-left corner."""
    lines = [
        f"Vehicles: {stats.get('total_vehicles', 0)}",
        f"Active: {stats.get('active_vehicles', 0)}",
        f"Congestion: {stats.get('congestion_level', 'Low')}",
        f"Violations: {stats.get('violations_count', 0)}",
    ]

    lane_counts = stats.get("lane_counts", {})
    for lane_id, count in lane_counts.items():
        lines.append(f"{lane_id}: {count}")

    width = 260
    height = 24 + len(lines) * 22
    overlay = frame.copy()
    cv2.rectangle(overlay, (12, 12), (12 + width, 12 + height), DARK, -1)
    cv2.addWeighted(overlay, 0.68, frame, 0.32, 0, dst=frame)

    for index, line in enumerate(lines):
        y = 42 + index * 22
        cv2.putText(frame, line, (26, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, WHITE, 1, cv2.LINE_AA)
    return frame


def _draw_polygon(frame: Any, polygon: Sequence[Sequence[float]], color: BGRColor, alpha: float) -> None:
    points = np.asarray(polygon, dtype=np.int32)
    if points.size == 0:
        return
    overlay = frame.copy()
    cv2.polylines(frame, [points], isClosed=True, color=color, thickness=2)
    cv2.fillPoly(overlay, [points], color)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, dst=frame)


def _draw_label(frame: Any, text: str, origin: tuple[int, int], color: BGRColor) -> None:
    x, y = origin
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.55
    thickness = 1
    (text_width, text_height), baseline = cv2.getTextSize(text, font, scale, thickness)
    x = max(0, min(x, frame.shape[1] - text_width - 8))
    y = max(text_height + 8, min(y, frame.shape[0] - 4))
    cv2.rectangle(
        frame,
        (x, y - text_height - baseline - 6),
        (x + text_width + 8, y + baseline + 2),
        color,
        -1,
    )
    cv2.putText(frame, text, (x + 4, y - 4), font, scale, (15, 18, 22), thickness, cv2.LINE_AA)


def _int_bbox(bbox: Sequence[float]) -> tuple[int, int, int, int]:
    return tuple(int(round(value)) for value in bbox[:4])  # type: ignore[return-value]

