"""Congestion estimation rules."""

from __future__ import annotations

from typing import Mapping


def estimate_congestion(
    active_vehicles: int,
    lane_counts: Mapping[str, int] | None = None,
    average_pixel_speed: float | None = None,
    road_zone_area: float | None = None,
    thresholds: Mapping[str, int] | None = None,
) -> dict[str, float | int | str | None]:
    """Estimate congestion level from active vehicle count.

    The optional speed value is pixel-based frame-to-frame motion, not real-world km/h.
    """
    thresholds = thresholds or {}
    medium_threshold = int(thresholds.get("medium_congestion_vehicle_count", 7))
    high_threshold = int(thresholds.get("high_congestion_vehicle_count", 15))

    if active_vehicles >= high_threshold:
        level = "High"
    elif active_vehicles >= medium_threshold:
        level = "Medium"
    else:
        level = "Low"

    density = None
    if road_zone_area and road_zone_area > 0:
        density = active_vehicles / road_zone_area

    return {
        "level": level,
        "active_vehicles": int(active_vehicles),
        "density": density,
        "avg_pixel_speed": average_pixel_speed,
        "lane_counts_total": sum(lane_counts.values()) if lane_counts else 0,
    }

