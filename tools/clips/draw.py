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
ENCODERS = {"ppo": ("PPO", (127, 216, 130)), "aux": ("RECON + BCE", (192, 139, 224))}
TRACK_MARGIN = 160


@lru_cache(maxsize=None)
def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = _FONT_DIR / f"fira-sans-latin-{600 if bold else 400}-normal.woff2"
    if not path.is_file():
        raise FileNotFoundError(f"Fira Sans not found at {path}; run `npm install` first.")
    return ImageFont.truetype(str(path), size)


def row_to_x(row: float, rows: tuple[int, int], x0: float, x1: float) -> float:
    return x0 + (row - rows[0]) / (rows[1] - rows[0]) * (x1 - x0)


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
        name, colour = ENCODERS[encoder]
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
    points = [(row_to_x(row, rows, x0 + gutter, x1),
               bottom - (min(values[row], ceiling) / ceiling) * (bottom - top))
              for row in range(rows[0], rows[1]) if np.isfinite(values[row])]
    if len(points) > 1:
        pen.line(points, fill=WHITE, width=3, joint="curve")
    xe = row_to_x(event_row, rows, x0 + gutter, x1)
    pen.line((xe, top, xe, y1), fill=RED, width=3)             # below the caption
    xp = row_to_x(playhead_row, rows, x0 + gutter, x1)
    pen.line((xp, top, xp, y1), fill=WHITE, width=2)


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
