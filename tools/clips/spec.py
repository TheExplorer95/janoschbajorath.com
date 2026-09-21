"""What one published clip is made of. Entries are validated when constructed, so a
timing mistake is an error before any frame is rendered."""

from __future__ import annotations

from dataclasses import dataclass

FPS_RAW = 50
FPS_OUT = 25
SKIP_FRAMES = 3
"""Leading raw frames that are never shown: a stale camera, then an unloaded ground."""
MAX_BYTES = 5_000_000
RAW_SIZE = (1920, 1080)


class ClipSpecError(ValueError):
    pass


def frames(seconds: float) -> int:
    """Raw-frame count of a time; refuses a time that is not on the 50 fps lattice."""
    exact = seconds * FPS_RAW
    nearest = round(exact)
    if abs(exact - nearest) > 1e-6:
        raise ClipSpecError(f"{seconds} s is not a whole number of raw frames at {FPS_RAW} fps.")
    return nearest


@dataclass(frozen=True)
class Segment:
    """A stretch of the cut, in seconds from the anchor, half-open."""
    start_s: float
    end_s: float
    slow: bool

    @property
    def start(self) -> int:
        return frames(self.start_s)

    @property
    def end(self) -> int:
        return frames(self.end_s)


@dataclass(frozen=True)
class Tile:
    run: str
    task: str
    title: str
    """Bold first label line; empty for a tile without a label plate."""
    subtitle: str
    """Second label line; `{f}` is replaced by the recording's stride frequency in Hz."""
    encoder: str | None
    """`"ppo"` or `"aux"`: the encoder's name is drawn in its colour; None draws none."""
    header: str | None
    """Column header above the tile; read from the first row only."""


@dataclass(frozen=True)
class Geometry:
    crop: tuple[int, int]
    """Frame-centred source box in raw pixels, (width, height)."""
    tile: tuple[int, int]
    rows: int
    cols: int
    header_h: int = 0
    trace_h: int = 0
    strip_h: int = 0
    timeline_h: int = 0

    def __post_init__(self) -> None:
        sizes = (*self.crop, *self.tile, self.header_h, self.trace_h, self.strip_h,
                 self.timeline_h)
        if any(value % 2 for value in sizes):
            raise ClipSpecError(f"Every size must be even for yuv420p; got {sizes}.")
        if self.crop[0] > RAW_SIZE[0] or self.crop[1] > RAW_SIZE[1]:
            raise ClipSpecError(f"Crop {self.crop} exceeds the raw frame {RAW_SIZE}.")

    @property
    def cell_h(self) -> int:
        return self.tile[1] + self.trace_h + self.strip_h

    @property
    def size(self) -> tuple[int, int]:
        return (self.cols * self.tile[0],
                self.header_h + self.rows * self.cell_h + self.timeline_h)


@dataclass(frozen=True)
class Clip:
    name: str
    tiles: tuple[Tile, ...]
    geometry: Geometry
    anchor: str
    """`"event"`: times count from each tile's event frame. `"raw"`: from raw frame 0."""
    event_column: str | None
    segments: tuple[Segment, ...]
    tick_label: str | None
    push_band: bool
    still_s: float
    env_idx: int = 0

    def __post_init__(self) -> None:
        if self.anchor not in ("event", "raw"):
            raise ClipSpecError(f"Clip '{self.name}': anchor must be 'event' or 'raw'.")
        if self.anchor == "event" and self.event_column is None:
            raise ClipSpecError(f"Clip '{self.name}': an event cut needs an event_column.")
        wanted = self.geometry.rows * self.geometry.cols
        if len(self.tiles) != wanted:
            raise ClipSpecError(f"Clip '{self.name}': the grid holds {wanted} tiles, "
                                f"{len(self.tiles)} given.")
        if not self.segments:
            raise ClipSpecError(f"Clip '{self.name}': no segments.")
        origin = 0 if self.anchor == "event" else self.segments[0].start
        for segment in self.segments:
            if segment.end <= segment.start:
                raise ClipSpecError(f"Clip '{self.name}': empty segment {segment}.")
            if not segment.slow and ((segment.start - origin) % 2 or
                                     (segment.end - segment.start) % 2):
                raise ClipSpecError(
                    f"Clip '{self.name}': a normal-speed segment must start an even number "
                    f"of frames from the anchor and have even length; got {segment}.")
        if self.anchor == "raw" and self.window[0] < SKIP_FRAMES:
            raise ClipSpecError(f"Clip '{self.name}': the cut starts before frame 3, "
                                f"which is never shown.")
        frames(self.still_s)

    @property
    def window(self) -> tuple[int, int]:
        return (min(s.start for s in self.segments), max(s.end for s in self.segments))

    @property
    def needs_recording(self) -> bool:
        geometry = self.geometry
        return bool(self.anchor == "event" or geometry.strip_h or geometry.trace_h)
