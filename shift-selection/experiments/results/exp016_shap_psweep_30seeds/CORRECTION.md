# 訂正（2026-10-25）

この実験の SHAP の列（`results.csv` の `shap_*`、`shap_selected`、`shap_correct`）と、それに基づく SHAP の検出率・McNemar 検定・図は、`run_shap_psweep.py` の集約の誤り（`reshape(-1, n_features)` が特徴の軸と行動の軸を混ぜる）による値です。「c (spurious)」とラベルされた列には c の寄与が入っていません。

- Δ の列、AA、J_S_train は正しい値です（exp029 が 120 件すべてで完全に再現しました）。
- SHAP は Q 値をオラクル（DQN）で、Δ はサロゲート（SoftMoET）で計算しています。両者は同じ seed ですが、同じモデルではありません。
- 正しく集約した SHAP と、同じモデル上での Δ との比較は exp029（`../exp029_shap_delta_same_model/`）にあります。

元の結果ファイルは変更していません。訂正の内容と影響範囲は `shift-selection/ERRATA.md` の 1 節にあります。
