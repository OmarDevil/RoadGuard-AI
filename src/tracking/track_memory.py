"""In-memory history store for tracked objects."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Deque, Sequence


class TrackMemory:
    """Store recent movement history and metadata for tracker IDs."""

    def __init__(self, max_positions: int = 80) -> None:
        self.max_positions = max_positions
        self.tracks: dict[int, dict[str, Any]] = {}
        self.violation_flags: set[tuple[int, str]] = set()

    def update_track(
        self,
        track_id: int,
        class_name: str,
        center: Sequence[float],
        bbox: Sequence[float],
        lane_id: str | None,
        frame_number: int,
    ) -> None:
        """Create or update a track entry."""
        center_tuple = (float(center[0]), float(center[1]))
        if track_id not in self.tracks:
            self.tracks[track_id] = {
                "class_name": class_name,
                "positions": deque(maxlen=self.max_positions),
                "bboxes": deque(maxlen=self.max_positions),
                "lanes": deque(maxlen=self.max_positions),
                "first_seen": frame_number,
                "last_seen": frame_number,
            }

        track = self.tracks[track_id]
        track["class_name"] = class_name
        track["positions"].append(center_tuple)
        track["bboxes"].append([float(value) for value in bbox[:4]])
        track["lanes"].append(lane_id)
        track["last_seen"] = frame_number

    def get_track_history(self, track_id: int) -> dict[str, Any] | None:
        """Return a serializable copy of a track history."""
        track = self.tracks.get(track_id)
        if track is None:
            return None
        return {
            "class_name": track["class_name"],
            "positions": list(track["positions"]),
            "bboxes": list(track["bboxes"]),
            "lanes": list(track["lanes"]),
            "first_seen": track["first_seen"],
            "last_seen": track["last_seen"],
        }

    def get_recent_positions(self, track_id: int, max_points: int = 20) -> list[tuple[float, float]]:
        """Return the most recent positions for a track."""
        track = self.tracks.get(track_id)
        if track is None:
            return []
        return list(track["positions"])[-max_points:]

    def remove_old_tracks(self, current_frame: int, max_age: int = 100) -> None:
        """Remove tracks that have not been seen for more than max_age frames."""
        expired_track_ids = [
            track_id
            for track_id, track in self.tracks.items()
            if current_frame - int(track["last_seen"]) > max_age
        ]
        for track_id in expired_track_ids:
            del self.tracks[track_id]

    def was_violation_flagged(self, track_id: int, violation_type: str) -> bool:
        """Return True if a violation has already been recorded for a track."""
        return (track_id, violation_type) in self.violation_flags

    def flag_violation(self, track_id: int, violation_type: str) -> None:
        """Mark a track/violation pair as recorded."""
        self.violation_flags.add((track_id, violation_type))

    def active_vehicle_speeds(self, vehicle_classes: set[str]) -> list[float]:
        """Estimate per-frame pixel speed from recent track positions."""
        speeds: list[float] = []
        for track in self.tracks.values():
            if track["class_name"] not in vehicle_classes or len(track["positions"]) < 2:
                continue
            last_two = list(track["positions"])[-2:]
            dx = last_two[1][0] - last_two[0][0]
            dy = last_two[1][1] - last_two[0][1]
            speeds.append((dx * dx + dy * dy) ** 0.5)
        return speeds

    def tracks_by_frame(self) -> dict[int, list[int]]:
        """Return a helper map of last_seen frame to track ids."""
        frame_map: dict[int, list[int]] = defaultdict(list)
        for track_id, track in self.tracks.items():
            frame_map[int(track["last_seen"])].append(track_id)
        return dict(frame_map)

