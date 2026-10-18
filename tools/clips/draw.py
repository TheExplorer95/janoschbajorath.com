"""Burned-in overlays. Every function draws into a box of an RGB image and nothing else."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from sources import FEET

_FONT_DIR = Path(__file__).resolve().parents[2] / "node_modules/@fontsource/fira-sans/files"
WHITE = (255, 255, 255)
MUTED = (200, 204, 200)
BAND = (24, 26, 24)
RED = (224, 84, 63)
CONDITIONS = {"ppo": ("PPO", (127, 216, 130)), "aux": ("+ AUX", (192, 139, 224)),
              "cur": ("+ Curriculum", (95, 196, 200))}
GAIT_COLOURS = {"stand": (104, 121, 135), "walk": (55, 145, 212), "trot": (202, 119, 47),
                "bound": (222, 95, 150)}
"""The poster legend's hues: the mid-ramp swatches of the poster's `GAIT_RAMPS`."""
AXIS = (90, 94, 90)
TRACK_MARGIN = 160


@lru_cache(maxsize=None)
def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = _FONT_DIR / f"fira-sans-latin-{600 if bold else 400}-normal.woff2"
    if not path.is_file():
        raise FileNotFoundError(f"Fira Sans not found at {path}; run `npm install` first.")
    return ImageFont.truetype(str(path), size)


def row_to_x(row: float, rows: tuple[int, int], x0: float, x1: float) -> float:
    return x0 + (row - rows[0]) / (rows[1] - rows[0]) * (x1 - x0)


def _runs(points: np.ndarray) -> list[list[tuple[float, float]]]:
    """The finite stretches of an `(n, 2)` pixel path: a NaN breaks the line."""
    finite = np.isfinite(points).all(axis=1)
    padded = np.concatenate([[False], finite, [False]])
    edges = np.flatnonzero(padded[1:] != padded[:-1])
    return [[tuple(map(float, q)) for q in points[a:b]] for a, b in zip(edges[::2], edges[1::2])]


def _polyline(pen: ImageDraw.ImageDraw, points: np.ndarray, fill, width: int) -> None:
    """A line through the finite stretches of `points`, broken at every NaN."""
    for run in _runs(points):
        if len(run) > 1:
            pen.line(run, fill=fill, width=width, joint="curve")


def _dotted(pen: ImageDraw.ImageDraw, points: np.ndarray, fill, radius: float,
            spacing: float) -> None:
    """Dots every `spacing` pixels along the finite stretches of `points`."""
    for run in _runs(points):
        if len(run) < 2:
            continue
        path = np.asarray(run)
        steps = np.hypot(*(path[1:] - path[:-1]).T)
        along = np.concatenate([[0.0], np.cumsum(steps)])
        for distance in np.arange(0.0, along[-1] + 1e-9, spacing):
            x = np.interp(distance, along, path[:, 0])
            y = np.interp(distance, along, path[:, 1])
            pen.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)


def _composite(image: Image.Image, box: tuple[int, int, int, int], layer: Image.Image) -> None:
    """Alpha-composite a box-sized RGBA `layer` onto the box of `image`; it clips there."""
    x0, y0 = int(box[0]), int(box[1])
    crop = image.crop((x0, y0, x0 + layer.width, y0 + layer.height)).convert("RGBA")
    image.paste(Image.alpha_composite(crop, layer).convert("RGB"), (x0, y0))


def _sizes(tile_w: int) -> tuple[int, int]:
    if tile_w >= 1900:
        return 46, 32
    if tile_w >= 900:
        return 34, 25
    return 24, 19


def label_plate(image: Image.Image, origin: tuple[int, int], tile_w: int, title: str,
                subtitle: str, encoder: str | None) -> None:
    """Top-left label of a tile on a semi-opaque plate; the ground is mid-grey."""
    lines: list[tuple[str, ImageFont.FreeTypeFont, tuple[int, int, int]]] = []
    big, small = _sizes(tile_w)
    if title:
        lines.append((title, font(big, bold=True), WHITE))
    if subtitle:
        lines.append((subtitle, font(small), MUTED))
    if encoder:
        name, colour = CONDITIONS[encoder]
        lines.append((name, font(small, bold=True), colour))
    if not lines:
        return
    pad = big // 3
    widths = [f.getlength(text) for text, f, _ in lines]
    heights = [f.size * 1.25 for _, f, _ in lines]
    x, y = origin[0] + pad, origin[1] + pad
    plate = (x, y, x + max(widths) + 2 * pad, y + sum(heights) + 2 * pad)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rounded_rectangle(plate, radius=pad // 2, fill=(0, 0, 0, 150))
    image.paste(Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB"))
    pen = ImageDraw.Draw(image)
    cursor = y + pad
    for (text, f, colour), height in zip(lines, heights):
        pen.text((x + pad, cursor), text, font=f, fill=colour)
        cursor += height


def slow_tag(image: Image.Image, right: int, top: int) -> None:
    """The slow-motion tag of a clip that has no timeline to carry it, top-right."""
    f = font(34, bold=True)
    width, pad = f.getlength("0.5×"), 11
    box = (right - 3 * pad - width, top + pad, right - pad, top + 3 * pad + f.size * 1.25)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rounded_rectangle(box, radius=5, fill=(0, 0, 0, 150))
    image.paste(Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB"))
    ImageDraw.Draw(image).text((box[0] + pad, box[1] + pad), "0.5×", font=f, fill=RED)


def column_header(image: Image.Image, box: tuple[int, int, int, int], text: str) -> None:
    pen = ImageDraw.Draw(image)
    pen.rectangle(box, fill=BAND)
    f = font(26, bold=True)
    pen.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), text, font=f, fill=WHITE,
             anchor="mm")


def footfall_strip(image: Image.Image, box: tuple[int, int, int, int], contact: np.ndarray,
                   desired: np.ndarray, center_row: float, event_row: int | None = None,
                   window_rows: int = 75) -> None:
    """Four rows (FL, FR, RL, RR), `window_rows` of source time centred on `center_row`:
    filled where the foot is down, outlined where the clock wants it down."""
    pen = ImageDraw.Draw(image)
    pen.rectangle(box, fill=BAND)
    x0, y0, x1, y1 = box
    gutter = 44
    rows = (center_row - window_rows / 2, center_row + window_rows / 2)
    lane = (y1 - y0 - 8) / len(FEET)
    lo = max(0, int(np.floor(rows[0])))
    hi = min(len(contact), int(np.ceil(rows[1])))

    def spans(flags: np.ndarray):
        padded = np.concatenate([[False], flags[lo:hi], [False]])
        edges = np.flatnonzero(padded[1:] != padded[:-1])
        return [(lo + a, lo + b) for a, b in zip(edges[::2], edges[1::2])]

    for index, foot in enumerate(FEET):
        top = y0 + 4 + index * lane
        pen.text((x0 + 8, top + lane / 2), foot, font=font(17), fill=MUTED, anchor="lm")
        for a, b in spans(contact[:, index]):
            xa = max(x0 + gutter, row_to_x(a, rows, x0 + gutter, x1))
            xb = min(x1, row_to_x(b, rows, x0 + gutter, x1))
            if xb > xa:
                pen.rectangle((xa, top + 5, xb, top + lane - 5), fill=(235, 238, 235))
        for a, b in spans(desired[:, index]):
            xa = max(x0 + gutter, row_to_x(a, rows, x0 + gutter, x1))
            xb = min(x1, row_to_x(b, rows, x0 + gutter, x1))
            if xb > xa:
                pen.rectangle((xa, top + 2, xb, top + lane - 2), outline=(150, 156, 150),
                              width=2)
    if event_row is not None and rows[0] <= event_row <= rows[1]:
        xe = row_to_x(event_row, rows, x0 + gutter, x1)
        pen.line((xe, y0, xe, y1), fill=RED, width=3)
    xc = row_to_x(center_row, rows, x0 + gutter, x1)
    pen.line((xc, y0, xc, y1), fill=WHITE, width=2)


def trace(image: Image.Image, box: tuple[int, int, int, int], values: np.ndarray,
          rows: tuple[int, int], playhead_row: float, event_row: int) -> None:
    """The deviation trace over the whole cut, with a playhead and the event line."""
    pen = ImageDraw.Draw(image)
    pen.rectangle(box, fill=BAND)
    x0, y0, x1, y1 = box
    gutter, top, bottom = 44, y0 + 26, y1 - 8
    window = values[rows[0]:rows[1]]
    ceiling = max(2.0, float(np.nanmax(window)))
    pen.text((x0 + gutter, y0 + 4), "joint targets · distance from the steady cycle",
             font=font(17), fill=MUTED)
    baseline = bottom - (1.0 / ceiling) * (bottom - top)
    pen.line((x0 + gutter, baseline, x1, baseline), fill=(90, 94, 90), width=1)
    _polyline(pen, _trace_path(window, rows, ceiling, x0 + gutter, x1, top, bottom), WHITE, 3)
    _trace_marks(pen, rows, playhead_row, event_row, x0 + gutter, x1, top, y1)


def _trace_path(values: np.ndarray, rows: tuple[int, int], ceiling: float, left: float,
                right: float, top: float, bottom: float) -> np.ndarray:
    """Pixel path of `values` (one per row of the window), clipped to `ceiling`; NaN stays."""
    xs = row_to_x(np.arange(rows[0], rows[1]), rows, left, right)
    ys = bottom - (np.minimum(values, ceiling) / ceiling) * (bottom - top)
    return np.column_stack([xs, ys])


def _trace_marks(pen: ImageDraw.ImageDraw, rows: tuple[int, int], playhead_row: float,
                 event_row: int, left: float, right: float, top: float, bottom: float) -> None:
    """The event line and the playhead of a trace, below its caption."""
    xe = row_to_x(event_row, rows, left, right)
    pen.line((xe, top, xe, bottom), fill=RED, width=3)
    xp = row_to_x(playhead_row, rows, left, right)
    pen.line((xp, top, xp, bottom), fill=WHITE, width=2)


def deviation_trace(image: Image.Image, box: tuple[int, int, int, int],
                    lines: dict[str, np.ndarray], rows: tuple[int, int], playhead_row: float,
                    event_row: int, ceiling: float, colour: tuple[int, int, int],
                    seconds_per_row: float, y_label: str | None) -> None:
    """The latent deviation over the cut as a plot: its behaviour part in `colour`, its
    domain part in white, and the raw value dotted in the muted tone wherever the drawn line
    departs from it. The y-axis runs from 0 to `ceiling` without tick labels (the values
    are not the point, the course is); the x-axis counts seconds from `event_row`, ticked
    at every whole second of the window. A legend row above the plot names the three line
    styles. `y_label`, when given, is the y-axis title; the first column of a row carries
    it, the others leave the gutter empty."""
    pen = ImageDraw.Draw(image)
    pen.rectangle(box, fill=BAND)
    x0, y0, x1, y1 = box
    small = font(15)
    gutter, legend_h, foot = 30, 24, 46
    left, right = x0 + gutter, x1 - 10
    top, bottom = y0 + legend_h + 6, y1 - foot

    x, y = left, y0 + legend_h / 2
    for text, fill, dotted in (("behaviour", colour, False), ("domain", WHITE, False),
                               ("removed by mask", MUTED, True)):
        sample = np.array([[x, y], [x + 24, y]], dtype=float)
        if dotted:
            _dotted(pen, sample, fill, 1.5, 7.0)
        else:
            _polyline(pen, sample, fill, 3)
        pen.text((x + 30, y), text, font=small, fill=fill, anchor="lm")
        x += 30 + small.getlength(text) + 18

    pen.line((left, top, left, bottom, right, bottom), fill=AXIS, width=1)
    first = int(np.ceil((rows[0] - event_row) * seconds_per_row))
    last = int(np.floor((rows[1] - event_row) * seconds_per_row))
    for second in range(first, last + 1):
        x = row_to_x(event_row + second / seconds_per_row, rows, left, right)
        pen.line((x, bottom, x, bottom + 4), fill=AXIS, width=1)
        pen.text((x, bottom + 7), str(second), font=small, fill=MUTED, anchor="ma")
    pen.text(((left + right) / 2, y1 - 4), "time (s)", font=small, fill=MUTED, anchor="md")
    if y_label:
        _rotated_text(image, (x0 + 12, (top + bottom) / 2), y_label, small, MUTED)

    def path(key: str) -> np.ndarray:
        values = np.asarray(lines[key], dtype=float)[rows[0]:rows[1]]
        return _trace_path(values, rows, ceiling, left, right, top, bottom)

    for key, fill in (("domain", WHITE), ("behaviour", colour)):   # the condition's on top
        solid, raw = path(key), path(f"{key}_raw")
        same = np.isclose(solid[:, 1], raw[:, 1]) | (np.isnan(solid[:, 1]) & np.isnan(raw[:, 1]))
        raw[same, 1] = np.nan
        _dotted(pen, raw, MUTED, 1.5, 7.0)
        _polyline(pen, solid, fill, 3)
    _trace_marks(pen, rows, playhead_row, event_row, left, right, top, bottom)


def _rotated_text(image: Image.Image, centre: tuple[float, float], text: str,
                  f: ImageFont.FreeTypeFont, fill: tuple[int, int, int]) -> None:
    """`text` read bottom-to-top, centred on `centre`."""
    width, height = int(f.getlength(text)) + 4, int(f.size * 1.3)
    tile = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((2, 0), text, font=f, fill=fill)
    tile = tile.rotate(90, expand=True)
    image.paste(tile, (int(centre[0] - tile.width / 2), int(centre[1] - tile.height / 2)), tile)


def latent_panel(image: Image.Image, box: tuple[int, int, int, int],
                 rings: dict[str, np.ndarray], trail: np.ndarray, point: np.ndarray | None,
                 limits: tuple[float, float, float, float], colour: tuple[int, int, int],
                 axis_labels: tuple[str, str]) -> None:
    """The live latent on two principal components: the gaits' rings faint behind, the tile's
    trail fading in from the band, the point filled in `colour` under a thin white ring.
    `limits = (x_min, x_max, y_min, y_max)` fill the plot area less a small padding; y up."""
    pen = ImageDraw.Draw(image)
    pen.rectangle(box, fill=BAND)
    x0, y0, x1, y1 = box
    gutter, edge = 28, 6
    plot = (x0 + gutter, y0 + edge, x1 - edge, y1 - gutter)
    pen.line((plot[0], plot[1], plot[0], plot[3], plot[2], plot[3]), fill=AXIS, width=1)
    pen.text(((plot[0] + plot[2]) / 2, y1 - gutter / 2), axis_labels[0], font=font(17),
             fill=MUTED, anchor="mm")
    _rotated_text(image, (x0 + gutter / 2, (plot[1] + plot[3]) / 2), axis_labels[1], font(17),
                  MUTED)
    pad = 0.08 * min(plot[2] - plot[0], plot[3] - plot[1])
    inner = (plot[0] + pad - x0, plot[1] + pad - y0, plot[2] - pad - x0, plot[3] - pad - y0)
    x_min, x_max, y_min, y_max = limits

    def to_pixels(data: np.ndarray) -> np.ndarray:
        data = np.asarray(data, dtype=float).reshape(-1, 2)
        xs = inner[0] + (data[:, 0] - x_min) / (x_max - x_min) * (inner[2] - inner[0])
        ys = inner[3] - (data[:, 1] - y_min) / (y_max - y_min) * (inner[3] - inner[1])
        return np.column_stack([xs, ys])

    radius = max(4, round(min(x1 - x0, y1 - y0) / 70))
    layer = Image.new("RGBA", (int(x1 - x0), int(y1 - y0)), (0, 0, 0, 0))
    brush = ImageDraw.Draw(layer)
    faint = round(0.35 * 255)
    for key, ring in rings.items():
        path = to_pixels(ring)
        if len(path) == 1:
            x, y = path[0]
            brush.ellipse((x - radius, y - radius, x + radius, y + radius),
                          fill=GAIT_COLOURS[key] + (faint,))
        else:
            _polyline(brush, path, GAIT_COLOURS[key] + (faint,), 2)
    path = to_pixels(trail)
    for index, run in enumerate(zip(path[:-1], path[1:])):
        if np.isfinite(run).all():
            alpha = round(255 * (index + 1) / (len(path) - 1))
            brush.line([tuple(run[0]), tuple(run[1])], fill=colour + (alpha,), width=3)
    if point is not None and np.isfinite(point).all():
        x, y = to_pixels(point)[0]
        brush.ellipse((x - radius - 1, y - radius - 1, x + radius + 1, y + radius + 1),
                      fill=WHITE + (255,))
        brush.ellipse((x - radius + 1, y - radius + 1, x + radius - 1, y + radius - 1),
                      fill=colour + (255,))
    _composite(image, box, layer)


def timeline(image: Image.Image, box: tuple[int, int, int, int], rows: tuple[int, int],
             playhead_row: float, event_row: int, tick_label: str | None,
             band_rows: tuple[int, int] | None, slow: bool) -> None:
    """A track over the cut, linear in source time: push band, event tick, playhead and
    the slow-motion tag."""
    pen = ImageDraw.Draw(image)
    pen.rectangle(box, fill=BAND)
    x0, y0, x1, y1 = box
    left, right, y = x0 + TRACK_MARGIN, x1 - TRACK_MARGIN, y0 + (y1 - y0) * 0.62
    pen.line((left, y, right, y), fill=(120, 124, 120), width=6)
    xp = row_to_x(playhead_row, rows, left, right)
    pen.line((left, y, xp, y), fill=WHITE, width=6)            # under the band and the tick
    if band_rows is not None:
        pen.rectangle((row_to_x(band_rows[0], rows, left, right), y - 9,
                       row_to_x(band_rows[1], rows, left, right), y + 9), fill=RED)
    xe = row_to_x(event_row, rows, left, right)
    pen.line((xe, y - 20, xe, y + 20), fill=RED, width=5)
    if tick_label:
        pen.text((xe + 12, y0 + 6), tick_label, font=font(24, bold=True), fill=RED)
    pen.ellipse((xp - 10, y - 10, xp + 10, y + 10), fill=WHITE)
    if slow:
        pen.text((x1 - 24, y0 + (y1 - y0) / 2), "0.5×", font=font(28, bold=True), fill=RED,
                 anchor="rm")
