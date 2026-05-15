"""Video analysis route."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from api.database import (
    ROOT_DIR,
    get_video,
    insert_analytics,
    insert_violation,
    update_video_status,
)
from src.main_pipeline import analyze_video

router = APIRouter()


@router.post("/analyze/{video_id}")
def analyze_uploaded_video(video_id: int) -> dict:
    """Run the RoadGuard AI pipeline for an uploaded video."""
    video = get_video(video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found.")

    original_path = Path(video["original_path"])
    if not original_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded video file is missing.")

    output_path = ROOT_DIR / "outputs" / "processed_videos" / f"video_{video_id}_{original_path.stem}_processed.mp4"

    update_video_status(video_id, "processing")
    try:
        result = analyze_video(
            video_path=original_path,
            output_path=output_path,
            config_path=ROOT_DIR / "config.yaml",
        )
    except Exception as exc:
        update_video_status(video_id, "failed")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    update_video_status(video_id, "completed", processed_path=result["output_video_path"])

    for violation in result.get("violations", []):
        insert_violation(
            video_id=video_id,
            frame_number=int(violation.get("frame_number", 0)),
            track_id=violation.get("track_id"),
            violation_type=str(violation.get("violation_type", "UNKNOWN")),
            confidence=violation.get("confidence"),
            screenshot_path=violation.get("screenshot_path"),
        )

    insert_analytics(
        video_id=video_id,
        total_vehicles=int(result.get("total_vehicles", 0)),
        lane_counts=result.get("lane_counts", {}),
        congestion_level=result.get("congestion_summary", {}).get("max_level", "Low"),
        processing_time=result.get("processing_time"),
    )

    result["video_id"] = video_id
    return result

