# exp013: Waterbirds 実世界スプリアス相関（Δ vs SHAP）

## 設定

| 項目 | 値 |
|------|----|
| データセット | waterbird_complete95_forest2water2（水鳥+水背景 95%、陸鳥+陸背景 95%） |
| Oracle | 凍結 ResNet-18（ImageNet 事前学習）+ Linear(512, 2)、10 エポック fine-tune |
| 介入（背景） | GrabCut マスクによる background_replace（bg_pool = 訓練データから 200 枚） |
| 介入（前景） | foreground_noise（std=0.3、GrabCut 前景マスクへの加算ノイズ） |
| SHAP | GradientExplainer（bg=50、eval=100）、GrabCut マスクで fg/bg 帰属を集計 |
| n_eval | 300 |
| seeds | [42, 123, 456, 789, 0] |
| n_workers | 2（threads_per_worker=4） |
| 実行時間 | 約 2.5 時間 |
| script | `experiments/run_waterbirds.py` |
| config | `experiments/configs/exp013_waterbirds.yaml` |

## 結果

| seed | val_acc | delta_bg | delta_fg | Δ判定 | shap_bg | shap_fg | SHAP判定 |
|------|---------|----------|----------|-------|---------|---------|---------|
| 0    | 0.822   | 0.100    | 0.078    | OK    | 0.8942  | 0.1058  | OK      |
| 42   | 0.786   | 0.094    | 0.084    | OK    | 0.8604  | 0.1396  | OK      |
| 123  | 0.759   | 0.122    | 0.094    | OK    | 0.8562  | 0.1438  | OK      |
| 456  | 0.796   | 0.116    | 0.091    | OK    | 0.8620  | 0.1380  | OK      |
| 789  | 0.776   | 0.122    | 0.075    | OK    | 0.8709  | 0.1291  | OK      |

**Δ 5/5 (100%)、SHAP 5/5 (100%)**

## 考察

GridWorld（Δ 80% / SHAP 10%）・ColoredMNIST（同率だが SHAP はアーティファクト）と異なり、
Waterbirds は両手法とも 100% 正解。

理由: スプリアス相関が非常に強く（95%）、背景特徴が視覚的に顕著であるため、
SHAP の gradient-based 帰属でも背景への依存を捉えられる。

SHAP 帰属の内訳（shap_bg ≈ 0.86–0.89）は、予測の 86–89% が背景ピクセルに帰属していることを示しており、
Δ（delta_bg > delta_fg）の結論と一致する。

## 結論

実世界のスプリアスベンチマークでも Δ テストは機能することを確認。
両手法が一致するケースとして、「スプリアス相関が強く特徴が視覚的に顕著な場合」を論文に位置づける。
GridWorld / ColoredMNIST での SHAP 失敗（特に exp011 での 10%）との対比で、
Δ の優位性が現れやすい条件を浮き彫りにする。
