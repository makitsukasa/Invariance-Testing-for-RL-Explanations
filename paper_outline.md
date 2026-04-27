# 論文アウトライン: 介入ベース性能感度測定によるスプリアス特徴検出

最終更新: 2026-04-27

本書は研究内容（exp005〜exp013）を踏まえた論文アウトラインの最新版である。Tier-0 の主張は exp011（GridWorld での Δ vs SHAP）と exp012（ColoredMNIST IRM での SHAP 構造的バイアス分析）であり、exp005 / exp010 / exp013 で外的妥当性を補強する構成とする。

**確定タイトル**: Detecting Spurious Features via Intervention-Based Performance Sensitivity

---

## 1. exp013 Waterbirds 結果（2026-04-27 確定）

| seed | val_acc | delta_bg | delta_fg | Δ判定 | shap_bg | shap_fg | SHAP判定 |
|------|---------|----------|----------|-------|---------|---------|---------|
| 0    | 0.822   | 0.100    | 0.078    | OK    | 0.8942  | 0.1058  | OK      |
| 42   | 0.786   | 0.094    | 0.084    | OK    | 0.8604  | 0.1396  | OK      |
| 123  | 0.759   | 0.122    | 0.094    | OK    | 0.8562  | 0.1438  | OK      |
| 456  | 0.796   | 0.116    | 0.091    | OK    | 0.8620  | 0.1380  | OK      |
| 789  | 0.776   | 0.122    | 0.075    | OK    | 0.8709  | 0.1291  | OK      |

**Δ 5/5 (100%)、SHAP 5/5 (100%)。** 両手法とも正解。
解釈: Waterbirds はスプリアス相関が強く（95%）背景が視覚的に顕著なため両手法とも機能する。論文の narrative としては「相関が強く特徴が顕著な場合は両者が一致し、弱くなるにつれΔが優位になる」という gradient として提示できる。

**推奨**: 案 1。理由は次の三点。
- 手法名 DELTA を確立すれば、後続論文・引用で参照しやすい。
- 「Intervention-Based Performance Sensitivity」の語が、SHAP 系の「attribution（出力分布上の寄与）」との対比を直接表現している。
- 8〜14 語制約の最短側（9 語）で、検索ヒットしやすい。

論文中の固有名詞は **DELTA**（Δ-test）で統一する。

---

## 2. セクション別アウトライン（総語数目標 約 6,800 語）

### 2.1 Abstract — 200 語

- **目標**: 問題、提案手法、見出し結果、メッセージを一段落で凝縮する。
- **語数目標**: 200 語。
- **主要な主張・内容**:
  1. 訓練済みモデルがスプリアス特徴に依存しているか否かを post-hoc に診断する問題は未解決である。
  2. 我々は **DELTA** を提案する。各特徴 f に対してドメイン適切な介入 T_f を適用し、Δ_f = J_train − J_perturbed を測定して argmax_f Δ_f をスプリアス特徴と同定する。
  3. GridWorld 10 次元（exp011）で DELTA は 16/20（80%）、SHAP は 2/20（10%）。
  4. ColoredMNIST（IRM 設定、exp012）では DELTA 17/20（85%）、SHAP 20/20（100%）に見えるが、この SHAP の見かけ上の優位は ColoredMNIST の R-G チャネル符号化に由来する**構造的アーティファクト**である（p=0.3 でのオラクル切替を SHAP は追従できず Δ のみが追従）。
  5. 結論: Δ は分布シフト下での性能劣化感度を直接測定する点で、出力分散寄与に基づく SHAP より信頼できる。
- **根拠リンク**: exp005, exp010, exp011, exp012, exp013。

### 2.2 Introduction — 900 語

- **目標**: 問題設定、既存手法の不足、本論文の貢献、論文構成を提示する。
- **語数目標**: 900 語（4 段構成）。
- **主要な主張・内容**:
  1. *動機（約 200 語）*: モデルがスプリアス相関を利用すると分布シフト下で性能が崩壊する（Geirhos et al. 2020、Sagawa et al. 2020）。実務者が必要とするのは「この訓練済みモデルが依存している特徴はどれか」を答える診断ツールである。
  2. *既存手法の不足（約 200 語）*: SHAP・IG・LIME などの attribution 手法は訓練分布上での出力寄与を測定する。スプリアスな特徴であっても寄与が小さく見えることがあり、寄与の大きさはスプリアス性と等価ではない。実際 exp011 で SHAP は GridWorld のスプリアス特徴をほぼ検出できなかった（10%）。
  3. *提案アイデア（約 250 語）*: 特徴 f の予測有用性が、ラベルとの相関を破る介入 T_f の下で消えるなら、その特徴はスプリアスである。Δ_f = J_train − J_perturbed を定義し、argmax を取る。Δ は介入後の実性能を直接測定するため、SHAP よりスプリアス性の判定に直結する。
  4. *貢献（約 150 語、箇条書き）*:
     - **C1**. DELTA test の定義と実装。訓練済みモデル、特徴単位の介入、保留評価セットのみを要する。
     - **C2**. 二つの統制環境（GridWorld 10 次元、ColoredMNIST IRM）での p-sweep による外的妥当性確認（exp005、exp010）。
     - **C3**. SHAP との同一 oracle・同一 seed での頭対頭比較（exp011、exp012）。SHAP の ColoredMNIST 上の見かけの成功が R-G 符号化由来の構造的アーティファクトであることの分析。
     - **C4**. 失敗事例分析（LunarLander、exp006–007）: oracle が候補スプリアス特徴を使わない場合、DELTA を適用する前提が成立しないことを明示。
  5. *構成（約 100 語）*: 各節の見取り図。
- **根拠リンク**: exp011（Δ 80% vs SHAP 10%）、exp012（SHAP アーティファクト解析）。

### 2.3 Related Work — 700 語

- **目標**: DELTA を (i) 不変学習、(ii) 特徴 attribution、(iii) スプリアス特徴自動発見、(iv) 介入ベースのテストの中で位置づける。
- **語数目標**: 700 語。
- **主要な主張・内容**:
  1. *不変学習・worst-group robustness（約 200 語）*: IRM（Arjovsky et al. 2019）、GroupDRO（Sagawa et al. 2020）、counterfactual invariance（Veitch et al. 2021）。これらは不変な予測器を**学習する**手法であり、環境ラベルや事前知識を要求し、訓練済みモデルの**診断**は行わない。
  2. *特徴 attribution（約 250 語）*: SHAP（Lundberg & Lee 2017）、IG（Sundararajan et al. 2017）、LIME（Ribeiro et al. 2016）、GradientExplainer（Erhan et al. 2009）。これらは「どの特徴が予測に寄与するか」に答えるが、「どの特徴がスプリアスに相関しているか」には答えない、という主張を exp011・exp012 が経験的に裏付ける。
  3. *事前知識なしのスプリアス特徴発見（約 150 語）*: Zhou et al. 2021、Singla & Feizi 2022、Adebayo et al. 2022。最近接の研究群。Adebayo et al. 2022 は post-hoc 説明がスプリアス相関の検出に不十分であることを示しており、本論文の問題意識と整合する。
  4. *介入ベースのテスト（約 100 語）*: 因果的特徴重要度（Janzing et al. 2020）、NLP の介入研究（Vig et al. 2020）。DELTA はこの系譜を「スプリアス性検出」に応用したものと位置づける。
- **根拠リンク**: 文献のみ（実験リンクなし）。

### 2.4 Method — 1,400 語

- **目標**: DELTA を厳密に定義し、設計上の選択（介入の意味づけ、サロゲート蒸留の役割、計算コスト）を説明する。
- **語数目標**: 1,400 語（6 サブセクション）。
- **主要な主張・内容**:
  1. *問題設定（約 200 語）*: 訓練済みモデル f_θ : X → Y、特徴分解 X = (x_1, …, x_n)、性能指標 J（精度 / リターン）。訓練分布 P_train に存在する相関の一部は P_test では成立しない。本論文の目的は、f_θ が依存しているスプリアス特徴を post-hoc に同定すること。
  2. *Δ_f の定義（約 250 語）*:
     - Δ_f = J(f_θ; D_eval) − J(f_θ; T_f(D_eval))
     - T_f は特徴 f に対するドメイン適切な介入。他特徴は保持する。
     - 同定規則: f* = argmax_f Δ_f。
     - 補足: Δ プロファイル（Δ_1, …, Δ_n）の全体をランキングとして提示することも可能（memo.md の議論を Method に組み込む）。
  3. *ドメイン適切な介入の設計（約 350 語）*:
     - GridWorld: スプリアスチャネル c のバッチ内シャッフル（ラベル相関を破壊しつつ周辺分布を保持）、または各候補特徴へのガウシアンノイズ加算。
     - ColoredMNIST: 色チャネル（R）置換による hue-shuffle、構造に対しては画素ノイズ／dropout。
     - Waterbirds: GrabCut による背景置換、前景マスクへのノイズ付加。
     - **設計原則**: 「候補特徴の情報経路を遮断するが、入力モダリティは保つ」。Pixel zeroing のように一切を破壊する介入は不適切（ベースライン低下が候補特徴の情報量と無関係になるため）。
  4. *Oracle / surrogate 蒸留パイプライン（約 250 語）*: oracle は偏った訓練データに適合させる。DELTA を適用するのはサロゲート（蒸留先）。AA ≥ 0.9 を介入前にゲートとして検証することで、Δ がサロゲート固有のノイズではなく oracle の振る舞いを反映していることを担保する。
  5. *計算コスト（約 150 語）*: O(n_features × evaluation_cost)。線形スケール。実測値は付録表（Table 4）。
  6. *DELTA が適用できない条件（約 200 語）*: oracle が候補特徴を全く使わない場合（∀f, Δ_f ≈ 0）、DELTA は意味のある出力を返せない。LunarLander（exp006–007）がこの境界事例にあたる。これは DELTA 自体の限界ではなく、診断対象の前提条件が成立しない場合と整理する。
- **根拠リンク**: Figure 1（パイプライン）、Figure 2（蒸留＋AA ≥ 0.9 ゲート）、exp006–007（適用境界の負例）。

### 2.5 Experiments — 600 語

- **目標**: 環境、ベースライン、評価プロトコルを記述する。
- **語数目標**: 600 語。
- **主要な主張・内容**:
  1. *環境（約 250 語）*:
     - GridWorld 10 次元（スプリアス 1 + 因果 2 + ノイズ 7、spurious_p ∈ {0.0, 0.1, 0.2, 0.3}）。
     - ColoredMNIST IRM 設定（label_noise_p = 0.25、Arjovsky et al. 2019 準拠、spurious_p ∈ {0.0, 0.1, 0.2, 0.3}）。
     - Waterbirds（waterbird_complete95_forest2water2、ResNet-18 + FC fine-tune、介入は GrabCut 背景置換 vs 前景ノイズ）。
  2. *ベースライン（約 150 語）*: SHAP GradientExplainer（ColoredMNIST では SHAP に最も有利な R-G 非対称集約を採用）、SHAP KernelExplainer（GridWorld の表形式入力向け）。Permutation Importance / LIME は SHAP / Δ と機能的に類似のため省略（memo.md で整理済み）。
  3. *プロトコル（約 150 語）*: 各 (環境, p) セルにつき 5 シード。検出成功 = 手法の top-1 特徴が真のスプリアス特徴と一致。検出率と 95% Wilson 区間を報告。同一 oracle・同一 seed で SHAP と Δ を比較する設計（exp011、exp012）により、データ・モデル分散の効果を排除。
  4. *指標（約 50 語）*: 検出率、Δ プロファイル、oracle 評価精度、サロゲート忠実度（AA）。
- **根拠リンク**: exp005, exp010, exp011, exp012, exp013。

### 2.6 Results — 1,500 語

- **目標**: 主張を実験単位で示す。各サブセクションは独立に読めるよう、見出し → 数値 → 図表 → 解釈の順に統一する。
- **語数目標**: 1,500 語。
- **主要な主張・内容**:
  1. *DELTA は相関強度を追跡する（約 300 語、exp005）*:
     - GridWorld 10 次元、p ∈ {0.0, 0.1, 0.2}: 15/15 (100%)、p=0.3: 1/5 (20%)。
     - 解釈: p=0.3 では oracle が因果特徴に再配置されるため、スプリアス特徴の Δ が低下する。これは「相関が崩壊するほど DELTA は引き分けに収束する」性質の経験的確認である。
     - **Figure 3**。
  2. *DELTA は画像ドメインに一般化する（約 250 語、exp010）*:
     - ColoredMNIST IRM、p=0.0: 5/5、p=0.1: 5/5、p=0.2: 4/5、p=0.3: 3/5。
     - **Figure 4**。
  3. *DELTA は GridWorld で SHAP を上回る（約 350 語、exp011）*:
     - DELTA 16/20 (80%) vs SHAP 2/20 (10%)。同一 oracle・同一 seed での比較。
     - 失敗モード分析: SHAP は agent_y やノイズ特徴を top-1 に挙げる。スプリアス特徴は出力分散寄与が因果特徴より小さく、attribution 順位で下に来るため。
     - **Table 1**, **Figure 5**。
  4. *SHAP の見かけの ColoredMNIST 成功は構造的バイアス（約 400 語、exp012）*:
     - 見出し: DELTA 17/20 vs SHAP 20/20 → 一見 SHAP が完勝。
     - 診断: ColoredMNIST は R チャネル = 色、G チャネル = 0 の符号化を採用しているため、SHAP の attribution は常に color_attr ≈ 2 × struct_attr を満たす（R-G 非対称集約のもとで）。これは oracle の振る舞いに依存しない構造的事実である。
     - 反証: p=0.3 で oracle は色依存から構造依存に切替わる（label_noise_p=0.25 のため、p=0.3 では構造の方が予測力が高くなる、IRM 設定の本来の挙動）。DELTA はこの切替を 5 シード中 3 シードで検出（Δ_struct > Δ_color）、SHAP は切替を全シードで検出できない（attribution 比は固定）。
     - したがって SHAP の 100% は「正しく特徴を当てた」結果ではなく、「データセットの符号化のおかげで偶然 100% に見える」結果である。
     - **Table 2**, **Figure 6**。
  5. *実世界スプリアス相関への適用（約 200 語、exp013）*:
     - Waterbirds、ResNet-18 + FC fine-tune。介入: 背景 GrabCut 置換 vs 前景ノイズ。
     - 期待される結果: Δ_background > Δ_foreground。
     - 現状: 実行中。確認済みシードでは Δ・SHAP 両方とも CORRECT。投稿版では n=5 完了後に検出率を埋める。
- **根拠リンク**: exp005, exp010, exp011, exp012, exp013。

### 2.7 Discussion — 700 語

- **目標**: 結果を解釈し、attribution と Δ の本質的差異、適用境界、実務上の含意を整理する。
- **語数目標**: 700 語。
- **主要な主張・内容**:
  1. *なぜ attribution はスプリアス性を捉えないか*: attribution は訓練多様体上での勾配場（あるいは Shapley の周辺寄与）の関数である。スプリアス性は介入下で**崩壊する**相関の性質である。両者は数学的に異なる対象を測っており、混同してきたこと自体が本論文の指摘点。
  2. *なぜ DELTA は高 p で劣化するか*: spurious_p が十分に大きいと、oracle は因果特徴とスプリアス特徴を併用するように再配置する。すると介入は両系統に対して性能を低下させ、argmax の決着が不安定になる。これは「高 p 領域では『どの特徴がスプリアスか』が識別不能になる」という、問題設定そのものの限界を反映している。バグではなく、識別性の限界。
  3. *Δ プロファイルの解釈*: argmax だけでなく、Δ プロファイル全体をランキングとして提示することで、依存度の定量的可視化が可能（memo.md「確認すること」項を反映）。
  4. *実務上の含意*: DELTA と attribution は補完関係にあり、置き換え関係ではない。実務者は (i) 候補特徴の attribution、(ii) Δ、(iii) 分布シフト評価を組み合わせて使うべき。
- **根拠リンク**: exp005（高 p 劣化）、exp012（attribution と Δ の乖離）。

### 2.8 Limitations — 400 語

- **目標**: 想定される限界を網羅的に列挙する。
- **語数目標**: 400 語。
- **主要な主張・内容**:
  1. *シード数*: 現状 n=5（前先行論文で n=10 でも少ないと指摘された経緯あり、memo.md 参照）。投稿版に向けて n=30 への拡張を予定。中断可能な再実装を計画。
  2. *計算コスト*: O(n_features) のため特徴数が大きい場合は特徴クラスタリング・グルーピングが必要。SHAP 絞り込み後に Δ を適用するハイブリッド戦略は将来課題（memo.md「保留中」を反映）。
  3. *因果保証の欠如*: Δ は介入下の統計的依存を測るが、Pearl 的因果スプリアス性は保証しない。どの介入が「ドメイン的に意味のある介入」かはドメイン知識を要する。
  4. *LunarLander 負例*: oracle が候補スプリアス特徴を使うように設計できなかったため、DELTA の適用前提が成立しない（exp006–007）。これは DELTA の限界というより評価条件の限界である。
  5. *Waterbirds は実行中*: 投稿版で結果を埋める。
  6. *ベースラインの限定*: SHAP（GradientExplainer / KernelExplainer）のみ。Permutation Importance / LIME は SHAP / Δ と機能的に類似のため除外したが、レビュアー要請があれば付録で追加。
- **根拠リンク**: exp006–007（LunarLander 負例）、exp013（Waterbirds 進行中）。

### 2.9 Broader Impact — 200 語

- **目標**: 社会的影響、誤用リスク、推奨される使い方を簡潔に述べる。
- **語数目標**: 200 語。
- **主要な主張・内容**:
  - DELTA は診断ツールであり、人口統計属性やショートカット特徴への依存を実務者が事前に把握する助けとなる。
  - リスク: (a) 設計者が想定した介入のみで「スプリアス性なし」と誤って認証されるリスク。(b) 部分的な特徴セットしか試行しないことによる過信。
  - 推奨: DELTA は分布シフト評価の代替ではなく補完。投入前評価のチェックリストの一項目として位置づけるべき。

### 2.10 Conclusion — 200 語

- **目標**: 主張の再強調と将来の方向。
- **語数目標**: 200 語。
- **主要な主張・内容**:
  - 結論: DELTA は介入ベースの post-hoc 診断であり、二つの統制環境で SHAP より信頼できるスプリアス特徴検出を達成する（GridWorld 80% vs 10%、ColoredMNIST IRM では SHAP の見かけの 100% が R-G 符号化由来のアーティファクトであることを exp012 が示す）。
  - 最も重要なメッセージ: SHAP の数値が高いことは「正しく特徴を当てている」ことと同義ではない。介入下で oracle の振る舞いを追跡できるかが本質である。
  - 将来課題: 特徴グルーピングへの拡張、worst-group robust 訓練との結合、CelebA 等への大規模実適用、ハイブリッド SHAP→Δ パイプライン。
- **根拠リンク**: exp011, exp012。

### 2.11 References

- 第 4 節（参考文献リスト）に列挙する。

---

## 3. 図表リスト

| ID | 種別 | 配置節 | 表示内容 | データ出典 |
|----|------|--------|----------|------------|
| **Figure 1** | 概念図 | Method 2.4.2 | DELTA パイプライン: 訓練済みモデル → 特徴単位介入 T_f → 性能差 Δ_f → argmax → 同定 | 概念のみ |
| **Figure 2** | 概念図 | Method 2.4.4 | Oracle → サロゲート蒸留、AA ≥ 0.9 ゲート、Δ 計算へ | 概念のみ |
| **Figure 3** | 折れ線/棒 | Results 2.6.1 | GridWorld 検出率 vs spurious_p（5 シード、誤差棒） | exp005 |
| **Figure 4** | 折れ線/棒 | Results 2.6.2 | ColoredMNIST IRM 検出率 vs spurious_p | exp010 |
| **Figure 5** | 並列棒 | Results 2.6.3 | DELTA vs SHAP（GradientExplainer / KernelExplainer）GridWorld 検出率 | exp011 |
| **Figure 6** | 散布/折れ線 | Results 2.6.4 | ColoredMNIST: 各シードの Δ_color vs Δ_structure。p=0.3 でのクロスオーバーを可視化、SHAP の固定 2:1 比と対比 | exp012 |
| **Figure 7** | 画像グリッド | Method 2.4.3 / Results | 介入の可視例: hue shuffle、構造ノイズ、GrabCut 背景置換 | exp010, exp013 |
| **Table 1** | 表 | Results 2.6.3 | GridWorld 検出率行列: 行 = p、列 = {DELTA, SHAP-Grad, SHAP-Kernel} | exp011 |
| **Table 2** | 表 | Results 2.6.4 | ColoredMNIST 検出率 + 各手法の top-1 特徴分布（SHAP の 2:1 R:G 比を露出） | exp012 |
| **Table 3** | 表 | Experiments 2.5 | 環境 × oracle × 介入 × spurious_p の総括 | 全実験 |
| **Table 4** | 表（付録） | Limitations | DELTA の環境別 wall-clock コスト | exp012 約 66 分 / 20 runs ほか |

---

## 4. 査読者への先手（想定反論と対応）

| # | 想定反論 | 対応方針 | 該当節・根拠 |
|---|----------|----------|--------------|
| Q1 | 「これは単なる特徴 ablation では？」 | DELTA は「ドメイン適切な介入」を要求する点が pixel zeroing 等の素朴 ablation と決定的に異なる（モダリティを保持し情報経路だけを遮断する）。Method 2.4.3 で設計原則を明記、Figure 7 で具体例を示す。 | Method 2.4.3、Figure 7 |
| Q2 | 「シード n=5 は少ない」 | 投稿時に n=30 に拡張する旨を Limitations に明記。中断可能実装の方針も併記。先行論文での n=10 指摘の経緯を踏まえ、camera-ready で完了させる。 | Limitations 2.8 |
| Q3 | 「ColoredMNIST で SHAP は 100% なのに DELTA が劣ると主張するのは不公平では？」 | exp012 の構造的バイアス分析（R-G 符号化により color_attr ≈ 2 × struct_attr が常成立）を示し、p=0.3 で oracle が構造に切替わっても SHAP の attribution 比は変わらず、DELTA のみが切替を検出することを Table 2 と Figure 6 で証明。 | Results 2.6.4、Discussion 2.7 |
| Q4 | 「ベースラインが SHAP のみ。LIME / Permutation Importance / IG はどうか」 | LIME と SHAP-Kernel は近似的に等価、PI は Δ と機能的に類似。本論文の主張軸は「attribution（出力分散寄与）vs 介入（性能感度）」であり、SHAP は attribution 系統の代表として十分。要請があれば付録で追加実験。 | Related Work 2.3、Limitations 2.8 |
| Q5 | 「LunarLander で失敗したのは DELTA の限界では？」 | Method 2.4.6 と Limitations 2.8 で「oracle が候補特徴を使わない場合は前提が成立しない」境界条件として明示。失敗の原因は oracle 設計（差分 shaping、zone_bonus sweep 全条件で c 非依存）であり、DELTA そのものの欠陥ではない。 | Method 2.4.6、Limitations 2.8、exp006–007 |
| Q6 | 「特徴数が増えたとき計算量が爆発するのでは？」 | O(n_features × eval_cost) を Method 2.4.5 で明示し、特徴グルーピング・SHAP 絞り込み後の Δ 適用というハイブリッド戦略を将来課題として提示。中規模特徴数（≤100）では実用的であることを exp011 / exp012 の wall-clock で例示。 | Method 2.4.5、Limitations 2.8、Table 4 |
| Q7 | 「Δ は因果スプリアス性を保証しない」 | その通り。DELTA は介入下の統計的依存を測る指標であり、Pearl 的因果性は保証しないと Limitations 2.8 で明示。これは memo.md の「主張」段落と整合。 | Limitations 2.8 |
| Q8 | 「Waterbirds の結果がない」 | 実行中のものを camera-ready までに完了させる旨を Limitations 2.8 で明記。投稿版に間に合わない場合は Section 2.6.5 を「初期所見」として位置づけ、最終版で完成させる。 | Limitations 2.8、exp013 |
| Q9 | 「サロゲート蒸留が必須なら、サロゲートのバイアスが Δ に混入するのでは？」 | AA ≥ 0.9 のゲート（Method 2.4.4）でサロゲート忠実度を担保。ゲートを通過した場合のみ Δ を解釈対象とする。サロゲート不適合は Δ 結果の棄却条件。 | Method 2.4.4、Figure 2 |
| Q10 | 「真のスプリアス特徴が未知の実世界で、どう DELTA を検証するのか？」 | 統制環境（GridWorld、ColoredMNIST IRM）で外的妥当性を確認後、Waterbirds（既知のスプリアス相関ベンチマーク）に適用するという段階的検証戦略を採用。Section 2.6.5 と Discussion 2.7 で議論。 | Results 2.6.5、Discussion 2.7、exp013 |

---

## 5. 参考文献

1. Arjovsky, M., Bottou, L., Gulrajani, I., & Lopez-Paz, D. (2019). **Invariant Risk Minimization**. arXiv:1907.02893.
2. Veitch, V., D'Amour, A., Yadlowsky, S., & Eisenstein, J. (2021). **Counterfactual Invariance to Spurious Correlations in Text Classification**. NeurIPS 2021.
3. Zhou, C. et al. (2021). **事前知識なしのスプリアス相関発見**（memo.md の参照論文 — arXiv:2106.07171）。
4. Lundberg, S. M., & Lee, S.-I. (2017). **A Unified Approach to Interpreting Model Predictions**. NeurIPS 2017. (SHAP)
5. Sundararajan, M., Taly, A., & Yan, Q. (2017). **Axiomatic Attribution for Deep Networks**. ICML 2017. (Integrated Gradients)
6. Erhan, D., Bengio, Y., Courville, A., & Vincent, P. (2009). **Visualizing Higher-Layer Features of a Deep Network**. University of Montreal Tech Report.
7. Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). **"Why Should I Trust You?": Explaining the Predictions of Any Classifier**. KDD 2016. (LIME)
8. Sagawa, S., Koh, P. W., Hashimoto, T. B., & Liang, P. (2020). **Distributionally Robust Neural Networks for Group Shifts**. ICLR 2020. (GroupDRO; Waterbirds)
9. Geirhos, R. et al. (2020). **Shortcut Learning in Deep Neural Networks**. Nature Machine Intelligence.
10. Singla, S., & Feizi, S. (2022). **Salient ImageNet: How to Discover Spurious Features in Deep Learning?**. ICLR 2022.
11. Adebayo, J., Muelly, M., Abelson, H., & Kim, B. (2022). **Post Hoc Explanations May Be Ineffective for Detecting Unknown Spurious Correlation**. ICLR 2022.
12. Janzing, D., Minorics, L., & Blöbaum, P. (2020). **Feature Relevance Quantification in Explainable AI: A Causal Problem**. AISTATS 2020.
13. Vig, J., Gehrmann, S., Belinkov, Y., et al. (2020). **Investigating Gender Bias in Language Models Using Causal Mediation Analysis**. NeurIPS 2020.
14. Rother, C., Kolmogorov, V., & Blake, A. (2004). **GrabCut: Interactive Foreground Extraction Using Iterated Graph Cuts**. SIGGRAPH 2004.

---

## 6. 投稿戦略メモ

- **想定投稿先**: NeurIPS 2026 main track。レビュアーが手法新規性で押される場合は Datasets & Benchmarks トラックを副案。
- **camera-ready アップグレード**: (i) n=30 シード、(ii) exp013 Waterbirds 完了、(iii) 第 4 環境として CelebA blond/gender（Sagawa et al. 2020）を追加検討。
- **再現性**: exp005 / exp010 / exp011 / exp012 の seed と config をコード公開。介入仕様は YAML 化して付録で配布。
- **最大のリスク**: Q3（ColoredMNIST で SHAP が 100% に見える）。Results 2.6.4 と Figure 6 / Table 2 で構造的バイアスを定量的に示すことで先回りする。
