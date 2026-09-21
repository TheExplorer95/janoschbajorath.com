"""One clip entry -> video, still and manifest entry."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import imageio.v3 as iio
import imageio_ffmpeg
import numpy as np
from PIL import Image

import draw
import schedule
import signals
import sources
from spec import FPS_OUT, MAX_BYTES, RAW_SIZE, SKIP_FRAMES, Clip, frames

TRACE_SETTLE_ROWS = 28
"""Rows after the warmup left out of the deviation trace's baseline (0.56 s)."""


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


def render_clip(clip: Clip, runs: dict[str, str], root: Path, out_dir: Path) -> dict:
    geometry = clip.geometry
    shots = schedule.build(clip.segments)
    lo, hi = clip.window

    tiles = []
    for position, tile in enumerate(clip.tiles):
        where = f"clip '{clip.name}', tile {position} ({tile.run}/{tile.task})"
        recording = recording_file = None
        try:
            raw = sources.clip_path(root, runs[tile.run], tile.task)
            n_frames = sources.frame_count(raw)
            if clip.needs_recording:
                recording_file = sources.recording_path(root, runs[tile.run], tile.task)
                recording = sources.load_recording(recording_file, clip.env_idx,
                                                   clip.event_column)
                sources.check_pair(raw, recording_file, recording, n_frames)
        except sources.SourceError as error:
            raise sources.SourceError(f"{where}: {error}") from error
        anchor = recording.frame_of(recording.event_row) if clip.anchor == "event" else 0
        if anchor + lo < SKIP_FRAMES or anchor + hi > n_frames:
            raise sources.SourceError(
                f"{where}: the cut spans raw frames {anchor + lo}..{anchor + hi}, outside "
                f"{SKIP_FRAMES}..{n_frames}.")
        values = None
        if geometry.trace_h:
            values = signals.deviation(recording.targets, recording.phase,
                                       recording.warmup + TRACE_SETTLE_ROWS,
                                       recording.event_row)
        tiles.append({"tile": tile, "raw": raw, "anchor": anchor, "recording": recording,
                      "recording_file": recording_file, "values": values})

    def compose(offset: int, slow: bool, frame_of) -> Image.Image:
        canvas = Image.new("RGB", geometry.size, draw.BAND)
        tile_w, tile_h = geometry.tile
        for position, entry in enumerate(tiles):
            row, col = divmod(position, geometry.cols)
            x, y = col * tile_w, geometry.header_h + row * geometry.cell_h
            tile, recording = entry["tile"], entry["recording"]
            canvas.paste(frame_of(entry, entry["anchor"] + offset), (x, y))
            subtitle = (tile.subtitle.format(f=f"{recording.frequency:g}")
                        if recording is not None else tile.subtitle)
            draw.label_plate(canvas, (x, y), tile_w, tile.title, subtitle, tile.encoder)
            if row == 0 and tile.header and geometry.header_h:
                draw.column_header(canvas, (x, 0, x + tile_w, geometry.header_h), tile.header)
            if recording is None:
                continue
            playhead = entry["anchor"] + offset + recording.warmup
            cut = (entry["anchor"] + lo + recording.warmup,
                   entry["anchor"] + hi + recording.warmup)
            below = y + tile_h
            if geometry.trace_h:
                draw.trace(canvas, (x, below, x + tile_w, below + geometry.trace_h),
                           entry["values"], cut, playhead, recording.event_row)
                below += geometry.trace_h
            if geometry.strip_h:
                draw.footfall_strip(canvas, (x, below, x + tile_w, below + geometry.strip_h),
                                    recording.contact, recording.desired, playhead,
                                    recording.event_row)
        if geometry.timeline_h:
            first = tiles[0]
            recording = first["recording"]
            shift = first["anchor"] + recording.warmup
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
        readers = {id(entry): _TileReader(entry["raw"],
                                          [entry["anchor"] + s.offset for s in shots],
                                          geometry.crop, geometry.tile) for entry in tiles}
        _encode(video, geometry.size,
                (compose(s.offset, s.slow, lambda e, i: readers[id(e)].get(i)) for s in shots),
                crf)
        for reader in readers.values():
            reader.close()
        if video.stat().st_size <= MAX_BYTES or crf >= 26:
            break
        print(f"  {clip.name}: {video.stat().st_size} bytes at CRF {crf}; re-encoding at 26")
        crf = 26

    def seek(entry, index):
        left, top = ((RAW_SIZE[0] - geometry.crop[0]) // 2, (RAW_SIZE[1] - geometry.crop[1]) // 2)
        frame = Image.fromarray(iio.imread(entry["raw"], index=index)).crop(
            (left, top, left + geometry.crop[0], top + geometry.crop[1]))
        return frame.resize(geometry.tile, Image.LANCZOS)

    # A still carries no slow-motion tag, wherever its offset lies.
    compose(frames(clip.still_s), False, seek).save(out_dir / f"{clip.name}.jpg", quality=85)

    return {
        "src": f"/videos/where-2026/{clip.name}.mp4",
        "poster": f"/videos/where-2026/{clip.name}.jpg",
        "width": geometry.size[0],
        "height": geometry.size[1],
        "duration_s": round(len(shots) / FPS_OUT, 2),
        "bytes": video.stat().st_size,
        "crf": crf,
        "tiles": [{
            "run": runs[entry["tile"].run],
            "task": entry["tile"].task,
            "recording": (str(entry["recording_file"].relative_to(root))
                          if entry["recording_file"] else None),
            "event_frame": entry["anchor"] if clip.anchor == "event" else None,
        } for entry in tiles],
    }
