import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold, cross_val_predict


def stack(trips, cols):
    X = np.concatenate([t["feats"][cols].to_numpy() for t in trips])
    y = np.concatenate([t["label"] for t in trips])
    g = np.concatenate([[t["trip"]] * len(t["label"]) for t in trips])
    m = (y == 0) | (y == 1)                           # connector points are not classified
    return X[m], y[m].astype(int), g[m]


def make_model():
    return RandomForestClassifier(n_estimators=200, min_samples_leaf=3, class_weight="balanced",
                                  n_jobs=-1, random_state=0)


def fit(trips, cols):
    X, y, _ = stack(trips, cols)
    return make_model().fit(X, y)


def evaluate_cv(trips, cols, folds=5):
    """Accuracy with whole trips held out together (no trip is in both train and test)."""
    X, y, g = stack(trips, cols)
    pred = cross_val_predict(make_model(), X, y, groups=g, cv=GroupKFold(n_splits=folds))
    return float((pred == y).mean()), pred, y


def p_service(model, feats, cols):
    """Probability that each point is on the service road."""
    p = model.predict_proba(feats[cols].to_numpy())
    return p[:, list(model.classes_).index(1)]