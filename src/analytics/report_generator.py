"""Report generation for RoadGuard AI analysis results."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def generate_reports(result: dict[str, Any], output_dir: str | Path = "outputs/reports") -> dict[str, str]:
    """Generate JSON and CSV reports from a completed analysis result."""
    reports_dir = Path(output_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    video_stem = Path(result.get("video_path", "analysis")).stem or "analysis"
    json_path = reports_dir / f"{video_stem}_analysis.json"
    csv_path = reports_dir / f"{video_stem}_summary.csv"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, default=str)

    violation_counts = Counter(
        violation.get("violation_type", "UNKNOWN") for violation in result.get("violations", [])
    )

    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["section", "key", "value"])
        writer.writerow(["video", "filename", Path(result.get("video_path", "")).name])
        writer.writerow(["video", "processed_video", result.get("output_video_path", "")])
        writer.writerow(["analytics", "total_vehicles", result.get("total_vehicles", 0)])
        writer.writerow(
            ["analytics", "congestion_level", result.get("congestion_summary", {}).get("max_level", "Low")]
        )

        for lane_id, count in result.get("lane_counts", {}).items():
            writer.writerow(["lane_counts", lane_id, count])

        for violation_type, count in violation_counts.items():
            writer.writerow(["violation_counts", violation_type, count])

        writer.writerow([])
        writer.writerow(["frame_number", "track_id", "violation_type", "confidence", "screenshot_path"])
        for violation in result.get("violations", []):
            writer.writerow(
                [
                    violation.get("frame_number"),
                    violation.get("track_id"),
                    violation.get("violation_type"),
                    violation.get("confidence"),
                    violation.get("screenshot_path"),
                ]
            )

    return {"json_report": str(json_path), "csv_report": str(csv_path)}

