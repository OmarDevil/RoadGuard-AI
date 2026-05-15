"""Read-only API routes for videos, analytics, violations, and files."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.database import (
    ROOT_DIR,
    get_all_videos,
    get_analytics_by_video,
    get_video,
    get_violations_by_video,
)

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Return API health status."""
    return {"status": "ok", "service": "RoadGuard AI API"}


@router.get("/videos")
def list_videos() -> list[dict]:
    """Return all uploaded videos."""
    return get_all_videos()


@router.get("/videos/{video_id}")
def read_video(video_id: int) -> dict:
    """Return one video record."""
    video = get_video(video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found.")
    return video


@router.get("/analytics/{video_id}")
def read_analytics(video_id: int) -> dict:
    """Return analytics summary for one video."""
    analytics = get_analytics_by_video(video_id)
    if analytics is None:
        raise HTTPException(status_code=404, detail="Analytics not found.")
    return analytics


@router.get("/violations/{video_id}")
def read_violations(video_id: int) -> list[dict]:
    """Return violations for one video."""
    if get_video(video_id) is None:
        raise HTTPException(status_code=404, detail="Video not found.")
    return get_violations_by_video(video_id)


@router.get("/processed-video/{video_id}")
def processed_video(video_id: int) -> FileResponse:
    """Return the processed video file for playback."""
    video = get_video(video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found.")

    processed_path = video.get("processed_path")
    if not processed_path:
        raise HTTPException(status_code=404, detail="Processed video not available.")

    path = Path(processed_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Processed video file is missing.")

    return FileResponse(path, media_type="video/mp4", filename=path.name)


@router.get("/screenshots/{filename}")
def screenshot(filename: str) -> FileResponse:
    """Return a saved violation screenshot by filename."""
    path = ROOT_DIR / "outputs" / "screenshots" / Path(filename).name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Screenshot not found.")
    return FileResponse(path, media_type="image/jpeg", filename=path.name)

