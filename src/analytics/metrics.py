"""Analytics helpers for active objects and motion metrics."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from src.utils.geometry import point_inside_polygon


def count_active_vehicles_in_zone(
    detections: Iterable[Mapping[str, Any]],
    road_zone: Sequence[Sequence[float]],
    vehicle_classes: set[str],
) -> int:
    """Count current-frame vehicle centers inside a road zone."""
    count = 0
    for detection in detections:
        if detection.get("class_name") not in vehicle_classes:
            continue
        center = detection.get("center")
        if center and point_inside_polygon(center, road_zone):
            count += 1
    return count


def average(values: Iterable[float]) -> float | None:
    """Return the average value or None for an empty iterable."""
    values_list = list(values)
    if not values_list:
        return None
    return sum(values_list) / len(values_list)

