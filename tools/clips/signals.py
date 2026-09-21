"""Signals derived from a recording for the overlays."""

from __future__ import annotations

import numpy as np


def deviation(targets: np.ndarray, phase: np.ndarray, first_row: int, event_row: int,
              bins: int = 36) -> np.ndarray:
    """Distance of `targets` from their mean cycle over rows [first_row, event_row), the
    cycle taken per clock-phase bin, in units of that distance's own pre-event mean."""
    index = np.minimum((phase * bins).astype(int), bins - 1)
    before = np.zeros(len(phase), dtype=bool)
    before[first_row:event_row] = True

    cycle = np.full((bins, targets.shape[1]), np.nan)
    for b in range(bins):
        rows = before & (index == b)
        if rows.any():
            cycle[b] = targets[rows].mean(axis=0)
    known = np.flatnonzero(np.isfinite(cycle[:, 0]))
    for b in np.flatnonzero(~np.isfinite(cycle[:, 0])):
        nearest = known[np.argmin(np.minimum((known - b) % bins, (b - known) % bins))]
        cycle[b] = cycle[nearest]

    distance = np.linalg.norm(targets - cycle[index], axis=1)
    trace = distance / distance[before].mean()
    trace[:first_row] = np.nan
    return trace
