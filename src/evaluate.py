import numpy as np
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support


def group_pred(edge_idx, grp):
    """Edge index per point -> road group per point (0 main road, 1 service road, 2 other, -1 none)."""
    out = np.full(len(edge_idx), -1)
    ok = edge_idx >= 0
    out[ok] = grp[edge_idx[ok]]
    return out


def _clean(y, p):
    m = (y == 0) | (y == 1)                           # label 2 (other road) is not scored
    y, p = y[m].astype(int), p[m].astype(int)
    p = np.where((p == 0) | (p == 1), p, 1 - y)      # connector or unmatched counts as wrong
    return y, p


def metrics(y, p):
    y, p = _clean(y, p)
    pr, rc, f1, _ = precision_recall_fscore_support(y, p, labels=[0, 1], zero_division=0)
    return {"acc": float((y == p).mean()), "f1_macro": float(f1.mean()),
            "prec_main": float(pr[0]), "rec_main": float(rc[0]),
            "prec_serv": float(pr[1]), "rec_serv": float(rc[1]), "n": int(len(y))}


def confusion(y, p):
    y, p = _clean(y, p)
    return confusion_matrix(y, p, labels=[0, 1])      # rows = true (main, service), columns = predicted


def main_distance(xy, groups):
    """Metres travelled on the main road: steps between GPS points, counted when the point reached is on the main road."""
    step = np.hypot(*np.diff(xy, axis=0).T)
    return float(step[np.asarray(groups)[1:] == 0].sum())


def switches(groups):
    """Positions where the road type changes between main (0) and service (1). Points of other types are skipped.
    Returns a list of (position, direction) with direction '0>1' (leaves the main road) or '1>0' (enters it)."""
    g = np.asarray(groups)
    pos = np.flatnonzero((g == 0) | (g == 1))
    out = []
    for a, b in zip(pos[:-1], pos[1:]):
        if g[a] != g[b]:
            out.append((int(b), f"{g[a]}>{g[b]}"))
    return out


def switch_scores(true_g, pred_g, tol=5):
    """How many true road changes have a predicted change of the same direction within tol points, and how many extra changes were predicted."""
    ts, ps = switches(true_g), switches(pred_g)
    used, found = set(), 0
    for pos, d in ts:
        best = None
        for k, (q, e) in enumerate(ps):
            if k not in used and e == d and abs(q - pos) <= tol and (best is None or abs(q - pos) < abs(ps[best][0] - pos)):
                best = k
        if best is not None:
            used.add(best)
            found += 1
    return {"switch_true": len(ts), "switch_found": found, "switch_extra": len(ps) - len(used)}