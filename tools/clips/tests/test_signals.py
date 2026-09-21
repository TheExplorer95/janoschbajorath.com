import numpy as np

from signals import deviation


def _periodic(rows=400, period=20):
    phase = ((np.arange(rows) + 0.5) / period) % 1.0      # off the bin edges, as real phases are
    targets = np.stack([np.sin(2 * np.pi * phase), np.cos(2 * np.pi * phase)], axis=1)
    return phase, targets


def test_a_periodic_signal_with_one_disturbed_cycle_spikes_there_and_nowhere_else():
    phase, targets = _periodic()
    targets = targets + 0.01 * np.random.default_rng(0).standard_normal(targets.shape)
    targets[200:220] += 1.0                    # one cycle pushed off its orbit, from the event
    trace = deviation(targets, phase, first_row=40, event_row=200, bins=20)

    assert np.isnan(trace[:40]).all()
    assert trace[200:220].min() > 20                      # 1.41 against a 0.014 baseline
    assert np.nanmean(trace[240:400]) < 1.5


def test_a_phase_bin_the_baseline_never_visits_is_filled_from_its_neighbours():
    phase, targets = _periodic(rows=200, period=10)       # 10 phases, 36 bins: most are empty
    trace = deviation(targets, phase, first_row=0, event_row=100, bins=36)
    assert np.isfinite(trace).all()
