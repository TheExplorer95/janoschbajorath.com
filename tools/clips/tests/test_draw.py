import numpy as np
from PIL import Image

import draw


def _canvas(size=(960, 300)):
    return Image.new("RGB", size, (80, 80, 80))


def _changed(image, box):
    pixels = np.asarray(image)[box[1]:box[3], box[0]:box[2]]
    return bool((pixels != 80).any())


def test_a_row_maps_linearly_onto_the_track():
    assert draw.row_to_x(100, (100, 300), 40, 440) == 40
    assert draw.row_to_x(200, (100, 300), 40, 440) == 240
    assert draw.row_to_x(300, (100, 300), 40, 440) == 440


def test_the_label_plate_draws_inside_the_tile_and_a_tile_without_title_gets_none():
    image = _canvas()
    draw.label_plate(image, (0, 0), 960, "Trot · 1.2 m/s", "commanded", "aux")
    assert _changed(image, (0, 0, 480, 150))
    assert not _changed(image, (0, 200, 960, 300))
    blank = _canvas()
    draw.label_plate(blank, (0, 0), 960, "", "", None)
    assert not _changed(blank, (0, 0, 960, 300))


def test_the_footfall_strip_fills_contact_only_where_the_foot_is_down():
    image = _canvas((960, 96))
    contact = np.zeros((200, 4), dtype=bool)
    contact[100:140, 0] = True                     # FL down for rows 100..139
    desired = np.zeros((200, 4), dtype=bool)
    draw.footfall_strip(image, (0, 0, 960, 96), contact, desired, center_row=100)
    pixels = np.asarray(image).astype(int)
    left, right = pixels[6:20, 100:400], pixels[6:20, 620:900]   # FL row, before / after
    assert right.mean() > left.mean() + 60         # bright bar only to the right of centre
    assert np.abs(pixels[30:90, 620:900].mean() - pixels[30:90, 100:400].mean()) < 5


def test_the_timeline_marks_the_event_and_the_push_band():
    image = _canvas((1920, 88))
    draw.timeline(image, (0, 0, 1920, 88), rows=(146, 326), playhead_row=200, event_row=176,
                  tick_label="substitution on", band_rows=(176, 186), slow=True)
    pixels = np.asarray(image).astype(int)
    red = (pixels[..., 0] > 180) & (pixels[..., 1] < 120)
    columns = np.flatnonzero(red.any(axis=0))
    event_x = draw.row_to_x(176, (146, 326), 160, 1760)
    assert abs(columns.min() - event_x) <= 6
    assert columns.max() >= draw.row_to_x(186, (146, 326), 160, 1760) - 6


def test_the_trace_stays_inside_its_box_and_survives_nan():
    image = _canvas((960, 120))
    values = np.full(400, np.nan)
    values[100:400] = 1.0
    values[200:210] = 9.0
    draw.trace(image, (0, 0, 960, 120), values, rows=(126, 326), playhead_row=200, event_row=176)
    assert _changed(image, (0, 0, 960, 120))
