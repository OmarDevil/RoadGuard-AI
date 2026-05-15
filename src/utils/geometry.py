"""Geometry helpers for zones, lanes, and tracked object positions."""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

Point = tuple[float, float]
Polygon = Sequence[Sequence[float]]
BBox = Sequence[float]


def get_box_center(x1: float, y1: float, x2: float, y2: float) -> Point:
    """Return the center point of a bounding box."""
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def point_inside_polygon(point: Sequence[float], polygon: Polygon) -> bool:
    """Return True when a point is inside or on the boundary of a polygon."""
    if len(polygon) < 3:
        return False

    x, y = float(point[0]), float(point[1])
    try:
        import cv2
        import numpy as np

        contour = np.asarray(polygon, dtype=np.float32)
        return cv2.pointPolygonTest(contour, (x, y), False) >= 0
    except Exception:
        return _point_inside_polygon_ray_cast((x, y), polygon)


def box_inside_polygon(bbox: BBox, polygon: Polygon) -> bool:
    """Return True when the bounding-box center falls inside a polygon."""
    center = get_box_center(*bbox)
    return point_inside_polygon(center, polygon)


def calculate_distance(point1: Sequence[float], point2: Sequence[float]) -> float:
    """Calculate Euclidean distance between two points."""
    return math.dist((float(point1[0]), float(point1[1])), (float(point2[0]), float(point2[1])))


def calculate_polygon_area(polygon: Polygon) -> float:
    """Calculate polygon area in pixel-space using the shoelace formula."""
    if len(polygon) < 3:
        return 0.0

    area = 0.0
    points = [(float(point[0]), float(point[1])) for point in polygon]
    for index, (x1, y1) in enumerate(points):
        x2, y2 = points[(index + 1) % len(points)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def assign_point_to_lane(point: Sequence[float], lanes: Mapping[str, Any]) -> str | None:
    """Return the first lane id containing a point, or None when no lane matches."""
    for lane_id, lane_config in lanes.items():
        polygon = lane_config.get("points", lane_config) if isinstance(lane_config, Mapping) else lane_config
        if point_inside_polygon(point, polygon):
            return lane_id
    return None


def _point_inside_polygon_ray_cast(point: Point, polygon: Polygon) -> bool:
    """Fallback polygon test used when OpenCV is unavailable."""
    x, y = point
    inside = False
    vertices = [(float(px), float(py)) for px, py in polygon]
    j = len(vertices) - 1

    for i, (xi, yi) in enumerate(vertices):
        xj, yj = vertices[j]
        if _point_on_segment(point, (xi, yi), (xj, yj)):
            return True
        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi
        )
        if intersects:
            inside = not inside
        j = i

    return inside


def _point_on_segment(point: Point, segment_start: Point, segment_end: Point) -> bool:
    px, py = point
    x1, y1 = segment_start
    x2, y2 = segment_end
    cross_product = (py - y1) * (x2 - x1) - (px - x1) * (y2 - y1)
    if abs(cross_product) > 1e-6:
        return False
    return min(x1, x2) - 1e-6 <= px <= max(x1, x2) + 1e-6 and min(y1, y2) - 1e-6 <= py <= max(y1, y2) + 1e-6

