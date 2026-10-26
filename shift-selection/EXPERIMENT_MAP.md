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
| exp017 | SHAP vs Δ p sweep（ColoredMNIST IRM、30シード版） | 完了 Δ=102/120（85%）, SHAP=120/120（100%）, McNemar p=0.0001 | **推定 20時間49分**（推定6:52:59 + 実測13:56:41） | [→](experiments/results/exp017_cmnist_shap_psweep_30seeds/) |
| exp018 | Waterbirds（実世界スプリアス相関、30シード版） | 完了 Δ=18/30（60%）, SHAP=30/30（100%）, McNemar p=0.0005 | **13時間32分** | [→](experiments/results/exp018_waterbirds_30seeds/) |
| exp019 | Waterbirds後処理（WGA再算出; exp018結果を入力に再集計） | 完了（mean worst_group_acc=0.3424, std=0.0804） | 5時間20分（30 seeds、3並列） | [→](experiments/results/exp019_waterbirds_wga/) |
| exp020 | Waterbirds マスク摂動 sensitivity（膨張/縮小で Δ の頑健性評価） | 完了（seed=0、decision flips 0/5） | **14時間04分** | [→](experiments/results/exp020_waterbirds_mask_sensitivity/) |
| exp021 | Waterbirds 追加ベースライン（Spurious Score proxy + PCA spuriousness proxy） | 完了（bg_score > fg_score = 30/30, pca_ok = 30/30） | **54.8分** | [→](experiments/results/exp021_waterbirds_specialized_baseline/) |
| exp022 | Waterbirds GrabCut sensitivity（mask 摂動による Δ の頑健性評価） | 完了（mask 安定性を 30 シードで評価） | **1時間08分10秒** | [→](experiments/results/exp022_waterbirds_grabcut_sensitivity/) |
| exp023 | 自動候補発見（GridWorld, 5 seeds） | 完了（linear_probe_drop 80%, tree_probe_drop 60%, mutual_info 40%, random 20% の top-1） | **1分55秒** | [→](experiments/results/exp023_gridworld_candidate_discovery/) |
| exp024 | 自動候補発見の `spurious_p` / noise sweep（GridWorld, 45 tasks） | 完了（低 `spurious_p` では probe 系が強く、`spurious_p` 上昇で top-1 回収率が低下） | **13分36秒** | [→](experiments/results/exp024_gridworld_candidate_discovery_noise_p_sweep/) |
| exp025 | Waterbirds 候補発見 sweep（`n_eval` × mask radius, exp018/022 再利用） | 完了（候補発見は background をほぼ常に top-1 に置くが、Delta 確認との整合は radius 依存） | **30分25秒** | [→](experiments/results/exp025_waterbirds_candidate_discovery_sweep/) |
| exp026 | Waterbirds 候補発見（CLIP / SSL 表現ベース） | 完了（CLIP は background を 100% top-1、SSL は foreground を 100% top-1 に選択） | **57分32秒** | [→](experiments/results/exp026_waterbirds_clip_ssl_candidate_discovery/) |
| exp027 | 自動候補発見の `spurious_p` / noise sweep（GridWorld, 30 seeds） | 完了（`linear_probe_drop` が最も安定して強く、top-k は多くの条件で高水準） | **74分30秒** | [→](experiments/results/exp027_gridworld_candidate_discovery_noise_p_sweep_30seeds/) |
| exp028 | Waterbirds 候補発見（CLIP / 自己教師あり表現, 30 seeds） | 完了（CLIP は background を 100% top-1、自己教師あり表現は foreground を 100% top-1 に選択） | **170分54秒** | [→](experiments/results/exp028_waterbirds_clip_ssl_candidate_discovery_30seeds/) |
| exp029 | SHAP と Δ を同じモデルで計算する 2×2（GridWorld 10次元、オラクル・サロゲート、30シード） | 完了 同じサロゲート上 Δ=85/120・SHAP=43/120、同じオラクル上 Δ=108/120・SHAP=54/120（McNemar とも p<0.0001）。exp011・exp016 の SHAP 集約の誤りを確認 | **54分05秒**（120 runs、4並列） | [→](experiments/results/exp029_shap_delta_same_model/) |
| exp030 | シフト対象の選定と診断手順全体の検証（GridWorld 10次元、環境側の分布シフト 20 条件、30シード） | 完了 H1（Δ サロゲートの hit@1=87/117、ランダム期待値 21.6）・H2（手順全体の成功=11/120、期待値 1.4）とも支持。ただし Δ がランダムを上回るのは p≤0.2、手順全体の検出率は 9%（段階1と AA>0.9 の条件による） | **3時間07分54秒**（120 runs、4並列） | [→](experiments/results/exp030_shift_target_validation/) |
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
| `run_cmnist_shap_psweep.py` | `exp012_cmnist_shap_psweep` / `exp017_cmnist_shap_psweep_30seeds`    |
| `run_waterbirds.py`         | `exp013_waterbirds` / `exp018_waterbirds_30seeds`                    |
| `run_waterbirds_mask_sensitivity.py` | `exp020_waterbirds_mask_sensitivity` |
| `run_waterbirds_specialized_scores.py` | `exp021_waterbirds_specialized_scores` |
| `run_waterbirds_specialized_baseline.py` | `exp021_waterbirds_specialized_scores` |
| `run_waterbirds_grabcut_sensitivity.py` | `exp022_waterbirds_grabcut_sensitivity` |
| `run_gridworld_candidate_discovery.py` | `exp023_gridworld_candidate_discovery` |
| `run_gridworld_candidate_discovery_noise_p_sweep.py` | `exp024_gridworld_candidate_discovery_noise_p_sweep` |
| `run_waterbirds_candidate_discovery_sweep.py` | `exp025_waterbirds_candidate_discovery_sweep` |
| `run_waterbirds_representation_candidate_discovery.py` | `exp026_waterbirds_clip_ssl_candidate_discovery` |
| `run_gridworld_candidate_discovery_noise_p_sweep.py` | `exp027_gridworld_candidate_discovery_noise_p_sweep_30seeds` |
| `run_waterbirds_representation_candidate_discovery.py` | `exp028_waterbirds_clip_ssl_candidate_discovery_30seeds` |
| `run_shap_delta_2x2.py`     | `exp029_shap_delta_same_model` |
| `run_shift_target_validation.py` | `exp030_shift_target_validation` |
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
| 6. Discussion | 相補性・適用条件・一般化可能性 | exp016, exp017, exp018, exp021, exp023, exp024, exp025, exp026, exp027, exp028 |
| 7. Limitations | 介入質依存、候補特徴前提、LunarLander負例 | exp006, exp007, exp020, exp022 |
| Appendix: Negative Results | LunarLanderの失敗例詳細 | exp003, exp006, exp007 |
| Appendix: Statistical Tests | Wilson CI, McNemar,補助表 | exp016, exp017, exp018, exp019 |
