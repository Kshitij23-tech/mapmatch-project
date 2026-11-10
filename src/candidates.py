import numpy as np
import shapely
from shapely import STRtree

from . import config as C


def build_index(edges):
    geoms = np.array(edges.geometry.tolist(), dtype=object)
    return STRtree(geoms), geoms


def candidates_for_points(xy, tree, geoms, radius=None, k=None):
    """For every point: list of (edge_index, distance_m, offset_m_along_edge), nearest first."""
    radius = radius or C.SEARCH_RADIUS_M
    k = k or C.MAX_CANDS
    pts = shapely.points(xy)
    out = [[] for _ in range(len(pts))]
    pi, gi = tree.query(pts, predicate="dwithin", distance=radius)
    if len(pi) == 0:
        return out
    d = shapely.distance(pts[pi], geoms[gi])
    s = shapely.line_locate_point(geoms[gi], pts[pi])
    order = np.lexsort((d, pi))
    for a, b, dist, off in zip(pi[order], gi[order], d[order], s[order]):
        if len(out[a]) < k:
            out[a].append((int(b), float(dist), float(off)))
    return out