"""Check the filmed push cell against the fall pattern the poster states.

    python tools/clips/check_push.py [--root DIR]

For every run and mask task of the SAB `push` clip, prints whether the robot is down at
the end of the clip's window (a trunk or hip contact within its last `END_S` seconds) and
the first such contact after the onset, in seconds; exits 1 when the pattern the spec
expects does not hold: PPO stands under No Mask and falls under the three others; + AUX
and + Curriculum stand under No Mask and the Behavior Mask and fall under the Domain Mask
and the Full Mask. A contact the robot recovers from is printed as a graze, not a fall:
the poster's survival rule counts any contact, and on the filmed curriculum No Mask clip
that would call a 0.08 s trunk graze a fall that the clip does not show.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

import sources
from sab_2026 import CHECKPOINT, PUSH, ROOT, RUNS

FALLEN = ["trunk_contact"] + [f"{leg}_hip_contact" for leg in ("FL", "FR", "RL", "RR")]
"""The contacts of the poster's rule (`plotting/allocation/mask_survival.py`)."""

END_S = 0.5
"""A robot is down when one of `FALLEN` is true within the last `END_S` s of the window."""

EXPECTED = {"ppo": ("stands", "falls", "falls", "falls"),
            "aux": ("stands", "stands", "falls", "falls"),
            "cur": ("stands", "stands", "falls", "falls")}
"""Per run, the outcome per column of the clip; the poster's pooled result."""


def outcome(recording: Path, env_idx: int) -> tuple[bool, float | None]:
    """`(down, first)`: whether `env_idx` is down at the end of the clip's window, and the
    seconds after the onset of its first contact row in the window, None without one."""
    meta = sources.recording_meta(recording)
    dt = meta["control_dt_s"]
    columns = ["env_idx", "timestep", PUSH.event_column] + FALLEN
    table = pq.read_table(recording, columns=columns).to_pandas()
    rows = table[table["env_idx"] == env_idx].sort_values("timestep")
    onset = rows["timestep"].to_numpy()[np.flatnonzero(rows[PUSH.event_column].to_numpy() > 0)]
    if len(onset) != 1:
        raise sources.SourceError(f"{recording.name}: {len(onset)} onset rows for env {env_idx}.")
    steps = rows["timestep"].to_numpy()
    window = rows[(steps >= onset[0]) & (steps < onset[0] + PUSH.window[1])]
    contact = window[FALLEN].to_numpy(dtype=bool).any(axis=1)
    down = bool(contact[-int(round(END_S / dt)):].any())
    fallen = np.flatnonzero(contact)
    first = float(fallen[0] * dt) if len(fallen) else None
    return down, first


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    columns = PUSH.geometry.cols
    failed = False
    for row, run in enumerate(EXPECTED):
        tiles = PUSH.tiles[row * columns:(row + 1) * columns]
        results = []
        for tile, expected in zip(tiles, EXPECTED[run]):
            recording = sources.recording_path(args.root, RUNS[run], tile.task, CHECKPOINT)
            down, first = outcome(recording, PUSH.env_idx)
            seen = "falls" if down else "stands"
            mark = "" if seen == expected else "  <- expected " + expected
            failed |= bool(mark)
            if down:
                text = f"falls, first contact {first:.2f} s"
            else:
                text = "stands" if first is None else f"stands, graze at {first:.2f} s"
            results.append(f"{tile.task}: {text}{mark}")
        print(f"{run}:\n  " + "\n  ".join(results))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
