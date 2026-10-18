"""The run's own latent basis and nominal table, read through gaitrl's readers, and the
quantities the latent panel (D7) and the deviation trace (D9) draw from them.

The numeric functions at the top take plain arrays and do no file I/O. Scaled means
divided by the basis's per-dimension divisor; a group is the span of the basis's leading
(behaviour) or trailing (domain) components."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

try:
    from gaitrl.pipeline.analysis.projection import project_rows
    from gaitrl.pipeline.base.latent_reference import (
        ArtifactProvenance, LatentBasis, MaskKind, NominalLatentTable, apply_mask,
        mask_matrices, read_latent_basis, read_nominal_table)
except ImportError as error:
    raise ImportError(
        f"{error}; tools/clips/latent.py reads the basis through gaitrl, which the isaac "
        f"conda env carries: run under `conda run -n isaac` or pip install -e "
        f"/home/janosch/code/gait_rl.") from error

import sources

LATENT_DIM_COLUMN = "latent_dim"
COMMAND_TOLERANCE = 1e-4
MIN_AMPLITUDE = 1e-9       # scaled units; a nominal cycle flatter than this normalises nothing
NODE = sources.LATENT_NODE
WIDTH = sources.LATENT_WIDTH


# ---- pure numerics ----------------------------------------------------------------

def _projectors(loading: np.ndarray, leading: int) -> tuple[np.ndarray, np.ndarray]:
    rows = np.asarray(loading, dtype=float)
    lead, trail = rows[:leading], rows[leading:]
    return lead.T @ lead, trail.T @ trail


def group_norms(deviation: np.ndarray, scaling: np.ndarray, loading: np.ndarray,
                leading: int) -> tuple[np.ndarray, np.ndarray]:
    """`(rows,)` norms of `P_lead d_s` and `P_trail d_s`, `d_s = deviation / scaling`."""
    scaled = np.asarray(deviation, dtype=float) / np.asarray(scaling, dtype=float)
    lead, trail = _projectors(loading, leading)
    return (np.linalg.norm(scaled @ lead, axis=1), np.linalg.norm(scaled @ trail, axis=1))


def group_amplitudes(nominal_mean: np.ndarray, scaling: np.ndarray, loading: np.ndarray,
                     leading: int) -> tuple[float, float]:
    """RMS over the bins of each group's norm of `(h(phi_b) - mean_b h) / scaling` for one
    condition's `(bins, width)` table."""
    cycle = np.asarray(nominal_mean, dtype=float)
    lead, trail = group_norms(cycle - cycle.mean(axis=0), scaling, loading, leading)
    return float(np.sqrt(np.mean(lead ** 2))), float(np.sqrt(np.mean(trail ** 2)))


def _toy_basis(scaling: np.ndarray, loading: np.ndarray, leading: int) -> LatentBasis:
    width = np.asarray(loading).shape[1]
    return LatentBasis(labels=tuple(f"{NODE}_{i}" for i in range(width)),
                       loading=np.asarray(loading, dtype=float),
                       scaling=np.asarray(scaling, dtype=float), leading_components=int(leading))


def masked_read(deviation: np.ndarray, mask: str, scaling: np.ndarray, loading: np.ndarray,
                leading: int) -> np.ndarray:
    """`M d` for one of the mask kinds, in recorded coordinates: `apply_mask` on a zero
    nominal with the one matrix `mask_matrices` builds for the kind."""
    rows = np.asarray(deviation, dtype=float)
    matrix = mask_matrices(_toy_basis(scaling, loading, leading), [MaskKind(mask)], None)[0]
    matrices = np.broadcast_to(matrix, (rows.shape[0], *matrix.shape))
    return apply_mask(matrices, rows, np.zeros_like(rows))


# ---- the reference of one recording ----------------------------------------------

@dataclass(frozen=True)
class Reference:
    basis: LatentBasis
    table: NominalLatentTable
    center: np.ndarray          # (16,), the basis file's `center` row
    scaling: np.ndarray         # (16,), a divisor
    loading: np.ndarray         # (16, 16), rows orthonormal in the scaled coordinates
    leading: int
    command_ids: np.ndarray     # (rows,), one id per recording row; all equal


def command_id(table: NominalLatentTable, commands: np.ndarray) -> int:
    """The one condition a clip's command rows name; refuses a command outside the table
    and a clip that names more than one condition."""
    ids = np.unique(table.command_ids(np.asarray(commands, dtype=float),
                                      tolerance=COMMAND_TOLERANCE))
    if len(ids) != 1:
        raise ValueError(f"The clip names {len(ids)} conditions {ids.tolist()} of the nominal "
                         f"table; one command is expected over the whole clip.")
    return int(ids[0])


def _basis_center(path: Path, labels: tuple[str, ...]) -> np.ndarray:
    """The basis file's `center` value per latent dimension, which is constant along the
    component axis."""
    frame = pq.read_table(path, columns=[LATENT_DIM_COLUMN, "center"]).to_pandas()
    center = np.empty(len(labels))
    for index, label in enumerate(labels):
        values = frame.loc[frame[LATENT_DIM_COLUMN].astype(str) == label, "center"].to_numpy(dtype=float)
        if values.size == 0 or not np.allclose(values, values[0]):
            raise ValueError(f"{path} carries no single 'center' value for '{label}'.")
        center[index] = values[0]
    return center


def load_reference(run_dir: Path, recording_path: Path, recording: sources.Recording,
                   leading: int, nominal_source: str = "nominal_fixed") -> Reference:
    """The basis and the nominal table of `run_dir`, refused unless they were produced
    from the recording's run, checkpoint, precision and latent block."""
    meta = sources.recording_meta(recording_path)
    expect = ArtifactProvenance(run_path=str(Path(run_dir).resolve()),
                                checkpoint_id=int(meta["checkpoint"]), node=NODE,
                                block=recording.block, width=WIDTH,
                                precision=str(meta["precision"]))
    folder = Path(run_dir) / "analysis" / "latent_representation"
    basis_path = folder / "shared" / "latent_basis.parquet"
    basis = read_latent_basis(basis_path, expect=expect, leading_components=leading)
    table = read_nominal_table(folder / "sources" / nominal_source / "latent_nominal.parquet",
                               expect=expect)
    one = command_id(table, recording.commands)
    return Reference(basis=basis, table=table, center=_basis_center(basis_path, basis.labels),
                     scaling=basis.scaling, loading=basis.loading,
                     leading=basis.leading_components,
                     command_ids=np.full(recording.rows, one, dtype=np.int64))


def _clip_command(reference: Reference) -> int:
    return int(reference.command_ids[0])


def nominal_rows(reference: Reference, phase: np.ndarray) -> np.ndarray:
    """`(rows, 16)` — the nominal latent at each row's phase; NaN where the phase is."""
    phase = np.asarray(phase, dtype=float)
    out = np.full((len(phase), len(reference.center)), np.nan)
    finite = np.isfinite(phase)
    out[finite] = reference.table.lookup(reference.command_ids[finite], phase[finite])
    return out


def project(reference: Reference, latent: np.ndarray) -> np.ndarray:
    """`(rows, 16)` — the rows' coordinates on the basis's components."""
    return project_rows(latent, center=reference.center, scaling=reference.scaling,
                        loading=reference.loading)


def trace_lines(recording: sources.Recording, reference: Reference, mask: str,
                event_row: int) -> dict[str, np.ndarray]:
    """The deviation trace's four lines over the recording's rows: `behaviour` and `domain`
    are what the controller reads (the raw deviation before `event_row`, the masked one
    from it); `behaviour_raw` and `domain_raw` the raw deviation throughout. Each is the
    group norm of the scaled deviation from the clip's own nominal cycle, divided by the
    group's nominal-cycle amplitude, so 1 reads as a deviation the size of the cycle itself.
    NaN where the phase or the latent is."""
    deviation = recording.latent - nominal_rows(reference, recording.phase)
    k = dict(scaling=reference.scaling, loading=reference.loading, leading=reference.leading)
    lead_raw, trail_raw = group_norms(deviation, **k)
    lead_masked, trail_masked = group_norms(masked_read(deviation, mask, **k), **k)
    before = np.arange(recording.rows) < event_row
    lines = {"behaviour": np.where(before, lead_raw, lead_masked),
             "domain": np.where(before, trail_raw, trail_masked),
             "behaviour_raw": lead_raw, "domain_raw": trail_raw}
    amplitude = dict(zip(("behaviour", "domain"), group_amplitudes(
        reference.table.mean[_clip_command(reference)], **k)))
    if min(amplitude.values()) < MIN_AMPLITUDE:
        raise ValueError(f"The nominal cycle at the clip's command has no amplitude on a "
                         f"group ({amplitude}); it cannot normalise the deviation.")
    return {name: line / amplitude[name.removesuffix("_raw")] for name, line in lines.items()}
