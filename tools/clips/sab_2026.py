"""The clips of the SAB 2026 page. Wording and timing are edited here only.

Three entries: `gaits` with the latent panel, `push` with the deviation trace, `intro` the
field of robots. The panel's rings are each tile's own recorded cycle; the trace is in
units of the group's nominal-cycle amplitude; both were chosen over their alternatives on
the rendered clips."""

from pathlib import Path

from spec import Clip, Geometry, Segment, Tile

ROOT = Path.home() / "code/gait_rl/experiment/sab_rev"
"""Where the three runs live; `render.py --root` overrides it."""

CHECKPOINT = "7250"
"""Checkpoint tag in every clip and recording path of this page."""

RUNS = {
    "ppo": "rl-only/26-10-12_16-04-32_rl-only",
    "aux": "proprio-encoder_contacts/26-10-15_09-29-51_proprio-encoder_contacts",
    "cur": ("proprio-encoder_contacts_curriculum/"
            "26-10-12_21-26-43_proprio-encoder_contacts_curriculum"),
}

LEADING = {"ppo": 5, "aux": 7, "cur": 2}
"""Behaviour components per run: the leading components of each basis, as the poster states."""

FULL = Geometry(crop=(1920, 1080), tile=(1920, 1080), rows=1, cols=1)


def _gait(task: str, name: str, speed: str) -> Tile:
    return Tile("cur", task, f"{name} · {speed} m/s commanded", "", "cur", None)


GAITS = Clip(
    name="gaits",
    tiles=(_gait("video_stand", "Stand", "0"), _gait("video_walk", "Walk", "0.35"),
           _gait("video_trot", "Trot", "1.2"), _gait("video_bound", "Bound", "2.1")),
    geometry=Geometry(crop=(960, 540), tile=(640, 360), rows=2, cols=2, strip_h=96,
                      side_w=456),
    anchor="raw", event_column=None,
    segments=(Segment(4.0, 7.0, False), Segment(4.0, 7.0, True)),
    tick_label=None, push_band=False, still_s=5.0)

_PUSH_COLUMNS = (
    ("video_mask_identity_m100", "No Mask · 100 N", "identity"),
    ("video_mask_trailing_m100", "Behavior Mask · 100 N", "trailing"),
    ("video_mask_leading_m0", "Domain Mask · 0 N", "leading"),
    ("video_mask_blind_m0", "Full Mask · 0 N", "blind"),
)

PUSH = Clip(
    name="push",
    tiles=tuple(Tile(run, task, "", "", run if column == 0 else None, header, mask)
                for run in ("ppo", "aux", "cur")
                for column, (task, header, mask) in enumerate(_PUSH_COLUMNS)),
    geometry=Geometry(crop=(864, 720), tile=(480, 400), rows=3, cols=4,
                      header_h=64, trace_h=160, timeline_h=88),
    anchor="event", event_column="robot_trunk_wrench_window_onset",
    segments=(Segment(-0.6, 0.0, False), Segment(0.0, 1.2, True), Segment(1.2, 4.0, False)),
    tick_label="substitution on", push_band=True, still_s=0.6, trace="latent")

INTRO = Clip(
    name="intro",
    tiles=(Tile("cur", "video_intro", "Locomotion Diversity", "", "cur", None),),
    geometry=FULL, anchor="raw", event_column=None,
    segments=(Segment(0.06, 11.98, False),),
    tick_label=None, push_band=False, still_s=4.0, max_bytes=6_000_000)
"""The field of 384 robots does not fit the page's 5 MB at any readable CRF (5.36 MB at
CRF 32 for 12 s); Janosch allowed the size over a shorter cut on 2026-10-18."""

CLIPS = {clip.name: clip for clip in (GAITS, PUSH, INTRO)}
