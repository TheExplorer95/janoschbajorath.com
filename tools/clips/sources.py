"""Locate a task's raw clip and recording under the runs root, and read what the
overlays draw from. Everything is read in place."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import pyarrow.parquet as pq

FEET = ("FL", "FR", "RL", "RR")
_PARTS = ("hip", "thigh", "calf")
TARGET_COLUMNS = [f"{foot}_{part}_joint_action_policy" for part in _PARTS for foot in FEET]
PUSH_BAND_COLUMNS = ("push_applied", "robot_trunk_wrench_window_open")   # WHERE, then SAB
COMMAND_COLUMNS = ("cmd_lin_x", "cmd_lin_y", "cmd_ang_z")
LATENT_NODE = "dynamics_encoder"
LATENT_WIDTH = 16
PAIR_TOLERANCE_S = 600


class SourceError(RuntimeError):
    pass


@dataclass(frozen=True)
class Recording:
    warmup: int
    rows: int
    event_row: int | None
    dt: float                 # seconds per row, the recorder's control period
    contact: np.ndarray
    desired: np.ndarray
    push_rows: tuple[int, int] | None
    frequency: float
    phase: np.ndarray
    targets: np.ndarray
    latent: np.ndarray | None = None      # (rows, LATENT_WIDTH), the block the policy reads
    commands: np.ndarray | None = None    # (rows, 3) over COMMAND_COLUMNS
    block: str | None = None

    def frame_of(self, row: int) -> int:
        return row - self.warmup


def clip_path(root: Path, run: str, task: str, checkpoint: str | None = None) -> Path:
    name = f"{task}-{checkpoint}-step-0.mp4" if checkpoint else f"{task}-step-0.mp4"
    path = Path(root) / run / "evaluations" / "videos" / "evaluation" / name
    if not path.is_file():
        raise SourceError(f"No raw clip for task '{task}' of run '{run}': {path}")
    return path


def recording_path(root: Path, run: str, task: str, checkpoint: str | None = None) -> Path:
    folder = Path(root) / run / "evaluations" / task
    if checkpoint:
        folder = folder / checkpoint
    found = sorted(folder.glob("evaluation_data_*.parquet"))
    if not found:
        raise SourceError(f"No recording for task '{task}' of run '{run}' under {folder}.")
    return found[-1]


def recording_meta(path: Path) -> dict:
    """The `.meta.json` the recorder writes beside a recording."""
    meta = path.with_suffix(".meta.json")
    if not meta.is_file():
        raise SourceError(f"Recording {path.name} has no meta file: {meta}")
    return json.loads(meta.read_text())


def latent_block(meta: dict) -> str:
    """The block of the dynamics encoder that the policy edge reads, as the meta names it."""
    for entry in meta.get("latent_blocks", []):
        if entry.get("node") == LATENT_NODE:
            return entry["read_block"]
    raise SourceError(f"Recording meta names no latent block for node '{LATENT_NODE}'.")


def latent_columns(block: str) -> list[str]:
    return [f"{LATENT_NODE}_{block}_{i}" for i in range(LATENT_WIDTH)]


def load_recording(path: Path, env_idx: int, event_column: str | None, *,
                   latent: bool = False) -> Recording:
    """One environment's rows in step order. With `latent`, also the latent block the
    recording's meta names and the command columns the nominal table is keyed by."""
    wanted = (["env_idx", "timestep", "warmup", *PUSH_BAND_COLUMNS, "gait_frequency", "gait_phase"]
              + [f"{foot}_foot_contact" for foot in FEET]
              + [f"{foot}_foot_desired_contact" for foot in FEET] + TARGET_COLUMNS
              + ([event_column] if event_column else []))
    meta = recording_meta(path)
    if "control_dt_s" not in meta:
        raise SourceError(f"Recording {path.name}: its meta names no control_dt_s.")
    block = None
    if latent:
        block = latent_block(meta)
        wanted += latent_columns(block) + list(COMMAND_COLUMNS)
    present = set(pq.read_schema(path).names)
    if block and not all(name in present for name in latent_columns(block)):
        raise SourceError(f"Recording {path.name} carries no columns {LATENT_NODE}_{block}_0.."
                          f"{LATENT_WIDTH - 1} for the block '{block}' its meta names.")
    missing = [name for name in wanted if name not in present and name not in PUSH_BAND_COLUMNS]
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
    band = next((name for name in PUSH_BAND_COLUMNS if name in frame), None)
    if band:
        applied = np.flatnonzero(frame[band].to_numpy() > 0)
        if len(applied):
            push_rows = (int(applied[0]), int(applied[-1]) + 1)

    settled = frame["warmup"].to_numpy() == 0
    return Recording(
        warmup=int((~settled).sum()),
        rows=len(frame),
        event_row=event_row,
        dt=float(meta["control_dt_s"]),
        contact=frame[[f"{foot}_foot_contact" for foot in FEET]].to_numpy() > 0.5,
        desired=frame[[f"{foot}_foot_desired_contact" for foot in FEET]].to_numpy() > 0.5,
        push_rows=push_rows,
        frequency=float(np.median(frame["gait_frequency"].to_numpy()[settled])),
        phase=frame["gait_phase"].to_numpy(dtype=float),
        targets=frame[TARGET_COLUMNS].to_numpy(dtype=float),
        latent=frame[latent_columns(block)].to_numpy(dtype=float) if block else None,
        commands=frame[list(COMMAND_COLUMNS)].to_numpy(dtype=float) if block else None,
        block=block,
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
