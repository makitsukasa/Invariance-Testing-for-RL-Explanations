# 構造制約ボトルネックに基づく強化学習方策の説明可能性境界の分析

強化学習（RL）の説明可能性を「内部の可視化」ではなく **「構造制約下での意思決定の再現可能性」** として定義し、その成立条件・崩壊条件を実験的に診断するプロジェクト。

---

## 研究概要

既存の XRL（説明可能強化学習）研究は「どう説明するか」という手法の提案に終始しており、説明が元の意思決定と真に整合しているか（faithfulness）を評価する枠組みが十分でない。

本研究は以下を提案する：

- **Intuitive policy**：ブラックボックスな RL policy（DQN）
- **Reasoned model**：構造制約付き蒸留モデル（本実装では MoET）
- **説明可能性の定義**：再現性（Reasoned が Intuitive の行動を再現できるか）と不変性（分布シフト下でも再現が維持されるか）の二軸で診断する

### 診断枠組み

| | 不変性：高 | 不変性：低 |
|---|---|---|
| **再現性：高** | 現在の情報では最も強い説明候補 | spurious な依存を忠実に写している疑いが強い |
| **再現性：低** | 粗すぎる surrogate、または capacity 不足 | 説明として弱い |

この分類は確定的な判定基準ではなく、観測された分布の範囲での整合性を診断するものである。不変性が高いことは因果的な正当性を保証しない。

---

## 実験構成

| | 実験1 (CartPole) | 実験2 (GridWorld) |
|---|---|---|
| エントリポイント | `run_cartpole.py` | `run_gridworld.py` |
| 環境 | `src/cartpole_env.py` | `src/gridworld_env.py` |
| eval 条件 | 1条件（train のみ） | 3条件（train / random\_c / reversed\_c） |
| MoET / distill | 共通 | 共通 |
| 設定ファイル | `configs/exp001_cartpole_noise.yaml` | `configs/exp002_spurious_gridworld.yaml` |

---

## ファイル構成

```
.
├── draft.md                          # 研究論文草稿
├── memo.md                           # アイデアメモ・査読フィードバック・先行研究リスト
│
└── experiments/
    ├── run_cartpole.py               # 実験1 エントリポイント
    ├── run_gridworld.py              # 実験2 エントリポイント
    ├── shap_analysis.py              # SHAP分析（GridWorld対象）
    ├── visualize.py                  # 可視化スクリプト（再実験不要）
    │
    ├── configs/
    │   ├── exp001_cartpole_noise.yaml
    │   └── exp002_spurious_gridworld.yaml
    │
    ├── src/
    │   ├── cartpole_env.py           # CartPole 拡張環境（ノイズ特徴付加）
    │   ├── cartpole_intuitive.py     # DQN 学習・評価・データ収集（CartPole）
    │   ├── gridworld_env.py          # Spurious GridWorld 環境
    │   ├── moet.py                   # Soft MoET 実装（共通）
    │   ├── distill.py                # 蒸留学習（共通）
    │   └── evaluate.py              # 評価指標（共通）
    │
    └── results/
        ├── exp001_cartpole_noise/    # 実験1 結果
        └── exp002_spurious_gridworld/ # 実験2 結果（SHAP結果含む）
```

---

## セットアップ

```bash
# Python 仮想環境（プロジェクトルート直下）
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # Mac/Linux

pip install gymnasium stable-baselines3 scikit-learn numpy pandas matplotlib torch pyyaml shap
```

---

## 実験の実行

```bash
# 実験1：CartPole ノイズ拡張
python experiments/run_cartpole.py --config experiments/configs/exp001_cartpole_noise.yaml

# 実験2：Spurious GridWorld
python experiments/run_gridworld.py --config experiments/configs/exp002_spurious_gridworld.yaml

# SHAP分析（実験2の結果が必要）
python experiments/shap_analysis.py

# 可視化（既存結果から図を生成、再実験不要）
python experiments/visualize.py --exp all   # 両方
python experiments/visualize.py --exp exp001
python experiments/visualize.py --exp exp002
```

新しい条件で実験を追加するときは `configs/exp003_xxx.yaml` を作成し、対応する runner を実行する。

---

## 主要な実験結果

### 実験1：CartPole（非相関スプリアス）

ノイズ次元数 N を増やすと、MoET の深さを深めても行動一致率（AA）の上限が低下する。
N=0 では depth=5 で AA≈0.91 に達するが、N=16 では 0.80 付近で頭打ちになる。
これは診断枠組みでいう「再現性低」状態への移行であり、説明可能性が入力の複雑さにも依存することを示す。

### 実験2：GridWorld（相関スプリアスと分布シフト）

p=0.0（完全相関）・reversed\_c 条件において：

| 評価条件 | AA | J_intuitive | J_reasoned |
|---------|-----|-------------|------------|
| train | 0.985 | 0.971 | 0.969 |
| reversed\_c | **0.954** | **−1.000** | **−1.000** |

**AA=0.95 かつ J=−1.000** — 診断枠組みでいう「再現性高 × 不変性低」に相当する。MoET は Intuitive のスプリアス依存を忠実に再現し、両者とも等しく完全に失敗した。これが本研究の核心的観察である「再現できるが間違っている」ケースの数値的証拠。

### SHAP との比較

同じ Intuitive policy に SHAP（KernelExplainer）を適用すると、スプリアス特徴 c の重要度は train / reversed\_c 条件で完全に同値（Mean |SHAP| = 0.0181）となる。SHAP は「方策が c を使っている」という事実は示すが、分布シフト後に依存が無効化されるという事実は検出できない。本研究の枠組みはこの隙間を補完する。

---

## 関連手法との差別化

| 手法 | 目的 | 本研究との違い |
|------|------|--------------|
| MoET（Vasic et al., 2019） | policy を精度よく近似する | MoET は Reasoned model の実装候補。本研究の問いは「いつ崩壊するか」の診断 |
| CBM | 事前定義した概念を経由させる | 概念ラベル不要。構造制約のみ |
| Information Bottleneck | 情報を最小限に圧縮する | 圧縮≠説明可能。決定の保存を診断 |
| LIME / SHAP | 個別インスタンスをローカルに説明する | 分布シフト下での依存の有効性を検出できない。本研究はその補完 |
