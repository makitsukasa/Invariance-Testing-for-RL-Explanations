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

---

## 実験完了後の更新チェックリスト

新しい実験を追加・完了させるたびに以下を更新する。

| ドキュメント | 更新内容 |
|-------------|---------|
| `EXPERIMENT_MAP.md`（このファイル） | 実験一覧の行を追加・ステータス更新・実行時間記入、スクリプト対応表に追記 |
| `experiments/results/expNNN_*/README.md` | 設定・結果・失敗原因を記録（実験開始前に雛形作成、完了後に結果を埋める） |
| `memo.md` | `## 実験結果まとめ` に概要を追記（詳細は README に逃がす） |

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
