from schedule import Shot, build
from spec import Segment


def test_normal_speed_shows_every_second_frame_and_slow_motion_every_frame():
    shots = build((Segment(-0.08, 0.0, False), Segment(0.0, 0.06, True), Segment(0.06, 0.14, False)))
    assert [s.offset for s in shots] == [-4, -2, 0, 1, 2, 3, 5]
    assert [s.slow for s in shots] == [False, False, True, True, True, False, False]


def test_a_window_is_half_open():
    assert [s.offset for s in build((Segment(0.0, 0.04, True),))] == [0, 1]


def test_the_event_frame_is_shown_when_the_event_lies_inside_a_normal_speed_segment():
    assert Shot(0, False) in build((Segment(-0.04, 0.04, False),))


def test_a_repeated_window_is_shown_twice_in_order():
    shots = build((Segment(4.0, 4.04, False), Segment(4.0, 4.04, True)))
    assert [s.offset for s in shots] == [200, 200, 201]
