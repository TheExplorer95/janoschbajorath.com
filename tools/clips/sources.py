"""Locate a task's raw clip and recording under the runs root, and read what the
overlays draw from. Everything is read in place."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import pyarrow.parquet as pq

FEET = ("FL", "FR", "RL", "RR")
_PARTS = ("hip", "thigh", "calf")
TARGET_COLUMNS = [f"{foot}_{part}_joint_action_policy" for part in _PARTS for foot in FEET]
PAIR_TOLERANCE_S = 600


class SourceError(RuntimeError):
    pass


@dataclass(frozen=True)
class Recording:
    warmup: int
    rows: int
    event_row: int | None
    contact: np.ndarray
    desired: np.ndarray
    push_rows: tuple[int, int] | None
    frequency: float
    phase: np.ndarray
    targets: np.ndarray

    def frame_of(self, row: int) -> int:
        return row - self.warmup


def clip_path(root: Path, run: str, task: str) -> Path:
    path = Path(root) / run / "evaluations" / "videos" / "evaluation" / f"{task}-step-0.mp4"
    if not path.is_file():
        raise SourceError(f"No raw clip for task '{task}' of run '{run}': {path}")
    return path


def recording_path(root: Path, run: str, task: str) -> Path:
    found = sorted((Path(root) / run / "evaluations" / task).glob("evaluation_data_*.parquet"))
    if not found:
        raise SourceError(f"No recording for task '{task}' of run '{run}'.")
    return found[-1]


def load_recording(path: Path, env_idx: int, event_column: str | None) -> Recording:
    wanted = (["env_idx", "timestep", "warmup", "push_applied", "gait_frequency", "gait_phase"]
              + [f"{foot}_foot_contact" for foot in FEET]
              + [f"{foot}_foot_desired_contact" for foot in FEET] + TARGET_COLUMNS
              + ([event_column] if event_column else []))
    present = set(pq.read_schema(path).names)
    optional = {"push_applied"}
    missing = [name for name in wanted if name not in present and name not in optional]
    if missing:
        raise SourceError(f"Recording {path.name} lacks column(s) {missing}.")
    frame = pq.read_table(path, columns=[n for n in wanted if n in present]).to_pandas()
    frame = frame[frame["env_idx"] == env_idx].sort_values("timestep").reset_index(drop=True)
    if frame.empty:
        raise SourceError(f"Recording {path.name} holds no rows for env {env_idx}.")

    event_row = None
    if event_column:
        fired = np.flatnonzero(frame[event_column].to_numpy() > 0)
        if len(fired) != 1:
            raise SourceError(f"Recording {path.name}: '{event_column}' fires {len(fired)} "
                              f"time(s) in env {env_idx}; one event is expected.")
        event_row = int(fired[0])

    push_rows = None
    if "push_applied" in frame:
        applied = np.flatnonzero(frame["push_applied"].to_numpy() > 0)
        if len(applied):
            push_rows = (int(applied[0]), int(applied[-1]) + 1)

    settled = frame["warmup"].to_numpy() == 0
    return Recording(
        warmup=int((~settled).sum()),
        rows=len(frame),
        event_row=event_row,
        contact=frame[[f"{foot}_foot_contact" for foot in FEET]].to_numpy() > 0.5,
        desired=frame[[f"{foot}_foot_desired_contact" for foot in FEET]].to_numpy() > 0.5,
        push_rows=push_rows,
        frequency=float(np.median(frame["gait_frequency"].to_numpy()[settled])),
        phase=frame["gait_phase"].to_numpy(dtype=float),
        targets=frame[TARGET_COLUMNS].to_numpy(dtype=float),
    )


def frame_count(path: Path) -> int:
    return int(imageio_ffmpeg.count_frames_and_secs(str(path))[0])


def check_pair(clip: Path, recording_file: Path, recording: Recording, n_frames: int) -> None:
    """Refuse a raw clip that was not written by the evaluation that wrote the recording:
    the clip is overwritten by every capture while recordings accumulate."""
    expected = recording.rows - recording.warmup - 1
    if n_frames != expected:
        raise SourceError(f"{clip.name} has {n_frames} frames but {recording_file.name} "
                          f"implies {expected} frames; they are not one evaluation.")
    stamp = datetime.strptime(recording_file.stem.removeprefix("evaluation_data_"),
                              "%y%m%d_%H%M%S").timestamp()
    apart = abs(clip.stat().st_mtime - stamp)
    if apart > PAIR_TOLERANCE_S:
        raise SourceError(f"{clip.name} was written {apart / 60:.0f} min apart from "
                          f"{recording_file.name}; they are not one evaluation.")
