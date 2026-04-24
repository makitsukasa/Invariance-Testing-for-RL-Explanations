"""SoftMoET と同じインタフェースを持つベースライン Reasoned model。

- LinearReasonedModel: sklearn LogisticRegression
- SingleTreeReasonedModel: sklearn DecisionTreeClassifier (単一木)
- GBTReasonedModel: sklearn HistGradientBoostingClassifier (勾配ブースティング木)

どちらも .predict(obs) / .predict_proba(obs) を実装しており、
evaluate.py の action_agreement / kl_divergence / evaluate_rollout で
そのまま利用できる。
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler

try:
    from interpret.glassbox import ExplainableBoostingClassifier, ExplainableBoostingRegressor
except Exception:  # pragma: no cover
    ExplainableBoostingClassifier = None
    ExplainableBoostingRegressor = None

try:
    from gplearn.genetic import SymbolicRegressor
except Exception:  # pragma: no cover
    SymbolicRegressor = None


class LinearReasonedModel:
    """ロジスティック回帰による Reasoned model。

    Parameters
    ----------
    input_dim : int
        入力次元数（状態空間）
    n_actions : int
        行動空間のサイズ
    C : float
        正則化の逆強度（デフォルト 1.0）
    """

    def __init__(self, input_dim: int, n_actions: int, C: float = 1.0):
        self.input_dim = input_dim
        self.n_actions = n_actions
        self.model = LogisticRegression(max_iter=2000, C=C, solver="lbfgs")
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LinearReasonedModel":
        self.model.fit(X, y)
        self._fitted = True
        return self

    def predict_proba(self, obs: np.ndarray) -> np.ndarray:
        """shape: (n_samples, n_actions)"""
        proba = self.model.predict_proba(obs)
        full = np.zeros((len(obs), self.n_actions), dtype=np.float32)
        for idx, cls in enumerate(self.model.classes_):
            full[:, int(cls)] = proba[:, idx]
        return full

    def predict(self, obs: np.ndarray) -> np.ndarray:
        """shape: (n_samples,)"""
        return self.predict_proba(obs).argmax(axis=1)


class SingleTreeReasonedModel:
    """単一決定木による Reasoned model。

    Parameters
    ----------
    input_dim : int
        入力次元数
    n_actions : int
        行動空間のサイズ
    max_depth : int
        決定木の最大深さ
    """

    def __init__(self, input_dim: int, n_actions: int, max_depth: int = 5):
        self.input_dim = input_dim
        self.n_actions = n_actions
        self.max_depth = max_depth
        self.model = DecisionTreeClassifier(max_depth=max_depth)
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SingleTreeReasonedModel":
        self.model.fit(X, y)
        self._fitted = True
        return self

    def predict_proba(self, obs: np.ndarray) -> np.ndarray:
        """shape: (n_samples, n_actions)"""
        proba = self.model.predict_proba(obs)
        full = np.zeros((len(obs), self.n_actions), dtype=np.float32)
        for idx, cls in enumerate(self.model.classes_):
            full[:, int(cls)] = proba[:, idx]
        return full

    def predict(self, obs: np.ndarray) -> np.ndarray:
        """shape: (n_samples,)"""
        return self.predict_proba(obs).argmax(axis=1)


class RegressionTreeModel:
    """多出力決定木回帰による Reasoned model（連続行動空間用）。

    DecisionTreeRegressor を使用し、連続行動ベクトルを直接予測する。
    binning 不要で、Hopper 等の連続制御タスクに適用できる。

    Parameters
    ----------
    input_dim : int
        入力次元数（状態空間）
    action_dim : int
        行動空間の次元数（例: Hopper は 3）
    max_depth : int
        決定木の最大深さ
    """

    def __init__(self, input_dim: int, action_dim: int, max_depth: int = 5):
        self.input_dim = input_dim
        self.action_dim = action_dim
        self.max_depth = max_depth
        self.model = DecisionTreeRegressor(max_depth=max_depth)
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RegressionTreeModel":
        self.model.fit(X, y)
        self._fitted = True
        return self

    def predict(self, obs: np.ndarray) -> np.ndarray:
        """shape: (n_samples, action_dim)"""
        pred = self.model.predict(obs)
        if pred.ndim == 1:
            pred = pred[:, np.newaxis]
        return np.clip(pred, -1.0, 1.0).astype(np.float32)


class RegressionLinearModel:
    """多出力線形回帰による Reasoned model（連続行動空間用）。

    Parameters
    ----------
    input_dim : int
        入力次元数（状態空間）
    action_dim : int
        行動空間の次元数
    """

    def __init__(self, input_dim: int, action_dim: int):
        self.input_dim = input_dim
        self.action_dim = action_dim
        self.model = LinearRegression()
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RegressionLinearModel":
        self.model.fit(X, y)
        self._fitted = True
        return self

    def predict(self, obs: np.ndarray) -> np.ndarray:
        """shape: (n_samples, action_dim)"""
        pred = self.model.predict(obs)
        if pred.ndim == 1:
            pred = pred[:, np.newaxis]
        return np.clip(pred, -1.0, 1.0).astype(np.float32)


class GBTReasonedModel:
    """勾配ブースティング木による Reasoned model。

    HistGradientBoostingClassifier を使用。MoET や単一決定木より高い再現性が
    期待される説明可能モデル。LunarLander のような連続力学系でも収束実績がある。

    Parameters
    ----------
    input_dim : int
        入力次元数（状態空間）
    n_actions : int
        行動空間のサイズ
    max_iter : int
        ブースティング反復数
    max_depth : int | None
        個々の決定木の最大深さ（None で無制限）
    learning_rate : float
        学習率
    """

    def __init__(
        self,
        input_dim: int,
        n_actions: int,
        max_iter: int = 200,
        max_depth: int | None = None,
        learning_rate: float = 0.1,
    ):
        self.input_dim = input_dim
        self.n_actions = n_actions
        self.model = HistGradientBoostingClassifier(
            max_iter=max_iter,
            max_depth=max_depth,
            learning_rate=learning_rate,
        )
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GBTReasonedModel":
        self.model.fit(X, y)
        self._fitted = True
        return self

    def predict_proba(self, obs: np.ndarray) -> np.ndarray:
        """shape: (n_samples, n_actions)"""
        proba = self.model.predict_proba(obs)
        full = np.zeros((len(obs), self.n_actions), dtype=np.float32)
        for idx, cls in enumerate(self.model.classes_):
            full[:, int(cls)] = proba[:, idx]
        return full

    def predict(self, obs: np.ndarray) -> np.ndarray:
        """shape: (n_samples,)"""
        return self.predict_proba(obs).argmax(axis=1)


class EBMReasonedModel:
    """Explainable Boosting Machines による分類モデル。"""

    def __init__(
        self,
        input_dim: int,
        n_actions: int,
        max_rounds: int = 300,
        outer_bags: int = 8,
        interactions: int = 0,
    ):
        if ExplainableBoostingClassifier is None:
            raise ImportError(
                "interpret が見つかりません。`pip install interpret` を実行してください。"
            )
        self.input_dim = input_dim
        self.n_actions = n_actions
        self.model = ExplainableBoostingClassifier(
            max_rounds=max_rounds,
            outer_bags=outer_bags,
            interactions=interactions,
        )
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "EBMReasonedModel":
        self.model.fit(X, y)
        self._fitted = True
        return self

    def predict_proba(self, obs: np.ndarray) -> np.ndarray:
        proba = self.model.predict_proba(obs)
        full = np.zeros((len(obs), self.n_actions), dtype=np.float32)
        for idx, cls in enumerate(self.model.classes_):
            full[:, int(cls)] = proba[:, idx]
        return full

    def predict(self, obs: np.ndarray) -> np.ndarray:
        return self.predict_proba(obs).argmax(axis=1)


class _SoftDecisionTreeCore(nn.Module):
    """2^depth 葉を持つ簡易 Soft Decision Tree。"""

    def __init__(self, input_dim: int, n_actions: int, depth: int):
        super().__init__()
        self.depth = depth
        self.n_leaves = 2 ** depth
        self.n_nodes = self.n_leaves - 1
        self.gating_w = nn.Parameter(torch.randn(self.n_nodes, input_dim) * 0.05)
        self.gating_b = nn.Parameter(torch.zeros(self.n_nodes))
        self.leaf_logits = nn.Parameter(torch.zeros(self.n_leaves, n_actions))
        self.register_buffer("leaf_path", self._build_leaf_path(depth))

    @staticmethod
    def _build_leaf_path(depth: int) -> torch.Tensor:
        paths = []
        for leaf in range(2 ** depth):
            bits = [(leaf >> i) & 1 for i in range(depth - 1, -1, -1)]
            node = 0
            p = []
            for b in bits:
                p.append((node, b))
                node = 2 * node + 1 + b
            paths.append(p)

        path_idx = torch.full((2 ** depth, depth, 2), -1, dtype=torch.long)
        for li, p in enumerate(paths):
            for di, (node_idx, direction) in enumerate(p):
                path_idx[li, di, 0] = node_idx
                path_idx[li, di, 1] = direction
        return path_idx

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        gate_probs = torch.sigmoid(F.linear(x, self.gating_w, self.gating_b))
        leaf_probs = []
        for leaf in range(self.n_leaves):
            prob = torch.ones(x.shape[0], device=x.device)
            for d in range(self.depth):
                node_idx = self.leaf_path[leaf, d, 0]
                direction = self.leaf_path[leaf, d, 1]
                p_node = gate_probs[:, node_idx]
                prob = prob * (p_node if direction == 1 else (1.0 - p_node))
            leaf_probs.append(prob)
        leaf_probs = torch.stack(leaf_probs, dim=1)
        leaf_class_probs = F.softmax(self.leaf_logits, dim=1)
        probs = leaf_probs @ leaf_class_probs
        return torch.clamp(probs, min=1e-8, max=1.0)


class SoftDecisionTreeReasonedModel:
    """分類タスク向け Soft Decision Tree。"""

    def __init__(
        self,
        input_dim: int,
        n_actions: int,
        depth: int = 4,
        epochs: int = 150,
        lr: float = 1e-3,
        batch_size: int = 512,
        entropy_coef: float = 1e-3,
        seed: int = 42,
    ):
        self.input_dim = input_dim
        self.n_actions = n_actions
        self.depth = depth
        self.epochs = epochs
        self.lr = lr
        self.batch_size = batch_size
        self.entropy_coef = entropy_coef
        self.seed = seed
        self.scaler = StandardScaler()
        self.model = _SoftDecisionTreeCore(input_dim, n_actions, depth)
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SoftDecisionTreeReasonedModel":
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)
        Xs = self.scaler.fit_transform(X).astype(np.float32)
        X_t = torch.from_numpy(Xs)
        y_t = torch.from_numpy(y.astype(np.int64))
        opt = torch.optim.Adam(self.model.parameters(), lr=self.lr)

        n = len(X_t)
        for _ in range(self.epochs):
            perm = torch.randperm(n)
            for i in range(0, n, self.batch_size):
                idx = perm[i : i + self.batch_size]
                xb, yb = X_t[idx], y_t[idx]
                probs = self.model(xb)
                nll = F.nll_loss(torch.log(probs), yb)
                leaf_dist = F.softmax(self.model.leaf_logits, dim=1)
                entropy = -(leaf_dist * torch.log(torch.clamp(leaf_dist, min=1e-8))).sum(dim=1).mean()
                loss = nll + self.entropy_coef * entropy
                opt.zero_grad()
                loss.backward()
                opt.step()

        self._fitted = True
        return self

    def predict_proba(self, obs: np.ndarray) -> np.ndarray:
        Xs = self.scaler.transform(obs).astype(np.float32)
        with torch.no_grad():
            probs = self.model(torch.from_numpy(Xs)).cpu().numpy()
        return probs.astype(np.float32)

    def predict(self, obs: np.ndarray) -> np.ndarray:
        return self.predict_proba(obs).argmax(axis=1)


class SymbolicReasonedModel:
    """gplearn を使った多クラス向け Symbolic Regression。"""

    def __init__(
        self,
        input_dim: int,
        n_actions: int,
        population_size: int = 1200,
        generations: int = 25,
        tournament_size: int = 20,
        parsimony_coefficient: float = 0.001,
        random_state: int = 42,
    ):
        if SymbolicRegressor is None:
            raise ImportError(
                "gplearn が見つかりません。`pip install gplearn` を実行してください。"
            )
        self.input_dim = input_dim
        self.n_actions = n_actions
        self.population_size = population_size
        self.generations = generations
        self.tournament_size = tournament_size
        self.parsimony_coefficient = parsimony_coefficient
        self.random_state = random_state
        self.models: list[SymbolicRegressor] = []
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SymbolicReasonedModel":
        self.models = []
        for cls in range(self.n_actions):
            target = (y == cls).astype(np.float32)
            reg = SymbolicRegressor(
                population_size=self.population_size,
                generations=self.generations,
                tournament_size=self.tournament_size,
                parsimony_coefficient=self.parsimony_coefficient,
                random_state=self.random_state + cls,
                verbose=0,
            )
            reg.fit(X, target)
            self.models.append(reg)
        self._fitted = True
        return self

    def predict_proba(self, obs: np.ndarray) -> np.ndarray:
        scores = []
        for reg in self.models:
            s = reg.predict(obs)
            scores.append(np.clip(s, 0.0, 1.0))
        score_mat = np.stack(scores, axis=1).astype(np.float32)
        denom = np.sum(score_mat, axis=1, keepdims=True)
        proba = score_mat / np.clip(denom, 1e-8, None)
        return proba

    def predict(self, obs: np.ndarray) -> np.ndarray:
        return self.predict_proba(obs).argmax(axis=1)


class GBTRegressionReasonedModel:
    """勾配ブースティング木による回帰 Reasoned model（連続行動空間用）。

    action 次元ごとに独立した HistGradientBoostingRegressor を学習する。
    DAgger と組み合わせて Hopper 等の連続制御タスクに適用する。
    """

    def __init__(
        self,
        input_dim: int,
        action_dim: int,
        max_iter: int = 300,
        max_depth: int | None = None,
        learning_rate: float = 0.1,
    ):
        self.input_dim = input_dim
        self.action_dim = action_dim
        self.models = [
            HistGradientBoostingRegressor(
                max_iter=max_iter,
                max_depth=max_depth,
                learning_rate=learning_rate,
            )
            for _ in range(action_dim)
        ]
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GBTRegressionReasonedModel":
        for i, m in enumerate(self.models):
            m.fit(X, y[:, i] if y.ndim > 1 else y)
        self._fitted = True
        return self

    def predict(self, obs: np.ndarray) -> np.ndarray:
        """shape: (n_samples, action_dim)"""
        preds = np.stack([m.predict(obs) for m in self.models], axis=1)
        return np.clip(preds, -1.0, 1.0).astype(np.float32)


class EBMRegressionReasonedModel:
    """多出力回帰向け EBM（action 次元ごとに独立学習）。"""

    def __init__(
        self,
        input_dim: int,
        action_dim: int,
        max_rounds: int = 300,
        outer_bags: int = 8,
        interactions: int = 0,
    ):
        if ExplainableBoostingRegressor is None:
            raise ImportError(
                "interpret が見つかりません。`pip install interpret` を実行してください。"
            )
        self.input_dim = input_dim
        self.action_dim = action_dim
        self.max_rounds = max_rounds
        self.outer_bags = outer_bags
        self.interactions = interactions
        self.models: list[ExplainableBoostingRegressor] = []
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "EBMRegressionReasonedModel":
        self.models = []
        for d in range(self.action_dim):
            model = ExplainableBoostingRegressor(
                max_rounds=self.max_rounds,
                outer_bags=self.outer_bags,
                interactions=self.interactions,
            )
            model.fit(X, y[:, d])
            self.models.append(model)
        self._fitted = True
        return self

    def predict(self, obs: np.ndarray) -> np.ndarray:
        pred = np.stack([m.predict(obs) for m in self.models], axis=1)
        return np.clip(pred, -1.0, 1.0).astype(np.float32)


class _SoftDecisionTreeRegressorCore(nn.Module):
    """連続行動向け Soft Decision Tree。"""

    def __init__(self, input_dim: int, action_dim: int, depth: int):
        super().__init__()
        self.depth = depth
        self.action_dim = action_dim
        self.n_leaves = 2 ** depth
        self.n_nodes = self.n_leaves - 1
        self.gating_w = nn.Parameter(torch.randn(self.n_nodes, input_dim) * 0.05)
        self.gating_b = nn.Parameter(torch.zeros(self.n_nodes))
        self.leaf_values = nn.Parameter(torch.zeros(self.n_leaves, action_dim))
        self.register_buffer("leaf_path", _SoftDecisionTreeCore._build_leaf_path(depth))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        gate_probs = torch.sigmoid(F.linear(x, self.gating_w, self.gating_b))
        leaf_probs = []
        for leaf in range(self.n_leaves):
            prob = torch.ones(x.shape[0], device=x.device)
            for d in range(self.depth):
                node_idx = self.leaf_path[leaf, d, 0]
                direction = self.leaf_path[leaf, d, 1]
                p_node = gate_probs[:, node_idx]
                prob = prob * (p_node if direction == 1 else (1.0 - p_node))
            leaf_probs.append(prob)
        leaf_probs = torch.stack(leaf_probs, dim=1)
        preds = leaf_probs @ self.leaf_values
        return preds


class SoftDecisionTreeRegressionReasonedModel:
    """多出力回帰向け Soft Decision Tree。"""

    def __init__(
        self,
        input_dim: int,
        action_dim: int,
        depth: int = 5,
        epochs: int = 150,
        lr: float = 1e-3,
        batch_size: int = 512,
        l2_leaf_coef: float = 1e-4,
        seed: int = 42,
    ):
        self.input_dim = input_dim
        self.action_dim = action_dim
        self.depth = depth
        self.epochs = epochs
        self.lr = lr
        self.batch_size = batch_size
        self.l2_leaf_coef = l2_leaf_coef
        self.seed = seed
        self.scaler = StandardScaler()
        self.model = _SoftDecisionTreeRegressorCore(input_dim, action_dim, depth)
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SoftDecisionTreeRegressionReasonedModel":
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)
        Xs = self.scaler.fit_transform(X).astype(np.float32)
        X_t = torch.from_numpy(Xs)
        y_t = torch.from_numpy(y.astype(np.float32))
        opt = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        n = len(X_t)
        for _ in range(self.epochs):
            perm = torch.randperm(n)
            for i in range(0, n, self.batch_size):
                idx = perm[i : i + self.batch_size]
                xb, yb = X_t[idx], y_t[idx]
                pred = self.model(xb)
                mse = F.mse_loss(pred, yb)
                reg = (self.model.leaf_values ** 2).mean()
                loss = mse + self.l2_leaf_coef * reg
                opt.zero_grad()
                loss.backward()
                opt.step()
        self._fitted = True
        return self

    def predict(self, obs: np.ndarray) -> np.ndarray:
        Xs = self.scaler.transform(obs).astype(np.float32)
        with torch.no_grad():
            preds = self.model(torch.from_numpy(Xs)).cpu().numpy()
        return np.clip(preds, -1.0, 1.0).astype(np.float32)


class SymbolicRegressionReasonedModel:
    """多出力回帰向け Symbolic Regression（action 次元ごと）。"""

    def __init__(
        self,
        input_dim: int,
        action_dim: int,
        population_size: int = 1200,
        generations: int = 25,
        tournament_size: int = 20,
        parsimony_coefficient: float = 0.001,
        random_state: int = 42,
    ):
        if SymbolicRegressor is None:
            raise ImportError(
                "gplearn が見つかりません。`pip install gplearn` を実行してください。"
            )
        self.input_dim = input_dim
        self.action_dim = action_dim
        self.population_size = population_size
        self.generations = generations
        self.tournament_size = tournament_size
        self.parsimony_coefficient = parsimony_coefficient
        self.random_state = random_state
        self.models: list[SymbolicRegressor] = []
        self._fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "SymbolicRegressionReasonedModel":
        self.models = []
        for d in range(self.action_dim):
            reg = SymbolicRegressor(
                population_size=self.population_size,
                generations=self.generations,
                tournament_size=self.tournament_size,
                parsimony_coefficient=self.parsimony_coefficient,
                random_state=self.random_state + d,
                verbose=0,
            )
            reg.fit(X, y[:, d])
            self.models.append(reg)
        self._fitted = True
        return self

    def predict(self, obs: np.ndarray) -> np.ndarray:
        pred = np.stack([m.predict(obs) for m in self.models], axis=1)
        return np.clip(pred, -1.0, 1.0).astype(np.float32)
