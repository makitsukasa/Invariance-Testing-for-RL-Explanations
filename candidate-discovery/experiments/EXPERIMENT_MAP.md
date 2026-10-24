# EXPERIMENT_MAP

このファイルは、実験の事実管理を集約するための入口です。
詳細は各 `experiments/results/expNNN_*/README.md` を参照。

## 実験一覧

| ID | 実験名 | 状態 | 実行時間 | 目的 | 結果メモ |
|---|---|---|---|---|---|
| exp001 | GridWorld candidate discovery | 完了 | 2026-05-02 21:11 - 21:13（実測 1分48秒, 5 seeds / 4 workers） | 正解付き小規模環境で、候補発見法が真のスプリアス特徴を上位回収し、PerformanceCheck に接続できるか確認する | 目的達成:候補発見法ごとの差を観測 |
| exp002 | GridWorld noise-p sweep | 完了 | 2026-05-02 22:26 - 22:38（実測 12分31秒, 45 tasks / 4 workers） | `spurious_p` と `n_noise` を振って、候補発見法の差がどの条件まで保たれるか確認する | 低 p では tree/linear が優位、高 p では全体に劣化 |

## ディレクトリ対応表

| ID | 実行スクリプト | 設定ファイル | 結果フォルダ |
|---|---|---|---|
| exp001 | `experiments/entrypoints/run_gridworld_candidate_discovery.py` | `experiments/configs/exp001_gridworld_candidate_discovery.yaml` | `experiments/results/exp001/` |
| exp002 | `experiments/entrypoints/run_gridworld_candidate_discovery_noise_p_sweep.py` | `experiments/configs/exp002_gridworld_noise_p_sweep.yaml` | `experiments/results/exp002/` |

---

## 実験と論文章の対応

| 論文章 | 目的 | 対応実験 |
|-------|------|---------|
