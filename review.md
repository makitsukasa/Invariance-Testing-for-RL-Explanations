# Peer Review: Detecting Spurious Features via Intervention-Based Performance Sensitivity

## 統合判定: Strong Reject（現状）/ Major Revision を経て resubmit 可

平均スコア: **(5+4+3)/3 = 4.0 / 10**

---

## Reviewer A: Methodology Expert（方法論専門家） — 5/10

### 強み
1. Δ テストの定式化が明快。`Δ_i = P(f, D) − P(f, T_i(D))` は再現可能な水準で記述されている。
2. ColoredMNIST における SHAP の構造的アーティファクト分析が独自性を持つ（`color_attr ≈ 2 × struct_attr` がデータ符号化から機械的に導かれる指摘）。
3. 適用境界（LunarLander 負例）を隠蔽せず記述する姿勢は誠実。

### 弱み
1. **介入演算子 T_i の理論的正当化が不足**: 周辺リサンプリングがスプリアス検出に妥当な理由、do-calculus や反事実的介入との関係が Method 節で未展開。Janzing [2020] を Related Work で引用しているのに Method 節で接続されていない。
2. **判定基準が二候補特徴間の相対比較に閉じている**: 事前にスプリアス候補を知っている前提を要求する設計で、Method 節でこの前提の妥当性を論じる必要がある。
3. **介入質の sensitivity analysis がない**: GrabCut マスク精度が Δ 値に直接影響するが定量化されていない。

### 修正提案
- Method 節に「介入演算子の妥当性条件」を新設し、他特徴の周辺分布保存・ターゲット特徴の情報破壊度を明示。
- 「未知のスプリアス特徴探索」設定への拡張（全特徴 Δ ランキング）を Discussion に追加するか、Abstract レベルで制約を先頭明示。
- Waterbirds で GrabCut の代替マスク（人手アノテーション、SAM 等）を 1 点追加比較。

---

## Reviewer B: Domain Expert（スプリアス相関・XAI 領域専門家） — 4/10

### 強み
1. Waterbirds への実世界寄り設定への展開（Δ_bg と Δ_fg を独立測定）は領域標準と整合。
2. ColoredMNIST IRM の符号化アーティファクト分析が XAI 評価プロトコルへの警鐘となる。
3. 診断（post-hoc）と訓練介入（IRM, GroupDRO）の distinction が明確。

### 弱み
1. **領域の主要ベースラインが欠落**: Spurious Score（Neuhaus et al., 2023）、Salient ImageNet（Singla 2022）、SpRAy（Lapuschkin et al., 2019）など SHAP 以外との比較が皆無。これだけで NeurIPS は Reject 圏。
2. **Waterbirds の worst-group accuracy が未記載**: Sagawa [2020] を引用しながら群別精度 4 群（landbird-land / landbird-water / waterbird-land / waterbird-water）を報告していない。average accuracy のみでは背景依存の有無が判別困難。
3. **LunarLander の扱いが弱い**: Abstract・Introduction・Conclusion で 4 度言及されるが方法論的洞察に発展していない。「discount-factor signal attenuation」という環境設計の問題が「Δ テストの適用境界」と混同されている。

### 修正提案
- Spurious Score または Salient ImageNet から最低 1 つを Waterbirds で追加比較（必須）。
- Waterbirds に worst-group accuracy を group-wise Table で報告。
- LunarLander 節を Appendix に移動、本文言及は Limitations のみに集約。「適用境界」の議論を理論的特徴付け（Δ の検出可能下限）に置き換え。

---

## Reviewer C: Statistics/Rigor Expert（統計・厳密性専門家） — 3/10

### 強み
1. 乱数シード管理を明示（numpy/PyTorch シード統一、サンプリング再現性）。
2. per-seed の生数値を Table で公開（ColoredMNIST p=0.3 の 5 シード分、Waterbirds 5 シード分）。
3. 相対比較（Δ_spurious > Δ_causal）という判定基準が Method 節で事前コミット。

### 弱み
1. **信頼区間・誤差棒・統計検定の完全欠落**: 検出率の点推定のみ。Wilson 95% CI で 16/20 = [58%, 93%]、2/20 = [3%, 30%] は重ならないが、セル単位（spurious_p ごと）の Fisher exact test や McNemar 検定が必要。「大幅に上回る」という主張を支持する統計的証拠がない。
2. **n=5 の正当化が「計算資源の都合」のみ**: GridWorld・ColoredMNIST は 1 シードあたり数分〜数十分のオーダーのはずで説得力に欠ける。領域標準は GridWorld で n=20 以上。
3. **exp005 と exp011 のシード独立性が不明**: 両者とも 16/20 を報告しているが「同一オラクル・同一シード」なのか「独立試行」なのかが不明。同一なら n=20 が共有されているだけで実質の独立性がなく、独立試行として誤読される可能性がある。

### 修正提案
- 全検出率に Wilson 95% CI を併記。例: 16/20 (80%, 95% CI [58%, 93%])。
- Δ vs SHAP 比較に paired McNemar 検定を実施、p-value を報告。
- 最低でも GridWorld・ColoredMNIST のシード数を n=10 に増加。
- exp005 と exp011 の関係を Experiments 節冒頭で明記。同一オラクルであれば Results 表を統合するか独立性注記を追加。

---

## 共通指摘（プロトコル準拠チェック）

| 項目 | 現状 | 判定 |
|------|------|------|
| TOPIC ALIGNMENT | LunarLander が contributions 風に言及されすぎ | △ |
| CLAIM-EVIDENCE ALIGNMENT | 数値対応はとれているが「相補的」の一般化が過大主張 | △ |
| STATISTICAL VALIDITY | CI・誤差棒・有意性検定が完全欠落 | ✗ |
| COMPLETENESS | ハイパーパラメータ（MLP 構造、IRM ペナルティ係数、学習率等）が未記載 | ✗ |
| REPRODUCIBILITY | 計算資源・データセットバージョン・コード URL が欠如 | ✗ |
| WRITING QUALITY | 概ね flowing prose。Limitations の bullet list は許容範囲 | ○ |
| FIGURES | **Figure ゼロ → Desk Reject** | ✗ |
| CITATION DISTRIBUTION | Method/Experiments/Discussion での引用がほぼなし | ✗ |

---

## 最優先修正項目（再投稿前必須）

1. **Figure を最低 3 点追加**（散布図 + bar chart + qualitative example）
2. **全検出率に Wilson 95% CI を併記**、Δ vs SHAP に McNemar 検定
3. **領域標準ベースライン**（Spurious Score または Salient ImageNet）を 1 つ以上追加
4. **Waterbirds worst-group accuracy** を group-wise に報告
5. **ハイパーパラメータ・計算資源・コード URL** を Appendix に完全記載
6. **Method/Experiments/Discussion 節の引用を増強**（特に Janzing と Adebayo を介入定義箇所で引用）
7. **LunarLander を Appendix に移動**、本文言及は Limitations のみに集約
8. **exp005 と exp011 のシード独立性** を Experiments 節冒頭で明示
