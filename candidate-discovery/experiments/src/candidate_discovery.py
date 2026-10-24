"""Candidate discovery baselines for tabular concept recovery experiments."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier


@dataclass(frozen=True)
class CandidateRanking:
    method: str
    scores: dict[str, float]
    ordered_features: list[str]

    @property
    def top_feature(self) -> str:
        return self.ordered_features[0]


def _discrete_mutual_information(x: np.ndarray, y: np.ndarray, n_bins: int = 8) -> float:
    if np.allclose(x, x[0]):
        return 0.0
    bins = np.linspace(float(x.min()), float(x.max()) + 1e-9, n_bins + 1)
    x_bin = np.clip(np.digitize(x, bins[1:-1], right=False), 0, n_bins - 1)
    x_vals, x_counts = np.unique(x_bin, return_counts=True)
    y_vals, y_counts = np.unique(y, return_counts=True)
    joint_vals, joint_counts = np.unique(np.stack([x_bin, y], axis=1), axis=0, return_counts=True)

    n = float(len(x))
    px = {int(v): c / n for v, c in zip(x_vals, x_counts)}
    py = {int(v): c / n for v, c in zip(y_vals, y_counts)}
    mi = 0.0
    for (xv, yv), count in zip(joint_vals, joint_counts):
        pxy = count / n
        mi += pxy * np.log((pxy + 1e-12) / (px[int(xv)] * py[int(yv)] + 1e-12))
    return float(mi)


def _rank_from_scores(method: str, feature_names: list[str], scores: list[float]) -> CandidateRanking:
    pairs = sorted(zip(feature_names, scores), key=lambda item: (-item[1], item[0]))
    return CandidateRanking(
        method=method,
        scores={name: float(score) for name, score in pairs},
        ordered_features=[name for name, _ in pairs],
    )


def _train_val_split(obs: np.ndarray, actions: np.ndarray, seed: int, ratio: float = 0.7):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(obs))
    n_train = max(1, int(len(obs) * ratio))
    train_idx = idx[:n_train]
    val_idx = idx[n_train:]
    if len(val_idx) == 0:
        val_idx = train_idx
    return obs[train_idx], actions[train_idx], obs[val_idx], actions[val_idx]


def _shuffle_feature(x: np.ndarray, feature_idx: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    x_shuffled = x.copy()
    perm = rng.permutation(len(x_shuffled))
    x_shuffled[:, feature_idx] = x_shuffled[perm, feature_idx]
    return x_shuffled


def rank_candidates(
    method: str,
    obs: np.ndarray,
    oracle_actions: np.ndarray,
    feature_names: list[str],
    seed: int,
) -> CandidateRanking:
    if method == "mutual_info":
        scores = [
            _discrete_mutual_information(obs[:, idx], oracle_actions)
            for idx in range(obs.shape[1])
        ]
        return _rank_from_scores(method, feature_names, scores)

    x_train, y_train, x_val, y_val = _train_val_split(obs, oracle_actions, seed=seed)

    if method == "linear_probe_drop":
        clf = LogisticRegression(max_iter=1000, random_state=seed)
    elif method == "tree_probe_drop":
        clf = DecisionTreeClassifier(max_depth=4, random_state=seed)
    elif method == "random":
        rng = np.random.default_rng(seed)
        scores = rng.random(obs.shape[1]).tolist()
        return _rank_from_scores(method, feature_names, scores)
    else:
        raise ValueError(f"Unknown candidate discovery method: {method}")

    clf.fit(x_train, y_train)
    baseline = accuracy_score(y_val, clf.predict(x_val))
    scores = []
    for idx in range(obs.shape[1]):
        x_val_shuffled = _shuffle_feature(x_val, idx, seed + idx * 9973)
        acc = accuracy_score(y_val, clf.predict(x_val_shuffled))
        scores.append(float(baseline - acc))
    return _rank_from_scores(method, feature_names, scores)
