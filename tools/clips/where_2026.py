"""The five clips of the WHERE 2026 page. Wording and timing are edited here only."""

from spec import Clip, Geometry, Segment, Tile

RUNS = {
    "aux": "dynamics-contacts/26-09-15_01-18-50_dynamics-contacts",
    "ppo": "rl-only/26-09-15_12-58-26_rl-only",
}

FULL = Geometry(crop=(1920, 1080), tile=(1920, 1080), rows=1, cols=1)

CAPABILITIES = Clip(
    name="capabilities",
    tiles=(Tile("aux", "video_capabilities", "Recovery from random initial orientations",
                "40 robots, each tracking its own velocity command",
                "aux", None),),
    geometry=FULL, anchor="raw", event_column=None,
    segments=(Segment(0.06, 9.98, False),),
    tick_label=None, push_band=False, still_s=8.0)


def _gait(task: str, name: str, speed: str) -> Tile:
    return Tile("aux", task, f"{name} · {speed} m/s", "commanded · {f} Hz stride", None, None)


GAITS = Clip(
    name="gaits",
    tiles=(_gait("video_stand", "Stand", "0"), _gait("video_walk", "Walk", "0.35"),
           _gait("video_trot", "Trot", "1.2"), _gait("video_bound", "Bound", "2.1")),
    geometry=Geometry(crop=(960, 540), tile=(960, 540), rows=2, cols=2, strip_h=96),
    anchor="raw", event_column=None,
    segments=(Segment(4.0, 7.0, False), Segment(4.0, 7.0, True)),
    tick_label=None, push_band=False, still_s=5.0)

DOMAIN = Clip(
    name="domain",
    tiles=(Tile("aux", "video_domain", "Trot · 1.2 m/s commanded",
                "one command, eight bodies from the trained domain randomisation", "aux",
                None),),
    geometry=FULL, anchor="raw", event_column=None,
    segments=(Segment(0.52, 8.0, False),),
    tick_label=None, push_band=False, still_s=3.0)

JUMP = Clip(
    name="jump",
    tiles=tuple(Tile(run, "video_jump_advance-quarter", "Trot · 1.2 m/s",
                     "clock advanced by a quarter cycle", run, None)
                for run in ("aux", "ppo")),
    geometry=Geometry(crop=(1280, 720), tile=(960, 540), rows=1, cols=2,
                      trace_h=120, strip_h=96, timeline_h=88),
    anchor="event", event_column="clock_jump_fired",
    segments=(Segment(-1.0, -0.2, False), Segment(-0.2, 1.4, True), Segment(1.4, 3.0, False)),
    tick_label="clock +¼ cycle", push_band=False, still_s=0.2)

_PUSH_COLUMNS = (
    ("video_push_m100_identity", "whole deviation · 100 N"),
    ("video_push_m100_trailing", "components 9–16 · 100 N"),
    ("video_push_m100_leading", "components 1–8 · 100 N"),
    ("video_push_m0_blind", "none · 0 N"),
)

PUSH = Clip(
    name="push",
    tiles=tuple(Tile(run, task, "", "", run if column == 0 else None, header)
                for run in ("aux", "ppo")
                for column, (task, header) in enumerate(_PUSH_COLUMNS)),
    geometry=Geometry(crop=(864, 720), tile=(480, 400), rows=2, cols=4,
                      header_h=64, timeline_h=88),
    anchor="event", event_column="push_fired",
    segments=(Segment(-0.6, 0.0, False), Segment(0.0, 1.2, True), Segment(1.2, 3.0, False)),
    tick_label="substitution on", push_band=True, still_s=0.6)

CLIPS = {clip.name: clip for clip in (CAPABILITIES, GAITS, DOMAIN, JUMP, PUSH)}
