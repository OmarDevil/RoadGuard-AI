"""Rule-based wrong-way driving detection."""

from __future__ import annotations

from typing import Sequence


def detect_wrong_way(
    track_points: Sequence[Sequence[float]],
    expected_direction: str,
    min_movement: float,
) -> dict[str, object]:
    """Detect movement opposite to the expected lane direction."""
    if len(track_points) < 2:
        return {
            "is_violation": False,
            "reason": "Not enough track history",
            "movement_vector": [0.0, 0.0],
        }

    start = track_points[0]
    end = track_points[-1]
    dx = float(end[0]) - float(start[0])
    dy = float(end[1]) - float(start[1])
    expected_direction = expected_direction.lower()

    opposite = False
    axis_movement = 0.0
    if expected_direction == "down":
        opposite = dy < -min_movement
        axis_movement = abs(dy)
    elif expected_direction == "up":
        opposite = dy > min_movement
        axis_movement = abs(dy)
    elif expected_direction == "right":
        opposite = dx < -min_movement
        axis_movement = abs(dx)
    elif expected_direction == "left":
        opposite = dx > min_movement
        axis_movement = abs(dx)
    else:
        return {
            "is_violation": False,
            "reason": f"Unknown expected direction: {expected_direction}",
            "movement_vector": [dx, dy],
        }

    if axis_movement < min_movement:
        return {
            "is_violation": False,
            "reason": "Movement below minimum threshold",
            "movement_vector": [dx, dy],
        }

    if opposite:
        return {
            "is_violation": True,
            "reason": f"Movement is opposite expected {expected_direction} direction",
            "movement_vector": [dx, dy],
        }

    return {
        "is_violation": False,
        "reason": "Movement follows expected direction",
        "movement_vector": [dx, dy],
    }

