"""Segments -> the raw-frame offsets shown, in order, at 25 fps."""

from __future__ import annotations

from dataclasses import dataclass

from spec import Segment


@dataclass(frozen=True)
class Shot:
    offset: int
    """Raw frames from the anchor."""
    slow: bool


def build(segments: tuple[Segment, ...]) -> list[Shot]:
    shots: list[Shot] = []
    for segment in segments:
        step = 1 if segment.slow else 2
        shots.extend(Shot(offset, segment.slow)
                     for offset in range(segment.start, segment.end, step))
    return shots
