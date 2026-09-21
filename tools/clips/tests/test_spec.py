import pytest

from spec import Clip, ClipSpecError, Geometry, Segment, Tile, frames

TILE = Tile(run="aux", task="video_trot", title="Trot", subtitle="", encoder=None, header=None)
FULL = Geometry(crop=(1920, 1080), tile=(1920, 1080), rows=1, cols=1)


def _clip(segments, anchor="event", event_column="clock_jump_fired", geometry=FULL, tiles=(TILE,)):
    return Clip(name="c", tiles=tiles, geometry=geometry, anchor=anchor,
                event_column=event_column, segments=segments, tick_label=None,
                push_band=False, still_s=0.0)


def test_seconds_convert_to_raw_frames_exactly():
    assert frames(2.88) == 144
    assert frames(-0.2) == -10


def test_a_time_off_the_frame_lattice_is_refused():
    with pytest.raises(ClipSpecError, match="0.205"):
        frames(0.205)


def test_the_jump_cut_is_accepted_and_reports_its_window():
    clip = _clip((Segment(-1.0, -0.2, False), Segment(-0.2, 1.4, True), Segment(1.4, 3.0, False)))
    assert clip.window == (-50, 150)


def test_a_normal_speed_segment_of_odd_length_is_refused():
    with pytest.raises(ClipSpecError, match="even"):
        _clip((Segment(-1.0, -0.22, False),))          # 39 frames


def test_a_normal_speed_segment_starting_an_odd_distance_from_the_event_is_refused():
    with pytest.raises(ClipSpecError, match="even"):
        _clip((Segment(-0.98, -0.02, False),))         # starts at -49


def test_a_raw_cut_is_measured_from_its_own_first_frame_and_may_not_start_before_frame_three():
    assert _clip((Segment(0.06, 9.98, False),), anchor="raw", event_column=None).window == (3, 499)
    with pytest.raises(ClipSpecError, match="frame 3"):
        _clip((Segment(0.0, 9.96, False),), anchor="raw", event_column=None)


def test_an_event_cut_without_an_event_column_is_refused():
    with pytest.raises(ClipSpecError, match="event_column"):
        _clip((Segment(-1.0, 3.0, False),), event_column=None)


def test_geometry_reports_the_output_size_and_refuses_odd_sizes():
    push = Geometry(crop=(864, 720), tile=(480, 400), rows=2, cols=4, header_h=64, timeline_h=88)
    assert push.size == (1920, 952)
    jump = Geometry(crop=(1280, 720), tile=(960, 540), rows=1, cols=2,
                    trace_h=120, strip_h=96, timeline_h=88)
    assert jump.size == (1920, 844)
    with pytest.raises(ClipSpecError, match="even"):
        Geometry(crop=(864, 720), tile=(480, 401), rows=2, cols=4)


def test_the_tile_count_must_fill_the_grid():
    grid = Geometry(crop=(960, 540), tile=(960, 540), rows=2, cols=2, strip_h=96)
    with pytest.raises(ClipSpecError, match="4 tiles"):
        _clip((Segment(4.0, 7.0, False),), anchor="raw", event_column=None,
              geometry=grid, tiles=(TILE,))
