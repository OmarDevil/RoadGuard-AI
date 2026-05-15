"""Lane-based vehicle counting."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence

from src.utils.geometry import assign_point_to_lane


class LaneCounter:
    """Count tracked vehicles per lane, once per track id per lane."""

    DEFAULT_VEHICLE_CLASSES = {"car", "truck", "bus", "motorcycle"}

    def __init__(
        self,
        lanes: Mapping[str, Any],
        vehicle_classes: set[str] | None = None,
    ) -> None:
        self.lanes = lanes
        self.vehicle_classes = vehicle_classes or self.DEFAULT_VEHICLE_CLASSES
        self.counts: dict[str, int] = {lane_id: 0 for lane_id in lanes}
        self.counted_track_ids: dict[str, set[int]] = defaultdict(set)

    def update(self, track_id: int, class_name: str, center: Sequence[float]) -> str | None:
        """Assign a vehicle to a lane and count it once for that lane."""
        lane_id = assign_point_to_lane(center, self.lanes)
        if lane_id is not None:
            self.count_track(track_id, class_name, lane_id)
        return lane_id

    def count_track(self, track_id: int, class_name: str, lane_id: str | None) -> None:
        """Count an already lane-assigned track."""
        if lane_id is None or class_name not in self.vehicle_classes:
            return
        if track_id in self.counted_track_ids[lane_id]:
            return
        self.counted_track_ids[lane_id].add(track_id)
        self.counts[lane_id] = self.counts.get(lane_id, 0) + 1

    def get_counts(self) -> dict[str, int]:
        """Return vehicle counts by lane."""
        return dict(self.counts)

    def get_summary(self) -> dict[str, Any]:
        """Return lane counts, total vehicles, and the busiest lane."""
        total_vehicles = sum(self.counts.values())
        busiest_lane = max(self.counts, key=self.counts.get) if self.counts else None
        return {
            "lane_counts": self.get_counts(),
            "total_vehicles": total_vehicles,
            "busiest_lane": busiest_lane,
        }

