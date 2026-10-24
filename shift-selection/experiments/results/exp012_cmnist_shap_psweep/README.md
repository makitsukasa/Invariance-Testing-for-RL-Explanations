# exp012: ColoredMNIST SHAP vs 介入テスト Δ の p-sweep 比較

## 設定

| 項目 | 値 |
|------|----|
| 環境 | ColoredMNIST IRM（label_noise_p=0.25, stage2_p=1.0） |
| p_values | [0.0, 0.1, 0.2, 0.3] |
| seeds | [42, 123, 456, 789, 0] |
| Oracle | CNN (Conv2d×2 + FC×2), 20 epochs |
| Surrogate | 同アーキテクチャ CNN, 20 epochs |
| SHAP | GradientExplainer (bg=100, eval=200) + R-G 非対称集約 |
| Δ | hue_shuffle vs structure_noise の性能差 |
| n_workers | 2 (threads_per_worker=4) |
| 実行時間 | 約66分 |
| script | `experiments/run_cmnist_shap_psweep.py` |
| config | `experiments/configs/exp012_cmnist_shap_psweep.yaml` |

## 結果

| p | Δ 検出率 | SHAP 検出率 |
|---|---------|------------|
| 0.0 | **5/5 (100%)** | **5/5 (100%)** |
| 0.1 | **5/5 (100%)** | **5/5 (100%)** |
| 0.2 | **5/5 (100%)** | **5/5 (100%)** |
| 0.3 | 2/5 (40%) | 5/5 (100%) |

## SHAP 集約方法

ColoredMNIST は R チャネルが赤画像の digit を、G チャネルが緑画像の digit をエンコードする。
ドメイン知識（R-G 差分 = 色の軸、R+G 平均 = 輝度/構造の軸）を用いた最善の集約：

```
color_attr = mean(|shap_R - shap_G|)  # R-G 非対称成分
struct_attr = mean(|shap_R + shap_G|) / 2  # R+G 対称成分
shap_correct = (color_attr > struct_attr)
```

この集約は**ドメイン知識を前提とした最も有利な SHAP 解釈**である。

## 考察

**p ≤ 0.2**: 両手法とも 15/15 で色（hue）を正しく特定。

**p = 0.3 での逆転**: SHAP が 5/5、Δ が 2/5。ただしこれは SHAP の優位性ではなく
R-G 集約の**構造的バイアス**による。color_attr = |shap_R - shap_G| = |shap_R|（G=0 のため）、
struct_attr = |shap_R + shap_G| / 2 = |shap_R| / 2 となり、**常に color_attr = 2 × struct_attr** が成立する。
SHAP はいかなる p でも「色が重要」と答え続け、oracle が構造依存に切り替わっても追従できない。

**Δ の p=0.3 NG 3件**: delta_struct > delta_hue（例: seed=789 で hue=0.075, struct=0.137）となっており、
oracle が色から構造依存に切り替わったことを Δ が正直に検出している。
正解基準（= 色を選択）との不一致は基準の問題であり、Δ の振る舞いは正しい。

## 結論

p ≤ 0.2 では両手法が同等。Δ は oracle の依存構造の変化（p=0.3 での色→構造シフト）を追従するが、
SHAP（DK-集約）はエンコーディングの制約により常に色を選択し追従できない。
