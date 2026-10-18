import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import sources
from sources import SourceError

JOINTS = [f"{leg}_{part}_joint_action_policy" for part in ("hip", "thigh", "calf")
          for leg in ("FL", "FR", "RL", "RR")]


def _write(path: Path, *, rows=40, warmup=4, event_row=20, envs=2, push=(20, 24), drop=(),
           checkpoint=None, window=True, latent_block=None, meta_block=None, episodes=1):
    """A recording in the WHERE layout with its `.meta.json` (control period 0.02 s), plus
    the SAB window columns (`window`), the latent block and command columns (`latent_block`;
    the meta then names `meta_block` when given) and `episodes` respawns per environment."""
    table = {"env_idx": [], "timestep": [], "warmup": [], "episode_id": [], "truncated": []}
    columns = (["clock_jump_fired", "push_applied", "gait_frequency", "gait_phase"]
               + [f"{f}_foot_contact" for f in sources.FEET]
               + [f"{f}_foot_desired_contact" for f in sources.FEET] + JOINTS
               + (["robot_trunk_wrench_window_open", "robot_trunk_wrench_window_onset"]
                  if window else [])
               + ([f"dynamics_encoder_{latent_block}_{i}" for i in range(16)]
                  + list(sources.COMMAND_COLUMNS) if latent_block else []))
    for name in columns:
        table[name] = []
    for env in range(envs):
        for row in range(rows):
            episode = row * episodes // rows
            table["env_idx"].append(env)
            table["timestep"].append(row)
            table["warmup"].append(1 if row < warmup else 0)
            table["episode_id"].append(episode)
            table["truncated"].append(1.0 if (row + 1) * episodes // rows > episode else 0.0)
            table["clock_jump_fired"].append(1.0 if (row == event_row and env == 0) else 0.0)
            table["push_applied"].append(1.0 if push[0] <= row < push[1] else 0.0)
            table["gait_frequency"].append(2.85)
            table["gait_phase"].append((row * 0.057) % 1.0)
            for index, foot in enumerate(sources.FEET):
                table[f"{foot}_foot_contact"].append(float((row + index) % 2))
                table[f"{foot}_foot_desired_contact"].append(0.49 if row % 2 else 0.51)
            for index, joint in enumerate(JOINTS):
                table[joint].append(float(row + index))
            if window:
                table["robot_trunk_wrench_window_open"].append(1.0 if 20 <= row < 30 else 0.0)
                table["robot_trunk_wrench_window_onset"].append(1.0 if row == 20 else 0.0)
            if latent_block:
                for i in range(16):
                    table[f"dynamics_encoder_{latent_block}_{i}"].append(row * 0.01 + i)
                table["cmd_lin_x"].append(1.2)
                table["cmd_lin_y"].append(0.0)
                table["cmd_ang_z"].append(0.0)
    for name in drop:
        del table[name]
    pq.write_table(pa.table(table), path)
    meta = {"run": "r", "checkpoint": checkpoint, "precision": "tf32", "control_dt_s": 0.02}
    if latent_block:
        block = meta_block or latent_block
        meta["latent_blocks"] = [{"node": "dynamics_encoder", "read_block": block,
                                  "blocks": [{"name": block, "width": 16, "kind": "emitted",
                                              "operation": None,
                                              "deterministic_counterpart": None}]}]
    path.with_suffix(".meta.json").write_text(json.dumps(meta))


def test_the_event_row_and_the_frame_it_maps_to(tmp_path):
    _write(tmp_path / "r.parquet")
    recording = sources.load_recording(tmp_path / "r.parquet", env_idx=0,
                                       event_column="clock_jump_fired")
    assert (recording.warmup, recording.rows, recording.event_row) == (4, 40, 20)
    assert recording.frame_of(20) == 16
    assert recording.dt == 0.02


def test_a_meta_without_the_control_period_is_refused(tmp_path):
    _write(tmp_path / "r.parquet")
    meta = json.loads((tmp_path / "r.meta.json").read_text())
    del meta["control_dt_s"]
    (tmp_path / "r.meta.json").write_text(json.dumps(meta))
    with pytest.raises(sources.SourceError, match="control_dt_s"):
        sources.load_recording(tmp_path / "r.parquet", env_idx=0, event_column=None)


def test_a_recording_without_warmup_maps_rows_to_frames_unchanged(tmp_path):
    _write(tmp_path / "r.parquet", warmup=0)
    recording = sources.load_recording(tmp_path / "r.parquet", 0, "clock_jump_fired")
    assert recording.frame_of(20) == 20


def test_desired_stance_is_the_smoothed_indicator_above_one_half(tmp_path):
    _write(tmp_path / "r.parquet")
    recording = sources.load_recording(tmp_path / "r.parquet", 0, "clock_jump_fired")
    assert recording.desired[:4, 0].tolist() == [True, False, True, False]
    assert recording.contact[:3].tolist() == [[False, True, False, True],
                                              [True, False, True, False],
                                              [False, True, False, True]]


def test_the_push_rows_are_half_open_and_the_targets_keep_joint_order(tmp_path):
    _write(tmp_path / "r.parquet")
    recording = sources.load_recording(tmp_path / "r.parquet", 0, "clock_jump_fired")
    assert recording.push_rows == (20, 24)
    assert recording.targets.shape == (40, 12)
    assert recording.targets[5].tolist() == [5.0 + i for i in range(12)]
    assert recording.frequency == 2.85


def test_only_the_asked_environment_is_read(tmp_path):
    _write(tmp_path / "r.parquet")
    with pytest.raises(SourceError, match="clock_jump_fired.*env 1"):
        sources.load_recording(tmp_path / "r.parquet", env_idx=1,
                               event_column="clock_jump_fired")


def test_a_missing_column_is_named(tmp_path):
    _write(tmp_path / "r.parquet", drop=("gait_phase",))
    with pytest.raises(SourceError, match="gait_phase"):
        sources.load_recording(tmp_path / "r.parquet", 0, "clock_jump_fired")


def test_no_event_column_means_no_event_row(tmp_path):
    _write(tmp_path / "r.parquet")
    assert sources.load_recording(tmp_path / "r.parquet", 0, None).event_row is None


def test_the_latest_recording_is_picked_and_a_missing_one_is_named(tmp_path):
    task = tmp_path / "runA" / "evaluations" / "video_trot"
    task.mkdir(parents=True)
    (task / "evaluation_data_260921_104421.parquet").touch()
    (task / "evaluation_data_260921_113005.parquet").touch()
    assert sources.recording_path(tmp_path, "runA", "video_trot").name == \
        "evaluation_data_260921_113005.parquet"
    with pytest.raises(SourceError, match="video_walk"):
        sources.recording_path(tmp_path, "runA", "video_walk")


def test_a_clip_and_recording_that_do_not_belong_together_are_refused(tmp_path):
    _write(tmp_path / "evaluation_data_260921_104421.parquet")
    recording = sources.load_recording(tmp_path / "evaluation_data_260921_104421.parquet",
                                       0, "clock_jump_fired")
    clip = tmp_path / "video_trot-step-0.mp4"
    clip.touch()
    with pytest.raises(SourceError, match="35 frames"):
        sources.check_pair(clip, tmp_path / "evaluation_data_260921_104421.parquet",
                           recording, n_frames=34)


def test_a_checkpoint_tag_enters_both_paths(tmp_path):
    (tmp_path / "r/evaluations/videos/evaluation").mkdir(parents=True)
    (tmp_path / "r/evaluations/videos/evaluation/video_walk-7250-step-0.mp4").touch()
    (tmp_path / "r/evaluations/video_walk/7250").mkdir(parents=True)
    (tmp_path / "r/evaluations/video_walk/7250/evaluation_data_261018_120000.parquet").touch()
    assert sources.clip_path(tmp_path, "r", "video_walk", "7250").name == "video_walk-7250-step-0.mp4"
    assert sources.recording_path(tmp_path, "r", "video_walk", "7250").parent.name == "7250"
    with pytest.raises(SourceError):
        sources.clip_path(tmp_path, "r", "video_walk")


def test_the_window_open_column_gives_the_push_band(tmp_path):
    _write(tmp_path / "r.parquet", window=True, drop=("push_applied",))   # window open rows 20..29
    recording = sources.load_recording(tmp_path / "r.parquet", 0, "robot_trunk_wrench_window_onset")
    assert recording.event_row == 20 and recording.push_rows == (20, 30)


def test_the_latent_block_is_read_from_the_meta(tmp_path):
    _write(tmp_path / "r.parquet", latent_block="mean")
    recording = sources.load_recording(tmp_path / "r.parquet", 0, None, latent=True)
    assert recording.block == "mean" and recording.latent.shape == (40, 16)
    assert recording.commands[0].tolist() == [1.2, 0.0, 0.0]


def test_a_block_the_recording_lacks_fails_loud(tmp_path):
    _write(tmp_path / "r.parquet", latent_block="mean", meta_block="latent")   # meta names a block the columns do not carry
    with pytest.raises(SourceError, match="dynamics_encoder_latent"):
        sources.load_recording(tmp_path / "r.parquet", 0, None, latent=True)


def test_a_recording_with_respawns_still_pairs_by_row_count(tmp_path):
    _write(tmp_path / "r.parquet", episodes=3, warmup=0)
    recording = sources.load_recording(tmp_path / "r.parquet", 0, None)
    assert recording.rows == 40 and recording.frame_of(39) == 39
