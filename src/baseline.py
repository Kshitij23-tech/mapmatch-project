import numpy as np


def nearest(cands):
    """Geometry-only baseline: every point goes to its nearest road."""
    return np.array([c[0][0] if c else -1 for c in cands])