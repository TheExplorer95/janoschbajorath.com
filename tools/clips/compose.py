"""One clip entry -> video, still and manifest entry."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import imageio.v3 as iio
import imageio_ffmpeg
import numpy as np
from PIL import Image

import draw
import latent
import schedule
import signals
import sources
from spec import FPS_OUT, RAW_SIZE, SKIP_FRAMES, Clip, ClipSpecError, Tile, frames

TRACE_SETTLE_ROWS = 28
"""Rows after the warmup left out of the deviation trace's baseline (0.56 s)."""
TRAIL_ROWS = 30
"""Rows of source time the latent panel's trail covers (0.6 s)."""
CRF_STEP, MAX_CRF = 3, 32
"""A clip over its `max_bytes` at CRF 23 is re-encoded `CRF_STEP` higher until it fits;
past `MAX_CRF` it is refused rather than published unreadable."""
TRACE_Y_LABEL = "latent deviation"
"""Axis title of the latent trace, drawn on the first column of each row only."""


class _TileReader:
    """Serves raw frames of one clip by index, cropped and scaled, reading the file once in
    order and keeping only frames that are asked for again later."""

    def __init__(self, path: Path, indices: list[int], crop: tuple[int, int],
                 size: tuple[int, int]) -> None:
        self._pending = Counter(indices)
        self._kept: dict[int, Image.Image] = {}
        self._frames = imageio_ffmpeg.read_frames(str(path), pix_fmt="rgb24")
        next(self._frames)                                   # metadata
        self._position = -1
        left, top = (RAW_SIZE[0] - crop[0]) // 2, (RAW_SIZE[1] - crop[1]) // 2
        self._box = (left, top, left + crop[0], top + crop[1])
        self._size = size

    def get(self, index: int) -> Image.Image:
        while self._position < index:
            raw = next(self._frames)
            self._position += 1
            if self._pending.get(self._position):
                frame = Image.frombuffer("RGB", RAW_SIZE, raw, "raw", "RGB", 0, 1).crop(self._box)
                if frame.size != self._size:
                    frame = frame.resize(self._size, Image.LANCZOS)
                self._kept[self._position] = frame
        frame = self._kept[index]
        self._pending[index] -= 1
        if not self._pending[index]:
            del self._kept[index]
        return frame

    def close(self) -> None:
        self._frames.close()


def _encode(path: Path, size: tuple[int, int], frames, crf: int) -> None:
    writer = imageio_ffmpeg.write_frames(
        str(path), size, fps=FPS_OUT, codec="libx264", pix_fmt_in="rgb24",
        pix_fmt_out="yuv420p", macro_block_size=1,
        output_params=["-crf", str(crf), "-preset", "slow", "-movflags", "+faststart",
                       "-g", "50", "-an"])
    writer.send(None)
    for frame in frames:
        writer.send(np.asarray(frame).tobytes())
    writer.close()


# ---- the fixed ranges -------------------------------------------------------------

def trace_ceiling(values: list[np.ndarray], floor: float = 1.0) -> float:
    """The largest finite value over all arrays, rounded up to one decimal, at least
    `floor`; `floor` when nothing is finite."""
    finite = np.concatenate([np.asarray(v, dtype=float).ravel() for v in values])
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return floor
    return max(floor, math.ceil(round(float(finite.max()) * 10, 6)) / 10)


def panel_limits(rings: list[np.ndarray],
                 margin: float = 0.1) -> tuple[float, float, float, float]:
    """Square limits `(x_min, x_max, y_min, y_max)` over all rings: centred on their
    bounding box, as wide as its longer side, plus `margin` of the half-side each way."""
    points = np.concatenate([np.asarray(r, dtype=float).reshape(-1, 2) for r in rings])
    lo, hi = np.nanmin(points, axis=0), np.nanmax(points, axis=0)
    half = float((hi - lo).max()) / 2
    if not half > 0:
        raise ValueError("The rings have no extent; the panel cannot be scaled to them.")
    half *= 1 + margin
    cx, cy = (lo + hi) / 2
    return (float(cx - half), float(cx + half), float(cy - half), float(cy + half))


# ---- per-tile preparation ---------------------------------------------------------

@dataclass
class _Prepared:
    tile: Tile
    raw: Path
    anchor: int
    recording: sources.Recording | None
    recording_file: Path | None
    cut: tuple[int, int] | None             # the cut window in recording rows
    values: np.ndarray | None = None        # joint-target trace, per row
    lines: dict[str, np.ndarray] | None = None   # latent deviation trace, per row
    projected: np.ndarray | None = None     # (rows, 2): the latent on PC1 and PC2
    reference: latent.Reference | None = None
    rings: dict[str, np.ndarray] = field(default_factory=dict)


def _gait(task: str) -> str:
    gait = task.removeprefix("video_")
    if gait not in draw.GAIT_COLOURS:
        raise ClipSpecError(f"Task '{task}' names no gait of {list(draw.GAIT_COLOURS)}; the "
                            f"latent panel takes its colour and ring from the gait.")
    return gait


def _row_encoder(clip: Clip, position: int) -> str:
    """The condition of a tile's row: the tile's own, else the row's first tile's."""
    first = position - position % clip.geometry.cols
    encoder = clip.tiles[position].encoder or clip.tiles[first].encoder
    if encoder is None:
        raise ClipSpecError(f"Clip '{clip.name}': tile {position} has no condition in its "
                            f"row; the latent trace is drawn in the condition's colour.")
    return encoder


def _origin(clip: Clip, position: int) -> tuple[int, int]:
    geometry = clip.geometry
    row, col = divmod(position, geometry.cols)
    return (col * (geometry.tile[0] + geometry.side_w),
            geometry.header_h + row * geometry.cell_h)


def _prepare_tile(clip: Clip, position: int, runs: dict[str, str], root: Path,
                  checkpoint: str | None, leading: dict[str, int] | None) -> _Prepared:
    """Read one tile's sources and compute what its overlays draw from, over all rows."""
    geometry, tile = clip.geometry, clip.tiles[position]
    lo, hi = clip.window
    where = f"clip '{clip.name}', tile {position} ({tile.run}/{tile.task})"
    latent_trace = bool(geometry.trace_h) and clip.trace == "latent"
    wants_latent = bool(geometry.side_w) or latent_trace
    recording = recording_file = None
    try:
        raw = sources.clip_path(root, runs[tile.run], tile.task, checkpoint)
        n_frames = sources.frame_count(raw)
        if clip.needs_recording:
            recording_file = sources.recording_path(root, runs[tile.run], tile.task, checkpoint)
            recording = sources.load_recording(recording_file, clip.env_idx, clip.event_column,
                                               latent=wants_latent)
            sources.check_pair(raw, recording_file, recording, n_frames)
    except sources.SourceError as error:
        raise sources.SourceError(f"{where}: {error}") from error
    anchor = recording.frame_of(recording.event_row) if clip.anchor == "event" else 0
    if anchor + lo < SKIP_FRAMES or anchor + hi > n_frames:
        raise sources.SourceError(
            f"{where}: the cut spans raw frames {anchor + lo}..{anchor + hi}, outside "
            f"{SKIP_FRAMES}..{n_frames}.")
    if recording is None:
        return _Prepared(tile, raw, anchor, None, None, None)

    entry = _Prepared(tile, raw, anchor, recording, recording_file,
                      (anchor + lo + recording.warmup, anchor + hi + recording.warmup))
    if wants_latent:
        if leading is None or tile.run not in leading:
            raise ClipSpecError(f"{where}: no leading-component count for run '{tile.run}'.")
        entry.reference = latent.load_reference(root / runs[tile.run], recording_file,
                                                recording, leading[tile.run])
        entry.projected = latent.project(entry.reference, recording.latent)[:, :2]
    if geometry.trace_h and not latent_trace:
        entry.values = signals.deviation(recording.targets, recording.phase,
                                         recording.warmup + TRACE_SETTLE_ROWS,
                                         recording.event_row)
    if latent_trace:
        if tile.mask is None or recording.event_row is None:
            raise ClipSpecError(f"{where}: the latent trace needs the tile's mask and an "
                                f"event row.")
        entry.lines = latent.trace_lines(recording, entry.reference, tile.mask,
                                         recording.event_row)
    return entry


def _share_rings(clip: Clip, tiles: list[_Prepared]) -> None:
    """The latent panel's rings: every tile's cut window, projected, keyed by the tile's
    gait, and the one dict handed to every tile."""
    rings = {_gait(e.tile.task): e.projected[e.cut[0]:e.cut[1]] for e in tiles}
    for entry in tiles:
        entry.rings = rings


# ---- drawing ----------------------------------------------------------------------

def _row_ceiling(clip: Clip, tiles: list[_Prepared], position: int) -> float:
    """The latent trace's y-range of a tile's row: one ceiling over the row's cut windows,
    so the row's masks share a scale and each condition has its own."""
    cols = clip.geometry.cols
    first = position - position % cols
    return trace_ceiling([line[e.cut[0]:e.cut[1]]
                          for e in tiles[first:first + cols] for line in e.lines.values()])


def _draw_overlays(canvas: Image.Image, clip: Clip, entry: _Prepared, position: int,
                   offset: int, limits: tuple[float, float, float, float] | None,
                   ceiling: float | None) -> None:
    """Everything of one tile but the frame: plate, header, side panel, trace, strip."""
    geometry = clip.geometry
    tile_w, tile_h = geometry.tile
    x, y = _origin(clip, position)
    row = position // geometry.cols
    tile, recording = entry.tile, entry.recording
    subtitle = (tile.subtitle.format(f=f"{recording.frequency:g}")
                if recording is not None else tile.subtitle)
    draw.label_plate(canvas, (x, y), tile_w, tile.title, subtitle, tile.encoder)
    if row == 0 and tile.header and geometry.header_h:
        draw.column_header(canvas, (x, 0, x + tile_w + geometry.side_w, geometry.header_h),
                           tile.header)
    if recording is None:
        return
    playhead = entry.anchor + offset + recording.warmup
    if geometry.side_w:
        trail = entry.projected[max(0, playhead - TRAIL_ROWS + 1):playhead + 1]
        # A square of the cell height, so the square limits are not stretched.
        draw.latent_panel(canvas, (x + tile_w, y, x + tile_w + geometry.side_w,
                                   y + geometry.cell_h),
                          entry.rings, trail, entry.projected[playhead], limits,
                          draw.GAIT_COLOURS[_gait(tile.task)], ("PC1", "PC2"))
    below = y + tile_h
    if geometry.trace_h:
        box = (x, below, x + tile_w, below + geometry.trace_h)
        if clip.trace == "latent":
            draw.deviation_trace(canvas, box, entry.lines, entry.cut, playhead,
                                 recording.event_row, ceiling,
                                 draw.CONDITIONS[_row_encoder(clip, position)][1],
                                 recording.dt,
                                 TRACE_Y_LABEL if position % geometry.cols == 0 else None)
        else:
            draw.trace(canvas, box, entry.values, entry.cut, playhead, recording.event_row)
        below += geometry.trace_h
    if geometry.strip_h:
        draw.footfall_strip(canvas, (x, below, x + tile_w, below + geometry.strip_h),
                            recording.contact, recording.desired, playhead,
                            recording.event_row)


def render_clip(clip: Clip, runs: dict[str, str], root: Path, out_dir: Path, page: str,
                checkpoint: str | None = None, leading: dict[str, int] | None = None) -> dict:
    """`leading` holds each run's behaviour-component count, keyed like `runs`; it is
    read only by a clip with a latent panel or a latent trace."""
    geometry = clip.geometry
    shots = schedule.build(clip.segments)
    lo, hi = clip.window

    tiles = [_prepare_tile(clip, position, runs, root, checkpoint, leading)
             for position in range(len(clip.tiles))]
    limits = None
    if geometry.side_w:
        _share_rings(clip, tiles)
        limits = panel_limits([ring for e in tiles for ring in e.rings.values()])
    ceilings = ([_row_ceiling(clip, tiles, position) for position in range(len(tiles))]
                if geometry.trace_h and clip.trace == "latent" else [None] * len(tiles))

    def compose(offset: int, slow: bool, frame_of) -> Image.Image:
        canvas = Image.new("RGB", geometry.size, draw.BAND)
        for position, entry in enumerate(tiles):
            canvas.paste(frame_of(entry, entry.anchor + offset), _origin(clip, position))
            _draw_overlays(canvas, clip, entry, position, offset, limits, ceilings[position])
        if geometry.timeline_h:
            first = tiles[0]
            recording = first.recording
            shift = first.anchor + recording.warmup
            draw.timeline(canvas, (0, geometry.size[1] - geometry.timeline_h, *geometry.size),
                          (shift + lo, shift + hi), shift + offset, recording.event_row,
                          clip.tick_label, recording.push_rows if clip.push_band else None,
                          slow)
        elif slow:
            draw.slow_tag(canvas, geometry.size[0], 0)
        return canvas

    out_dir.mkdir(parents=True, exist_ok=True)
    video = out_dir / f"{clip.name}.mp4"
    crf = 23
    while True:
        readers = {id(entry): _TileReader(entry.raw,
                                          [entry.anchor + s.offset for s in shots],
                                          geometry.crop, geometry.tile) for entry in tiles}
        _encode(video, geometry.size,
                (compose(s.offset, s.slow, lambda e, i: readers[id(e)].get(i)) for s in shots),
                crf)
        for reader in readers.values():
            reader.close()
        size = video.stat().st_size
        if size <= clip.max_bytes:
            break
        if crf >= MAX_CRF:
            raise ClipSpecError(f"Clip '{clip.name}': {size} bytes at CRF {crf}, over "
                                f"{clip.max_bytes}; shorten the cut or shrink the frame.")
        print(f"  {clip.name}: {size} bytes at CRF {crf}; re-encoding at {crf + CRF_STEP}")
        crf += CRF_STEP

    def seek(entry, index):
        left, top = ((RAW_SIZE[0] - geometry.crop[0]) // 2, (RAW_SIZE[1] - geometry.crop[1]) // 2)
        frame = Image.fromarray(iio.imread(entry.raw, index=index)).crop(
            (left, top, left + geometry.crop[0], top + geometry.crop[1]))
        return frame.resize(geometry.tile, Image.LANCZOS)

    # A still carries no slow-motion tag, wherever its offset lies.
    compose(frames(clip.still_s), False, seek).save(out_dir / f"{clip.name}.jpg",
                                                     quality=85)

    return {
        "src": f"/videos/{page}/{clip.name}.mp4",
        "poster": f"/videos/{page}/{clip.name}.jpg",
        "width": geometry.size[0],
        "height": geometry.size[1],
        "duration_s": round(len(shots) / FPS_OUT, 2),
        "bytes": video.stat().st_size,
        "crf": crf,
        "tiles": [{
            "run": runs[entry.tile.run],
            "task": entry.tile.task,
            "recording": (str(entry.recording_file.relative_to(root))
                          if entry.recording_file else None),
            "event_frame": entry.anchor if clip.anchor == "event" else None,
        } for entry in tiles],
    }
