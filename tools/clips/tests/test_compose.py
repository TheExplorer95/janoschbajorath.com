import numpy as np

import compose


def test_the_ceiling_is_the_largest_finite_value_rounded_up_at_least_the_floor():
    assert compose.trace_ceiling([np.array([0.2, np.nan]), np.array([1.74])]) == 1.8
    assert compose.trace_ceiling([np.array([np.nan, np.nan])]) == 1.0


def test_panel_limits_are_square_and_shared():
    limits = compose.panel_limits([np.array([[-1.0, 0.0], [1.0, 0.0]]),
                                   np.array([[0.0, -2.0], [0.0, 2.0]])], margin=0.0)
    assert limits == (-2.0, 2.0, -2.0, 2.0)
