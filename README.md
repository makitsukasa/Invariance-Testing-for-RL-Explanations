# auto-spurious-discovery

> **このリポジトリは更新を終了しました。** 内容は全履歴ごと [Invariance-Testing-for-RL-Explanations](https://github.com/makitsukasa/Invariance-Testing-for-RL-Explanations) の `candidate-discovery/` に統合しました。

不変性テストに基づく説明評価で、それまで人が与えていた「検査する候補の特徴」を自動で見つける段階を扱おうとした試みです（2026-05-02）。構想は `vision.md` にあります。

## やったこと
- 正解付きの Spurious GridWorld で、候補を順位付けする手法（相互情報量、線形プローブ・決定木プローブの permutation importance、ランダム）が、c を 1 位に挙げるかを比べた（exp001・exp002）。詳細は `experiments/EXPERIMENT_MAP.md`。

## 分かったことと限界
- 決定木プローブの permutation importance が c を最もよく 1 位に挙げた（exp001 で 5/5 シード）。
- ただしこれは「候補の自動発見」ではなく、重要度の順位付けの比較である。この GridWorld ではゴールの手がかりが c しかないため、c が 1 位になることは、c がスプリアスであることを示さない。
- 構想にあった CLIP・自己教師あり表現による候補の抽出は、実施していない。
- 研究1の主張2（シフトすべき特徴は Δ で選べる）の、比較対象を増やした補強材料として使える。
