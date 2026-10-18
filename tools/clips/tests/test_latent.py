import numpy as np
import pytest

import latent
from gaitrl.pipeline.base.latent_reference import NominalLatentTable


def test_group_norms_split_the_scaled_deviation():
    d = np.array([[3.0, 4.0, 0.0, 0.0], [0.0, 0.0, 0.0, 5.0]])
    lead, trail = latent.group_norms(d, scaling=np.array([1, 2, 1, 1.0]), loading=np.eye(4), leading=2)
    assert lead.tolist() == [pytest.approx(np.hypot(3, 2)), 0.0] and trail.tolist() == [0.0, 5.0]


def test_masked_read_keeps_the_right_group():
    d = np.array([[1.0, 1.0, 1.0, 1.0]])
    k = dict(scaling=np.ones(4), loading=np.eye(4), leading=2)
    assert latent.masked_read(d, "identity", **k).tolist() == [[1, 1, 1, 1]]
    assert latent.masked_read(d, "blind", **k).tolist() == [[0, 0, 0, 0]]
    assert latent.masked_read(d, "trailing", **k).tolist() == [[0, 0, 1, 1]]
    assert latent.masked_read(d, "leading", **k).tolist() == [[1, 1, 0, 0]]


def test_group_amplitudes_are_the_rms_of_the_centred_cycle():
    bins = np.array([[1.0, 0, 0, 0], [-1.0, 0, 0, 0], [0, 0, 2.0, 0], [0, 0, -2.0, 0]])
    lead, trail = latent.group_amplitudes(bins, scaling=np.ones(4), loading=np.eye(4), leading=2)
    assert (lead, trail) == (pytest.approx(np.sqrt(0.5)), pytest.approx(np.sqrt(2.0)))


def test_a_command_outside_the_table_is_refused():
    # a NominalLatentTable built directly with commands [[1.2,0,0]] and a recording at 1.3 m/s
    table = NominalLatentTable(labels=tuple(f"d{i}" for i in range(4)),
                               commands=np.array([[1.2, 0.0, 0.0]]), bins=4,
                               mean=np.zeros((1, 4, 4)), residual_rms=np.zeros((1, 4)),
                               n_bin_rows=np.ones((1, 4)))
    with pytest.raises(ValueError):
        latent.command_id(table, np.array([[1.3, 0.0, 0.0]]))
