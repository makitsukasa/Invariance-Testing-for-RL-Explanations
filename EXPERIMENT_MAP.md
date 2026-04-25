# EXPERIMENT_MAP.md

実験インデックス。詳細は各 `experiments/results/expNNN_*/README.md` を参照。

---

## 実験一覧

| ID | 概要 | ステータス | results |
|----|------|-----------|---------|
| exp001 | SHAP 自動選択（GridWorld 3特徴） | 完了 60% | [→](experiments/results/exp001_shap_gridworld/) |
| exp002 | 介入テスト自動選択（GridWorld 3特徴） | 完了 100% | [→](experiments/results/exp002_intervention_gridworld/) |
| exp003 | 介入テスト（LunarLander 9特徴） | 失敗・中止 | [→](experiments/results/exp003_intervention_lunar/) |
| exp004 | 介入テスト（GridWorld + noise 10特徴） | 完了 100% | [→](experiments/results/exp004_noise_gridworld/) |
| exp005 | spurious_p sweep + end-to-end（介入→Stage2） | 完了 p≤0.2で100% | [→](experiments/results/exp005_psweep_gridworld/) |

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
