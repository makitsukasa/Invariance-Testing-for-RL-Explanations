# Detecting Spurious Dependencies in Surrogate Explanations of RL Policies via Invariance Testing

強化学習（RL）で学習したブラックボックス方策（Oracle policy）に手を加えず、構造制約付きの蒸留モデル（Surrogate model）を事後的に配置することで、説明品質をモデル非依存に診断するプロジェクト。

---

## 研究概要

先行研究の XRL（説明可能強化学習）は行動一致率（AA）の最大化を達成の証拠としてきたが、高 AA の Surrogate model が Oracle policy と同じスプリアス依存を写し取っているケースを検出できない。本研究は **再現性** と **分布シフト下での不変性** の二軸で説明品質を診断する枠組みを提案する。

### 二段階評価

**Stage 1 — 再現性の確認**
- 離散行動空間：行動一致率 AA > 0.9
- 連続行動空間：決定係数 R² > 0.9（ε-agreement を補助指標として併用）

**Stage 2 — 不変性の検査**
- 分布シフト $D_\text{train} \to D_\text{shift}$ に対し $({\rm AA}(D_\text{shift}),\; J_S(D_\text{shift}))$ を報告
- スプリアス依存の疑いが強い：${\rm AA}(D_\text{shift}) > \theta_{\rm AA}$ かつ $J_S(D_\text{shift}) < \alpha \times J_S(D_\text{train})$

なお、本枠組みはスプリアス依存を**検出**するが、その不在を確認する機能は持たない。

---

## 実験構成

| 実験 | 環境 | 目的 |
|------|------|------|
| 実験1 | CartPole（ノイズ特徴拡張） | Stage 1：ノイズ次元数と AA 上限の関係 |
| 実験2 | Spurious GridWorld（p=0.0） | Stage 2：スプリアス依存の検出デモ（高 AA・低不変性） |
| 実験3 | CartPole（非スプリアス・重力シフト） | 対照実験：非スプリアス環境での壊滅的崩壊なし |
| 実験4 | CartPole（モデル比較） | モデル種別（MoET・Tree・Linear）の AA 比較 |
| 実験5 | Spurious GridWorld（モデル比較） | 同上、GridWorld 版 |
| 実験6 | Spurious GridWorld（蒸留感度） | 蒸留データ量と AA の関係 |
| 実験7 | LunarLander-v3（付録） | 連続物理系への拡張性（予備的） |
| 実験8 | MuJoCo Hopper-v5（付録） | 連続制御タスクへの拡張性（予備的） |
| 実験9 | Spurious GridWorld（faithfulness 比較） | Comprehensiveness faithfulness との比較 |

---

## ファイル構成

```
.
├── draft.md                           # 研究論文草稿（日本語）
├── draft_en.md                        # 研究論文草稿（英語）
├── memo.md                            # 査読対応メモ
│
└── experiments/
    ├── run.py                         # 統合エントリポイント（--config で全実験対応）
    ├── run_cartpole.py                # CartPole 実験
    ├── run_gridworld.py               # GridWorld 実験
    ├── run_gravity.py                 # CartPole 重力シフト実験
    ├── run_comparison.py              # モデル比較実験
    ├── run_mujoco.py                  # MuJoCo / LunarLander 実験
    ├── run_distill_sensitivity.py     # 蒸留感度実験
    ├── shap_analysis.py               # SHAP 分析
    ├── make_figures.py                # 図生成（結果から再生成、再実験不要）
    │
    ├── configs/                       # 実験設定ファイル
    │   ├── exp001_cartpole_noise.yaml
    │   ├── exp002_spurious_gridworld.yaml
    │   ├── exp003_cartpole_gravity.yaml
    │   ├── exp004_cartpole_comparison.yaml
    │   ├── exp005_gridworld_comparison.yaml
    │   ├── exp006_distill_sensitivity.yaml
    │   ├── exp007_lunarlander.yaml
    │   ├── exp008_hopper.yaml
    │   └── ...
    │
    ├── src/
    │   ├── cartpole_env.py            # CartPole 拡張環境（ノイズ特徴付加）
    │   ├── gravity_env.py             # CartPole 重力シフト環境
    │   ├── gridworld_env.py           # Spurious GridWorld 環境
    │   ├── lunar_env.py               # LunarLander 環境ラッパー
    │   ├── hopper_env.py              # MuJoCo Hopper 環境ラッパー
    │   ├── moet.py                    # Soft MoET 実装
    │   ├── distill.py                 # 蒸留学習（共通）
    │   ├── evaluate.py                # 評価指標（AA・J_S・R²・ε-agreement）
    │   └── baselines.py               # Comprehensiveness faithfulness など
    │
    └── results/                       # 実験結果（seed 別 zip・npy・csv）
        ├── exp001_cartpole_noise/
        ├── exp002_spurious_gridworld/
        ├── exp003_cartpole_gravity/
        ├── ...
        └── pvalue_summary.csv         # 統計検定まとめ
```

---

## セットアップ

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

pip install gymnasium stable-baselines3 scikit-learn numpy pandas matplotlib torch pyyaml shap mujoco
```

---

## 実験の実行

```bash
# 統合インタフェース（推奨）
python experiments/run.py --config experiments/configs/exp001_cartpole_noise.yaml

# 個別スクリプト
python experiments/run_cartpole.py --config experiments/configs/exp001_cartpole_noise.yaml
python experiments/run_gridworld.py --config experiments/configs/exp002_spurious_gridworld.yaml
python experiments/run_gravity.py   --config experiments/configs/exp003_cartpole_gravity.yaml

# 図の再生成（既存結果から、再実験不要）
python experiments/make_figures.py
```

---

## 主要な実験結果

### 実験2（Spurious GridWorld p=0.0）：「高 AA・低不変性」の実証

reversed\_c 条件での核心的な観測：

| 評価条件 | AA | J_oracle | J_surrogate |
|---------|-----|----------|-------------|
| train | 0.988 ± 0.011 | — | — |
| reversed\_c | **0.942** (95% CI: [0.902, 0.982]) | **−1.000** | **−1.000** |

AA=0.942 を維持したまま方策性能が完全崩壊。Surrogate model が Oracle policy のスプリアス依存（$c$ 依存）をそのまま複製した結果。train vs reversed\_c の AA 差は $p_\text{adj}=0.030$（$d=1.14$、Holm–Bonferroni 補正）で有意だが、CI 下限は診断閾値 $\theta_{\rm AA}=0.9$ をわずか 0.002 上回るのみ。$n=10$ での検出力は約 0.55〜0.65。

### 実験3（CartPole 重力シフト）：対照実験

非スプリアス環境では重力変化後も $J_S$ の壊滅的崩壊は観測されず、AA の低下のみ（pole\_long 条件で有意、$p_\text{adj}=0.0004$, $d=2.65$）。実験2との対照が枠組みの有効性を支持する。

### SHAP との比較（実験9）

同一の Oracle policy に SHAP（KernelExplainer）を適用すると、スプリアス特徴 $c$ の重要度は train と reversed\_c で完全に同値（Mean |SHAP| = 0.0181 vs 0.0178）。本枠組みの不変性評価は SHAP が検出できない「依存の有効性」を補完的に診断する。

---

## 関連手法との差別化

| 手法 | 目的 | 本研究との違い |
|------|------|--------------|
| MoET（Vasic et al., 2019） | policy を精度よく近似する | Surrogate 実装の一候補。本研究は「いつ崩壊するか」の診断枠組み |
| LIME / SHAP | 個別インスタンスをローカルに説明する | 訓練分布内の依存のみ可視化。分布シフト後の有効性は不問 |
| IRM（Arjovsky et al., 2019） | 訓練時にスプリアス依存を排除する | 訓練戦略の変更が必要。本枠組みは学習済みモデルへの事後的適用 |
| Comprehensiveness faithfulness | 特徴重要度の忠実性評価 | 訓練分布内の評価。分布外での依存維持は評価しない |
