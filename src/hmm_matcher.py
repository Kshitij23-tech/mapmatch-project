import numpy as np

from . import config as C
from .network import Network  # noqa: F401  (the road graph class lives in network.py)


def viterbi(xy, cands, net, bias=None, sigma=None, beta=None):
    """Most likely road for every point. Returns one edge index per point (-1 = no candidate).

    bias[i] is an optional array with one extra log-score per candidate of point i."""
    sigma = sigma or C.SIGMA_M
    beta = beta or C.BETA_M
    n = len(xy)
    result = np.full(n, -1)
    idx = [i for i in range(n) if cands[i]]
    if not idx:
        return result

    def emission(i):
        d = np.array([c[1] for c in cands[i]])
        e = -0.5 * (d / sigma) ** 2
        if bias is not None:
            e = e + bias[i]
        return e

    prev = idx[0]
    score = emission(prev)
    back = []
    for i in idx[1:]:
        gc = float(np.hypot(*(xy[i] - xy[prev])))
        e = emission(i)
        new = np.empty(len(cands[i]))
        ptr = np.empty(len(cands[i]), dtype=int)
        for j, cj in enumerate(cands[i]):
            best, arg = -np.inf, 0
            for k, ck in enumerate(cands[prev]):
                r = net.route((ck[0], ck[2]), (cj[0], cj[2]))
                t = -C.NO_ROUTE_PENALTY if not np.isfinite(r) else max(-abs(gc - r) / beta, -C.NO_ROUTE_PENALTY)
                v = score[k] + t
                if v > best:
                    best, arg = v, k
            new[j] = best + e[j]
            ptr[j] = arg
        back.append(ptr)
        score, prev = new, i

    k = int(np.argmax(score))
    path = [k]
    for ptr in reversed(back):
        k = int(ptr[k])
        path.append(k)
    path.reverse()
    for i, k in zip(idx, path):
        result[i] = cands[i][k][0]
    return result