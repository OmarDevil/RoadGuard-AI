"""Video upload route."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.database import ROOT_DIR, insert_video

router = APIRouter()
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


@router.post("/upload-video")
async def upload_video(file: UploadFile = File(...)) -> dict[str, int | str]:
    """Accept a traffic video upload and store it on disk."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    original_name = Path(file.filename).name
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported video file type.")

    upload_dir = ROOT_DIR / "data" / "raw" / "videos"
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_filename = f"{uuid.uuid4().hex}_{original_name.replace(' ', '_')}"
    destination = upload_dir / safe_filename

    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {exc}") from exc
    finally:
        await file.close()

    video_id = insert_video(filename=original_name, original_path=str(destination), status="uploaded")
    return {"video_id": video_id, "filename": original_name, "stored_filename": safe_filename}

