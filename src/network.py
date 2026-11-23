import networkx as nx
import numpy as np

from . import config as C


class Network:
    """Road graph plus the lookups the matcher needs."""

    def __init__(self, G, edges):
        self.G = G
        self.U = edges["u"].to_numpy()
        self.V = edges["v"].to_numpy()
        self.L = edges.geometry.length.to_numpy()
        self.grp = edges["grp"].to_numpy()
        self._reach = {}

    def reach(self, node):
        r = self._reach.get(node)
        if r is None:
            r = nx.single_source_dijkstra_path_length(self.G, node, cutoff=C.ROUTE_CUTOFF_M, weight="length")
            self._reach[node] = r
        return r

    def route(self, a, b):
        """Driving distance from (edge, offset) a to (edge, offset) b; inf if not reachable."""
        ea, sa = a
        eb, sb = b
        if ea == eb and sb >= sa - C.BACK_TOL_M:
            return max(sb - sa, 0.0)
        d = self.reach(self.V[ea]).get(self.U[eb])
        if d is None:
            return np.inf
        return (self.L[ea] - sa) + d + sb