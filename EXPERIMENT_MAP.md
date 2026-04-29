# EXPERIMENT_MAP.md

実験インデックス。詳細は各 `experiments/results/expNNN_*/README.md` を参照。

---

## 実験一覧

| ID | 概要 | ステータス | 実行時間 | results |
|----|------|-----------|---------|---------|
| exp001 | SHAP 自動選択（GridWorld 3特徴） | 完了 60% | 不明 | [→](experiments/results/exp001_shap_gridworld/) |
| exp002 | 介入テスト自動選択（GridWorld 3特徴） | 完了 100% | 不明 | [→](experiments/results/exp002_intervention_gridworld/) |
| exp003 | 介入テスト（LunarLander 9特徴） | 失敗・中止 | 不明 | [→](experiments/results/exp003_intervention_lunar/) |
| exp004 | 介入テスト（GridWorld + noise 10特徴） | 完了 100% | 不明 | [→](experiments/results/exp004_noise_gridworld/) |
| exp005 | spurious_p sweep + end-to-end（介入→Stage2） | 完了 p≤0.2で100% | 不明 | [→](experiments/results/exp005_psweep_gridworld/) |
| exp006 | LunarLander PPO + gamma=0.999（差分 shaping あり） | 失敗・中止（Stage2 collapse なし） | 不明 | [→](experiments/results/exp006_ppo_lunar/) |
| exp007 | LunarLander アブレーション v2（差分 shaping 除去 + zone_bonus sweep） | 失敗・中止（oracle が c を使わない） | **4時間10分**（21分/batch、4並列、torch.set_num_threads(2)） | [→](experiments/results/exp007_ablation_lunar/) |
| exp008 | ColoredMNIST + CNN surrogate 基本動作確認（spurious_p=0.0） | 完了 5/5 | 不明（未実測） | [→](experiments/results/exp008_colored_mnist/) |
| exp009 | ColoredMNIST p sweep（ラベルノイズなし） | 失敗・p=0.0 のみ成功 | **約45分**（20 runs） | [→](experiments/results/exp009_cmnist_psweep/) |
| exp010 | ColoredMNIST IRM 設定 p sweep（label_noise_p=0.25） | 完了 p≤0.1で5/5、p=0.2で4/5、p=0.3で3/5 | **約45分**（20 runs） | [→](experiments/results/exp010_cmnist_irm_psweep/) |
| exp011 | SHAP vs Δ p sweep（GridWorld 10次元、同一 oracle・seed） | 完了 Δ p≤0.2で15/15、SHAP 2/15 | **実測未記録** | [→](experiments/results/exp011_shap_psweep/) |
| exp012 | SHAP vs Δ p sweep（ColoredMNIST IRM、同一 oracle・seed） | 完了 p≤0.2で両者15/15、p=0.3でΔ 2/5・SHAP 5/5（バイアスによる） | **約66分**（20 runs、2並列） | [→](experiments/results/exp012_cmnist_shap_psweep/) |
| exp013 | Waterbirds（実世界スプリアス相関、ResNet-18 + GrabCut） | 完了 Δ 5/5・SHAP 5/5（両者100%） | **約2.5時間**（5 seeds、2並列） | [→](experiments/results/exp013_waterbirds/) |
| exp016 | SHAP vs Δ p sweep 30シード版（GridWorld 10次元、同一 oracle・seed） | 完了（30シード再実験） | **不明（未記録）** | [→](experiments/results/exp016_shap_psweep_30seeds/) |

---

## 実験完了後の更新チェックリスト

新しい実験を追加・完了させるたびに以下を更新する。

| ドキュメント | 更新内容 |
|-------------|---------|
| `EXPERIMENT_MAP.md`（このファイル） | 実験一覧の行を追加・ステータス更新・実行時間記入、スクリプト対応表に追記 |
| `experiments/results/expNNN_*/README.md` | 設定・結果・失敗原因を記録（実験開始前に雛形作成、完了後に結果を埋める） |
| `review_log.md` | 査読コメントに対応する進捗（未着手/進行中/完了）を更新 |

---

## 命名規則

- `expNNN_<説明>` の連番で管理する
- 設定変更・再実験は新番号を振る（上書きしない）
- 廃棄した実験も番号は欠番にせずここに残す

## スクリプトと config の対応

| script | 対応 config prefix |
|--------|-------------------|
| `run_shap_pilot.py`         | `exp001_shap_gridworld`         |
| `run_intervention_pilot.py` | `exp002_intervention_gridworld` |
| `run_lunar_pilot.py`        | `exp003_intervention_lunar`     |
| `run_gridworld_noise.py`    | `exp004_noise_gridworld`        |
| `run_gridworld_psweep.py`   | `exp005_psweep_gridworld`       |
| `run_lunar_ppo.py`          | `exp006_ppo_lunar`              |
| `run_lunar_ablation.py`     | `exp007_ablation_lunar`         |
| `run_colored_mnist.py`      | `exp008_colored_mnist`          |
| `run_cmnist_psweep.py`      | `exp009_cmnist_psweep` / `exp010_cmnist_irm_psweep`（引数で切り替え） |
| `run_shap_psweep.py`        | `exp011_shap_psweep` / `exp016_shap_psweep_30seeds`                  |
| `run_cmnist_shap_psweep.py` | `exp012_cmnist_shap_psweep`                                           |
| `run_waterbirds.py`         | `exp013_waterbirds`                                                   |

---

## 実験と論文章の対応

| 論文章 | 目的 | 対応実験 |
|-------|------|---------|
| Abstract / 1. Introduction | 主結果の要約（Δ と SHAP の比較、適用範囲） | exp016, exp017, exp018（完了後） |
| 2. Related Work | 直接対応実験なし（文献整理） | なし |
| 3. Method | 介入演算子の定義・設計の妥当性、判定規則 | exp002, exp004, exp016, exp017, exp018 |
| 4. Experimental Setup | 各ベンチマーク設定、シード、実装条件 | exp016, exp017, exp018 |
| 5. Results: GridWorld | Δ vs SHAP の主要比較（p-sweep, top-k） | exp016（+比較参照 exp011） |
| 5. Results: ColoredMNIST | IRM設定での比較、構造的アーティファクト分析 | exp017（+既存参照 exp012） |
| 5. Results: Waterbirds | 実世界スプリアス相関での比較（scatter / group） | exp018（+既存参照 exp013） |
| 6. Discussion | 相補性・適用条件・一般化可能性 | exp016, exp017, exp018 |
| 7. Limitations | 介入質依存、候補特徴前提、LunarLander負例 | exp006, exp007 |
| Appendix: Negative Results | LunarLanderの失敗例詳細 | exp003, exp006, exp007 |
| Appendix: Statistical Tests | Wilson CI, McNemar,補助表 | exp016, exp017, exp018 |
