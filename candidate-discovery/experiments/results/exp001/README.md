# exp001: GridWorld candidate discovery

## 目的

正解付きの Spurious GridWorld 上で、自動候補発見法が真のスプリアス特徴 `c` を上位に回収できるかを確認する。
さらに、選ばれた候補を PerformanceCheck に接続したとき、性能低下候補として整合的に振る舞うかを確認する。

## 対応ファイル

- 実行スクリプト: `experiments/entrypoints/run_gridworld_candidate_discovery.py`
- 設定ファイル: `experiments/configs/exp001_gridworld_candidate_discovery.yaml`
- 部分結果: `experiments/results/exp001/results_partial.csv`
- 実行メタ情報: `experiments/results/exp001/meta.json`
- 実行セッション: `experiments/results/exp001/runtime_sessions.csv`
- seed ごとのログ: `experiments/results/exp001/seed_logs/`
- 学習済みモデル: `experiments/results/exp001/checkpoints/`

## 記録項目

- 実験設定
- 実行時間
- seed ごとの結果
- 中断後の再開有無
- `top-1 hit`, `top-k hit`, 真のスプリアス特徴の順位
- PerformanceCheck 側の `delta` との整合性
- 失敗原因
- 考察

## 現在の状態

完了

- 開始時刻: `2026-05-02 21:11:12`
- 完了時刻: `2026-05-02 21:13:01`
- 実行時間: `1分48秒`
- 出力先: `experiments/results/exp001/`
- 進捗管理: `meta.json`, `results_partial.csv`, `seed_logs/`

## 実行設定

- seeds: `[0, 42, 123, 456, 789]`
- workers: `4`
- oracle steps: `50000`
- distill samples: `10000`
- distill epochs: `100`
- estimated minutes per seed: `8.0`

## 結果要約

- 完了 seed 数: `5 / 5`
- `mutual_info`: top-1 hit `0%`, top-3 hit `100%`, mean rank `2.40`
- `linear_probe_drop`: top-1 hit `60%`, top-3 hit `100%`, mean rank `1.60`
- `tree_probe_drop`: top-1 hit `100%`, top-3 hit `100%`, mean rank `1.00`
- `random`: top-1 hit `20%`, top-3 hit `20%`, mean rank `5.60`

## 生成物

- `results.csv`
- `results_partial.csv`
- `summary.txt`
- `results.png`
- `meta.json`
- `runtime_sessions.csv`
- `run.log`
- `checkpoints/oracle/`
- `checkpoints/surrogate/`
- `seed_logs/`

## 短い考察

この最小実験では、正解付き小規模環境において候補発見法ごとの差が確認できた。
特に `tree_probe_drop` は真のスプリアス特徴 `c` を全 seed で top-1 回収しており、少なくとも通し実験の土台としては十分に機能している。

## 追記（2026-10-24）：注意

- top-3 hit は情報を持たない。観測は x・y・c とノイズ次元なので、c はほぼ必ず top-3 に入る。比べるなら top-1 hit と平均順位。
- `tree_probe_drop`・`linear_probe_drop` は、プローブの permutation importance で、研究1の Δ とほぼ同じ量である。この結果は「候補の自動発見」ではなく、「方策が頼っている特徴を、どの重要度の指標が 1 位に挙げるか」の比較として読む。p の向きと合わせて、exp002 の README の追記を参照。
