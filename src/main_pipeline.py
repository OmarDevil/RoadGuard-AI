"""Main video analysis pipeline for RoadGuard AI."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any, Mapping

import cv2
import yaml

from src.analytics.lane_counter import LaneCounter
from src.analytics.metrics import average, count_active_vehicles_in_zone
from src.analytics.report_generator import generate_reports
from src.detection.helmet_detector import HelmetDetector
from src.tracking.track_memory import TrackMemory
from src.tracking.tracker import ObjectTracker
from src.utils.drawing import (
    draw_dashboard_overlay,
    draw_detection_box,
    draw_lane_polygons,
    draw_track_id,
    draw_violation_label,
    draw_zone_polygon,
)
from src.utils.geometry import assign_point_to_lane, calculate_polygon_area
from src.utils.logger import get_logger
from src.utils.video_utils import create_video_writer, get_video_info, read_video_frames, save_frame
from src.violations.congestion import estimate_congestion
from src.violations.helmet_violation import detect_helmet_violation
from src.violations.pedestrian_violation import detect_pedestrian_violation
from src.violations.wrong_way import detect_wrong_way

LOGGER = get_logger(__name__)
VEHICLE_CLASSES = {"car", "truck", "bus", "motorcycle"}


def analyze_video(
    video_path: str | Path | None = None,
    output_path: str | Path | None = None,
    config_path: str | Path = "config.yaml",
) -> dict[str, Any]:
    """Analyze a traffic video and generate annotated output plus analytics."""
    start_time = time.perf_counter()
    config_file = Path(config_path)
    config = load_config(config_file)
    project_root = config_file.resolve().parent

    input_video_path = _resolve_path(video_path or config["video"]["input_path"], project_root)
    output_video_path = _resolve_path(output_path or config["video"]["output_path"], project_root)
    screenshots_dir = project_root / "outputs" / "screenshots"
    reports_dir = project_root / "outputs" / "reports"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    frame_skip = max(1, int(config.get("video", {}).get("frame_skip", 1)))
    lanes = config.get("lanes", {})
    zones = config.get("zones", {})
    road_zone = zones.get("road_zone", {}).get("points", [])
    crosswalk_zone = zones.get("crosswalk_zone", {}).get("points", [])
    thresholds = config.get("thresholds", {})
    confidence_threshold = float(config.get("model", {}).get("confidence_threshold", 0.35))
    tracker_config = str(config.get("tracking", {}).get("tracker", "bytetrack.yaml"))
    min_track_length = int(config.get("tracking", {}).get("min_track_length", 8))

    vehicle_model = _resolve_model_path(config.get("model", {}).get("vehicle_model", "yolo11n.pt"), project_root)
    helmet_model_path = _resolve_path(config.get("model", {}).get("helmet_model", "models/helmet_detector.pt"), project_root)

    video_info = get_video_info(input_video_path)
    writer = create_video_writer(
        output_video_path,
        fps=float(video_info["fps"]),
        width=int(video_info["width"]),
        height=int(video_info["height"]),
    )

    tracker = ObjectTracker(
        model_path=vehicle_model,
        tracker_config=tracker_config,
        confidence_threshold=confidence_threshold,
    )
    helmet_detector = HelmetDetector(helmet_model_path, confidence_threshold=confidence_threshold)
    track_memory = TrackMemory()
    lane_counter = LaneCounter(lanes, vehicle_classes=VEHICLE_CLASSES)

    violations: list[dict[str, Any]] = []
    congestion_timeline: list[dict[str, Any]] = []
    active_vehicle_counts: list[int] = []
    processed_frames = 0
    road_zone_area = calculate_polygon_area(road_zone) if road_zone else None

    try:
        for frame_number, frame in read_video_frames(input_video_path):
            annotated_frame = frame.copy()
            draw_lane_polygons(annotated_frame, lanes)
            if road_zone:
                draw_zone_polygon(annotated_frame, road_zone, "road_zone")
            if crosswalk_zone:
                draw_zone_polygon(annotated_frame, crosswalk_zone, "crosswalk_zone")

            if frame_number % frame_skip != 0:
                writer.write(annotated_frame)
                continue

            processed_frames += 1
            detections = tracker.update(frame)

            active_vehicles = count_active_vehicles_in_zone(detections, road_zone, VEHICLE_CLASSES) if road_zone else 0
            active_vehicle_counts.append(active_vehicles)
            avg_pixel_speed = average(track_memory.active_vehicle_speeds(VEHICLE_CLASSES))
            congestion = estimate_congestion(
                active_vehicles=active_vehicles,
                lane_counts=lane_counter.get_counts(),
                average_pixel_speed=avg_pixel_speed,
                road_zone_area=road_zone_area,
                thresholds=thresholds,
            )
            congestion_timeline.append(
                {
                    "frame_number": frame_number,
                    "level": congestion["level"],
                    "active_vehicles": congestion["active_vehicles"],
                    "avg_pixel_speed": congestion["avg_pixel_speed"],
                }
            )

            for detection in detections:
                class_name = detection["class_name"]
                confidence = float(detection["confidence"])
                bbox = detection["bbox"]
                center = detection["center"]
                track_id = detection.get("track_id")
                label = f"{class_name} {confidence:.2f}"

                lane_id = assign_point_to_lane(center, lanes)
                if track_id is not None:
                    track_memory.update_track(track_id, class_name, center, bbox, lane_id, frame_number)
                    lane_counter.count_track(track_id, class_name, lane_id)

                draw_detection_box(annotated_frame, bbox, label)
                draw_track_id(annotated_frame, bbox, track_id)

                if track_id is not None and class_name in VEHICLE_CLASSES and lane_id:
                    _handle_wrong_way(
                        frame=annotated_frame,
                        frame_number=frame_number,
                        track_id=track_id,
                        bbox=bbox,
                        lane_id=lane_id,
                        lanes=lanes,
                        track_memory=track_memory,
                        min_track_length=min_track_length,
                        min_movement=float(thresholds.get("wrong_way_min_movement", 40)),
                        violations=violations,
                        screenshots_dir=screenshots_dir,
                    )

                if class_name == "motorcycle":
                    _handle_helmet_violation(
                        frame=annotated_frame,
                        frame_number=frame_number,
                        track_id=track_id,
                        bbox=bbox,
                        helmet_detector=helmet_detector,
                        track_memory=track_memory,
                        violations=violations,
                        screenshots_dir=screenshots_dir,
                    )

                if class_name == "person" and road_zone and crosswalk_zone:
                    _handle_pedestrian_violation(
                        frame=annotated_frame,
                        frame_number=frame_number,
                        track_id=track_id,
                        bbox=bbox,
                        road_zone=road_zone,
                        crosswalk_zone=crosswalk_zone,
                        track_memory=track_memory,
                        violations=violations,
                        screenshots_dir=screenshots_dir,
                    )

            track_memory.remove_old_tracks(frame_number)
            lane_summary = lane_counter.get_summary()
            draw_dashboard_overlay(
                annotated_frame,
                {
                    "total_vehicles": lane_summary["total_vehicles"],
                    "active_vehicles": active_vehicles,
                    "congestion_level": congestion["level"],
                    "violations_count": len(violations),
                    "lane_counts": lane_summary["lane_counts"],
                },
            )
            writer.write(annotated_frame)
    finally:
        writer.release()

    lane_summary = lane_counter.get_summary()
    result = {
        "video_path": str(input_video_path),
        "output_video_path": str(output_video_path),
        "total_frames": int(video_info["total_frames"]),
        "processed_frames": processed_frames,
        "total_vehicles": lane_summary["total_vehicles"],
        "lane_counts": lane_summary["lane_counts"],
        "busiest_lane": lane_summary["busiest_lane"],
        "violations": violations,
        "congestion_timeline": congestion_timeline,
        "congestion_summary": {
            "max_level": _max_congestion_level(congestion_timeline),
            "average_active_vehicles": average(active_vehicle_counts) or 0,
        },
        "processing_time": time.perf_counter() - start_time,
    }
    result["reports"] = generate_reports(result, reports_dir)
    LOGGER.info("Analysis complete: %s", output_video_path)
    return result


def load_config(config_path: str | Path) -> dict[str, Any]:
    """Load YAML configuration from disk."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def _handle_wrong_way(
    frame: Any,
    frame_number: int,
    track_id: int,
    bbox: list[float],
    lane_id: str,
    lanes: Mapping[str, Any],
    track_memory: TrackMemory,
    min_track_length: int,
    min_movement: float,
    violations: list[dict[str, Any]],
    screenshots_dir: Path,
) -> None:
    if track_memory.was_violation_flagged(track_id, "WRONG_WAY"):
        return

    positions = track_memory.get_recent_positions(track_id, max_points=30)
    if len(positions) < min_track_length:
        return

    expected_direction = lanes.get(lane_id, {}).get("expected_direction", "down")
    result = detect_wrong_way(positions, expected_direction, min_movement)
    if not result["is_violation"]:
        return

    draw_violation_label(frame, bbox, "WRONG_WAY")
    screenshot_path = _save_violation_screenshot(frame, screenshots_dir, "wrong_way", track_id, frame_number)
    violations.append(
        {
            "frame_number": frame_number,
            "track_id": track_id,
            "violation_type": "WRONG_WAY",
            "confidence": None,
            "screenshot_path": screenshot_path,
            "reason": result["reason"],
            "movement_vector": result["movement_vector"],
        }
    )
    track_memory.flag_violation(track_id, "WRONG_WAY")


def _handle_helmet_violation(
    frame: Any,
    frame_number: int,
    track_id: int | None,
    bbox: list[float],
    helmet_detector: HelmetDetector,
    track_memory: TrackMemory,
    violations: list[dict[str, Any]],
    screenshots_dir: Path,
) -> None:
    violation_type = "NO_HELMET"
    if track_id is not None and track_memory.was_violation_flagged(track_id, violation_type):
        return

    result = detect_helmet_violation(frame, bbox, helmet_detector)
    if not result["is_violation"]:
        return

    draw_violation_label(frame, bbox, violation_type)
    screenshot_path = _save_violation_screenshot(frame, screenshots_dir, "no_helmet", track_id, frame_number)
    violations.append(
        {
            "frame_number": frame_number,
            "track_id": track_id,
            "violation_type": violation_type,
            "confidence": result["confidence"],
            "screenshot_path": screenshot_path,
        }
    )
    if track_id is not None:
        track_memory.flag_violation(track_id, violation_type)


def _handle_pedestrian_violation(
    frame: Any,
    frame_number: int,
    track_id: int | None,
    bbox: list[float],
    road_zone: list[list[float]],
    crosswalk_zone: list[list[float]],
    track_memory: TrackMemory,
    violations: list[dict[str, Any]],
    screenshots_dir: Path,
) -> None:
    violation_type = "PEDESTRIAN_OUTSIDE_CROSSWALK"
    if track_id is not None and track_memory.was_violation_flagged(track_id, violation_type):
        return

    result = detect_pedestrian_violation(bbox, road_zone, crosswalk_zone)
    if not result["is_violation"]:
        return

    draw_violation_label(frame, bbox, violation_type)
    screenshot_path = _save_violation_screenshot(frame, screenshots_dir, "pedestrian", track_id, frame_number)
    violations.append(
        {
            "frame_number": frame_number,
            "track_id": track_id,
            "violation_type": violation_type,
            "confidence": None,
            "screenshot_path": screenshot_path,
            "reason": result["reason"],
        }
    )
    if track_id is not None:
        track_memory.flag_violation(track_id, violation_type)


def _save_violation_screenshot(
    frame: Any,
    screenshots_dir: Path,
    prefix: str,
    track_id: int | None,
    frame_number: int,
) -> str:
    track_label = "unknown" if track_id is None else str(track_id)
    screenshot_path = screenshots_dir / f"{prefix}_{track_label}_{frame_number}.jpg"
    return save_frame(frame, screenshot_path)


def _max_congestion_level(timeline: list[dict[str, Any]]) -> str:
    order = {"Low": 0, "Medium": 1, "High": 2}
    if not timeline:
        return "Low"
    return max((str(item.get("level", "Low")) for item in timeline), key=lambda level: order.get(level, 0))


def _resolve_path(path: str | Path, project_root: Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else project_root / candidate


def _resolve_model_path(path: str | Path, project_root: Path) -> str:
    """Resolve local model files while allowing Ultralytics model aliases like yolo11n.pt."""
    candidate = Path(path)
    if candidate.is_absolute() or candidate.exists():
        return str(candidate)
    local_candidate = project_root / candidate
    if local_candidate.exists():
        return str(local_candidate)
    return str(path)


def main() -> None:
    """CLI entrypoint for direct pipeline execution."""
    parser = argparse.ArgumentParser(description="Run RoadGuard AI video analysis.")
    parser.add_argument("--video", type=str, default=None, help="Input video path.")
    parser.add_argument("--output", type=str, default=None, help="Annotated output video path.")
    parser.add_argument("--config", type=str, default="config.yaml", help="Config YAML path.")
    args = parser.parse_args()

    result = analyze_video(video_path=args.video, output_path=args.output, config_path=args.config)
    print(f"Processed video: {result['output_video_path']}")
    print(f"Total vehicles: {result['total_vehicles']}")
    print(f"Violations: {len(result['violations'])}")


if __name__ == "__main__":
    main()

