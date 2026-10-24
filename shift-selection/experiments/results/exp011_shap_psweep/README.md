# exp011: SHAP vs 介入テスト Δ の p-sweep 比較

## 設定

| 項目 | 値 |
|------|----|
| 環境 | SpuriousGridWorld（10次元: x, y, c + noise×7） |
| p_values | [0.0, 0.1, 0.2, 0.3] |
| seeds | [42, 123, 456, 789, 0] |
| Oracle | DQN 50,000 steps |
| Surrogate | SoftMoET (4 experts, depth=5, 100 epochs) |
| SHAP | KernelExplainer (bg=100, eval=300, nsamples=100) |
| Δ | 介入テスト（n_episodes=200 × 10 features） |
| script | `experiments/run_shap_psweep.py` |
| config | `experiments/configs/exp011_shap_psweep.yaml` |

## 結果

| p | Δ 検出率 | SHAP 検出率 |
|---|---------|------------|
| 0.0 | **5/5 (100%)** | 0/5 (0%) |
| 0.1 | **5/5 (100%)** | 1/5 (20%) |
| 0.2 | **5/5 (100%)** | 1/5 (20%) |
| 0.3 | 1/5 (20%) | 0/5 (0%) |

## Per-seed 詳細

| p | seed | Δ selected | Δ_c | SHAP selected | SHAP_c |
|---|------|-----------|-----|--------------|--------|
| 0.0 | 0 | c (spurious) OK | 0.522 | agent_y NG | 0.0207 |
| 0.0 | 42 | c (spurious) OK | 0.520 | agent_y NG | 0.0222 |
| 0.0 | 123 | c (spurious) OK | 0.483 | agent_y NG | 0.0166 |
| 0.0 | 456 | c (spurious) OK | 0.545 | agent_y NG | 0.0206 |
| 0.0 | 789 | c (spurious) OK | 0.573 | agent_y NG | 0.0210 |
| 0.1 | 0 | c (spurious) OK | 0.295 | agent_y NG | 0.0083 |
| 0.1 | 42 | c (spurious) OK | 0.219 | agent_x NG | 0.0116 |
| 0.1 | 123 | c (spurious) OK | 0.201 | c (spurious) OK | 0.0188 |
| 0.1 | 456 | c (spurious) OK | 0.145 | agent_x NG | 0.0139 |
| 0.1 | 789 | c (spurious) OK | 0.220 | noise_0 NG | 0.0070 |
| 0.2 | 0 | c (spurious) OK | 0.314 | noise_1 NG | 0.0054 |
| 0.2 | 42 | c (spurious) OK | 0.236 | agent_y NG | 0.0074 |
| 0.2 | 123 | c (spurious) OK | 0.273 | noise_2 NG | 0.0083 |
| 0.2 | 456 | c (spurious) OK | 0.312 | c (spurious) OK | 0.0120 |
| 0.2 | 789 | c (spurious) OK | 0.221 | agent_x NG | 0.0084 |
| 0.3 | 0 | noise_2 NG | 0.142 | noise_1 NG | 0.0045 |
| 0.3 | 42 | agent_x NG | -0.034 | noise_2 NG | 0.0022 |
| 0.3 | 123 | c (spurious) OK | 0.348 | noise_2 NG | 0.0084 |
| 0.3 | 456 | agent_y NG | 0.034 | noise_2 NG | 0.0043 |
| 0.3 | 789 | noise_6 NG | 0.052 | agent_y NG | 0.0028 |

## 考察

**p ≤ 0.2**: Δ は全 15/15 で c (spurious) を正しく特定。SHAP は 2/15（13%）。

**SHAP の失敗傾向**: p=0.0 では 5/5 すべてで agent_y を最重要と判定。SHAP は Q 値への限界的寄与を測定するため、位置特徴（エージェント移動に直接関わる）を優先しやすく、spurious 相関を持つ c を見落とす。

**p=0.3 での Δ 劣化**: surrogate の AA が 0.76–0.87 と低く（exp005 での p≤0.2 では全 PASS）、J_S_train がほぼゼロに近いケースが複数。oracle 自体が c をほぼ無視するため Δ_c が小さくなり、ノイズ特徴との識別が難しくなる。これは手法の限界ではなく、oracle が c に依存しない設定での合理的な挙動。

**p=0.3 での Δ の SHAP に対する優位性**: どちらも検出できないが、Δ は 1/5 成功（seed=123: Δ_c=0.348）に対し SHAP は 0/5。

## 結論

p ≤ 0.2 の実験設定において、Δ（介入テスト）は SHAP KernelExplainer を大幅に上回る検出率（100% vs 13%）を示した。
