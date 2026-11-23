import numpy as np


def make_bias(p_service, cands, grp, w):
    """Extra log-score for every candidate: w * log(probability the classifier gives its road type)."""
    bias = []
    for i, cl in enumerate(cands):
        b = np.zeros(len(cl))
        for j, (e, _, _) in enumerate(cl):
            if grp[e] == 0:
                b[j] = w * np.log(1 - p_service[i] + 1e-3)
            elif grp[e] == 1:
                b[j] = w * np.log(p_service[i] + 1e-3)
        bias.append(b)
    return bias