"""SQLite persistence layer for RoadGuard AI."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "database" / "roadguard.db"


def get_connection(db_path: str | Path = DB_PATH) -> sqlite3.Connection:
    """Create a SQLite connection with dictionary-like rows."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: str | Path = DB_PATH) -> None:
    """Create all required database tables when they do not already exist."""
    with get_connection(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_path TEXT NOT NULL,
                processed_path TEXT,
                uploaded_at TEXT NOT NULL,
                status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                frame_number INTEGER NOT NULL,
                track_id INTEGER,
                violation_type TEXT NOT NULL,
                confidence REAL,
                screenshot_path TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (video_id) REFERENCES videos (id)
            );

            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                total_vehicles INTEGER NOT NULL,
                lane_counts TEXT NOT NULL,
                congestion_level TEXT NOT NULL,
                processing_time REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (video_id) REFERENCES videos (id)
            );
            """
        )


def insert_video(
    filename: str,
    original_path: str,
    processed_path: str | None = None,
    status: str = "uploaded",
) -> int:
    """Insert an uploaded video row and return its id."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO videos (filename, original_path, processed_path, uploaded_at, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (filename, original_path, processed_path, _now_iso(), status),
        )
        return int(cursor.lastrowid)


def update_video_status(video_id: int, status: str, processed_path: str | None = None) -> None:
    """Update video processing status and optionally processed path."""
    with get_connection() as connection:
        if processed_path is None:
            connection.execute("UPDATE videos SET status = ? WHERE id = ?", (status, video_id))
        else:
            connection.execute(
                "UPDATE videos SET status = ?, processed_path = ? WHERE id = ?",
                (status, processed_path, video_id),
            )


def insert_violation(
    video_id: int,
    frame_number: int,
    track_id: int | None,
    violation_type: str,
    confidence: float | None,
    screenshot_path: str | None,
) -> int:
    """Insert a violation record and return its id."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO violations (
                video_id, frame_number, track_id, violation_type,
                confidence, screenshot_path, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (video_id, frame_number, track_id, violation_type, confidence, screenshot_path, _now_iso()),
        )
        return int(cursor.lastrowid)


def insert_analytics(
    video_id: int,
    total_vehicles: int,
    lane_counts: dict[str, int],
    congestion_level: str,
    processing_time: float | None,
) -> int:
    """Insert a video analytics summary row and return its id."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO analytics (
                video_id, total_vehicles, lane_counts,
                congestion_level, processing_time, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                video_id,
                total_vehicles,
                json.dumps(lane_counts),
                congestion_level,
                processing_time,
                _now_iso(),
            ),
        )
        return int(cursor.lastrowid)


def get_video(video_id: int) -> dict[str, Any] | None:
    """Return one video by id."""
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    return _row_to_dict(row)


def get_all_videos() -> list[dict[str, Any]]:
    """Return all uploaded videos ordered by newest first."""
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM videos ORDER BY uploaded_at DESC").fetchall()
    return [_row_to_dict(row) for row in rows if row is not None]


def get_violations_by_video(video_id: int) -> list[dict[str, Any]]:
    """Return all violations for a video."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM violations WHERE video_id = ? ORDER BY frame_number ASC",
            (video_id,),
        ).fetchall()
    return [_row_to_dict(row) for row in rows if row is not None]


def get_analytics_by_video(video_id: int) -> dict[str, Any] | None:
    """Return the latest analytics summary for a video."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM analytics
            WHERE video_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (video_id,),
        ).fetchone()

    analytics = _row_to_dict(row)
    if analytics and isinstance(analytics.get("lane_counts"), str):
        analytics["lane_counts"] = json.loads(analytics["lane_counts"])
    return analytics


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

