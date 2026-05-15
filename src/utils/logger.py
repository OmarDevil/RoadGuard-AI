"""Logging helpers for RoadGuard AI."""

from __future__ import annotations

import logging


def get_logger(name: str = "roadguard", level: int = logging.INFO) -> logging.Logger:
    """Return a configured project logger."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger(name)

