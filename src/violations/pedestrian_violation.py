"""Pedestrian road-zone violation rules."""

from __future__ import annotations

from typing import Sequence

from src.utils.geometry import get_box_center, point_inside_polygon


def detect_pedestrian_violation(
    person_bbox_or_center: Sequence[float],
    road_zone: Sequence[Sequence[float]],
    crosswalk_zone: Sequence[Sequence[float]],
) -> dict[str, bool | str]:
    """Flag people inside a road zone and outside the configured crosswalk."""
    if len(person_bbox_or_center) >= 4:
        point = get_box_center(*person_bbox_or_center[:4])
    else:
        point = (float(person_bbox_or_center[0]), float(person_bbox_or_center[1]))

    inside_road = point_inside_polygon(point, road_zone)
    inside_crosswalk = point_inside_polygon(point, crosswalk_zone)

    if inside_road and not inside_crosswalk:
        return {
            "is_violation": True,
            "violation_type": "PEDESTRIAN_OUTSIDE_CROSSWALK",
            "reason": "Person detected inside road zone and outside crosswalk zone",
        }

    return {
        "is_violation": False,
        "violation_type": "PEDESTRIAN_OUTSIDE_CROSSWALK",
        "reason": "Person is outside road zone or inside crosswalk zone",
    }

