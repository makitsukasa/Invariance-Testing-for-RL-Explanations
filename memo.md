draft.mdには入らないがメモしておきたい事柄を本ファイルに記載。

# 残対応項目
指摘番号の形式 : [重大度]-[レビュー回数]-[レビュワー]-[指摘連番]
重大度 : C=Critical, M=Major, m=Minor
レビュー回数 : review1/2/3.md を同時更新した1セット＝1回。01=第1回, 02=第2回, 03=第3回…
              ※ 例: review1.md revision2・review2.md revision2・review3.md revision2 → 02
レビュワー : A/B/C=review1.md内（PEER_REVIEW 3名）, D=review2.md, E=review3.md, X=複数共通
各フィールドの役割:
- [指摘]    : レビュアーの指摘内容。Claudeが追加・更新する。指摘の中で対応案が示されていたら本フィールド内に「対応案:xx」と書く。
- [方針]    : ユーザが記入する対応方針。Claudeは上書きしない。空欄なら「要確認」と書いておく。
- [対応内容] : Claudeが実際に行った作業の記録。未着手なら「未対応」。完了時に内容を書く。
- [所感]    : ユーザの私的メモ。Claudeにも読んで欲しいが、書き込みはしない。

---

[C-01-X-02] 参考文献リストの形式
    [指摘] 脚注スタイル（[^n]）は Markdown 表記では問題ないが、投稿フォーマット依存。提出先のテンプレートに応じて調整。
    [方針] 対応しない
    [対応内容] -
    [所感] 投稿の予定はございませんでして。

[M-01-B-05] ★再指摘 連続行動空間での Stage 1 基準と Stage 2 適用の論理的不整合
    [指摘]
        Section 3.3 の「AA > 0.9 または R² > 0.9 を高忠実性の目安とする」という記述に対し、
        Hopper（連続行動空間）では RegTree d=12 が R²=0.922（合格）かつ AA_ε=0.703（不合格）という状態になる。
        どちらの基準が連続行動空間で適用されるのかが Section 3.3 からは読み取れない。
        さらに DAgger surrogate は AA_ε=0.420 と Stage 1 基準を大きく下回っているにもかかわらず、
        Stage 2 の不変性評価に用いられている。Stage 1 を通過しない Surrogate を Stage 2 に進める
        ことの論理的根拠が示されていない。
        → 第2回再指摘（Rev B）: R² を Stage 1 の支配的基準と位置づけた対応後も、
        BC の R²=0.922 は合格するが DAgger は R² が不適切（分布ミスマッチ）で AA_ε=0.420 と低い。
        BC の Stage 1 通過 → Stage 2 は筋が通るが、DAgger の Stage 2 適用には依然として
        「Stage 1 基準を何で満たすのか」の説明が必要。
        対応案: Appendix 5 に「DAgger は分布ミスマッチにより R² が不適切であるため、
        AA_ε を Stage 1 の代替指標として扱うが、0.9 閾値は満たさない。
        本実験は Stage 1 未達の surrogate でも invariance 評価の枠組みが記述的に適用できる
        ことを示すデモ」として位置づけを明示する。
    [方針] 離散行動空間ではAAの定義を現行のものとし、連続行動空間ではAAの定義をR^2とする。みたいな書き方に変更
    [対応内容] 対応済み（第1回）。Section 3.3 を改訂し、離散行動空間では AA（行動一致率）、
        連続行動空間では AA を R² として再定義（ε-agreement は補助指標）と明示した。
        ← 第2回指摘が残存。DAgger の Stage 1 未達問題の位置づけが未対応。
    [所感] 連続と離散なんだから定義が違っても別にそんなに変じゃないよね？

[M-01-B-06] 形式的な判定手続き（Algorithm 1）がない
    [指摘]
        2段階評価を提案しているが、「いつ Surrogate を合格/不合格/要調査とするか」の形式的な手続きがない。
        スレッショルドが borderline の場合に何をするかが不明。概念的な枠組みに留まっており、
        実践者が使うには操作的な定義が不足している。
        対応案: Algorithm 1 または決定フローチャートを追加。
    [方針] 却下
    [対応内容] -
    [所感]
        概念的な枠組みを提案してるんです。俺がどう頑張ったって学習し直しがいいかモデル変更がいいか単に時間を伸ばすだけでいいかなんかわからんし。
        それがわかればすごくいいことだとは思いますけれどもね

[m-01-B-10] MoET ツリー可視化がコードブロック形式
    [指摘]
        Section 6.2 の決定木可視化が indented テキスト（コードブロック）で記述されており、
        論文の図として体裁が整っていない。camera-ready では proper figure が必要。
    [方針] 却下
    [対応内容] -
    [所感] 一緒のことが書いてあって体裁で文句言うな

[m-01-B-11] ★再指摘（4.3のみ） Section 4.3・5.1 の箇条書きを prose に変換すべき
    [指摘]
        NeurIPS フォーマットでは本文中の箇条書きリストは推奨されない。
        Section 4.3（Evaluation Metrics）と Section 5.1（実験目的リスト）が箇条書き形式。
        → 第2回再指摘（Rev A cross-reviewer summary）: Section 5.1 の番号付きリストは
        "functional" として認められているが、Section 4.3 の bullet list は
        「should be converted to prose for a NeurIPS submission」と再び指摘。
    [方針] 以前reviewで箇条書きが読みやすいと言われて変更したはず。それを確認して矛盾しないのであれば修正で。
    [対応内容] review3.md が「Section 5.1 のシグンポストが navigation に役立つ」と明示的に評価。
        前回レビューと矛盾するため Section 5.1 は変更なし。
        ← Section 4.3（AA と J_S の 2 bullet）は再指摘が残存。
    [所感]

[M-02-X-01] タイトル・フレーミングの過剰主張
    [指摘]
        タイトル「Explainability Evaluation Framework」に対し、実際に提案しているのはスプリアス依存の
        複製を検出するツールであり、「説明品質を評価するフレームワーク」という主張は過剰。
        人間評価・グラウンドトゥルースとの比較・実践者による有用性検証が一切なく、
        "explainability evaluation" と呼ぶ根拠が薄い。（Rev A・B 共通指摘）
        対応案（Rev A）: "Detecting Spurious Dependencies in Surrogate Explanations of RL Policies
        via Invariance Testing" 等、実際の貢献を反映したタイトルに変更する。
    [方針] 要確認
    [対応内容] 未対応
    [所感]

[M-02-A-01] 実験2の設計がトートロジー的
    [指摘]
        Spurious GridWorld を p=0.0 で構成すると c が確定的にゴールを示す。
        この設定では任意の合理的な学習器が c に依存する。その依存を複製した Surrogate が
        c を反転すると失敗することは設計上自明（by construction）であり、
        提案フレームワークの有効性を独立に示す証拠になっていない。
        論文には言及があるが「なぜそれでも価値があるか」の説明が不十分。
        対応案: 「制御された環境での diagnostic criteria の動作検証」であることを明示し、
        フレームワークが既知の ground-truth を持つ設定で正しく機能することの証拠として位置づける。
    [方針] 要確認
    [対応内容] 未対応
    [所感]

[M-02-A-02] 閾値感度分析が main text にない
    [指摘]
        θ_AA=0.9 と α=0.8 の恣意性はフレームワーク論文の中心的問題であるにもかかわらず、
        感度分析（Tables 6・7）が付録的な扱いになっており、本文から数値なしで参照されるのみ。
        「どの閾値を選んでも定性的結論は変わらない」という主張は本文に明示すべき。
        対応案: Section 7（Discussion）に感度分析の主要結論（閾値変化で結論不変）を1段落追加。
    [方針] 要確認
    [対応内容] 未対応
    [所感]

[M-02-C-01] 統計報告：AA の有意差が marginal かつ SD/CI の使い分けが不明確
    [指摘]
        （1）実験2の中心的主張「高 AA」の根拠となる train vs reversed_c の AA 比較は
        p_adj=0.030（n=10）で有意閾値ぎりぎり。d=1.14 は中〜大効果だが検出力は低い。
        論文はこの marginal な有意差を過剰に断定的に提示している。
        （2）AA=0.942±0.056 は標準偏差（SD）で報告しているが、診断閾値 θ=0.9 との比較は
        推論的文脈なので 95% CI（≈ [0.902, 0.982]）で表記すべき。
        CI 下限が閾値 0.9 をわずかに上回るに過ぎず、「高 AA」条件の成立が全シードで安定しない。
        （Rev C）
        対応案: Experiment 2 の AA 比較に 95% CI を追記し「p=0.030 は有意だが marginal」と
        一言注記する。診断閾値との比較箇所では SD でなく 95% CI を使用する。
    [方針] 要確認
    [対応内容] 未対応
    [所感]

[m-02-B-01] MoET が主要 surrogate だが広く普及していない
    [指摘]
        実験の大部分が MoET を primary surrogate として使用しているが、MoET は広く使われていない。
        モデル比較（Exp4・5）では MoET と Tree が GridWorld でほぼ同等の AA を示しており、
        MoET のゲーティング機構がこれらの小規模環境で付加価値を持つのか疑問。
        （Rev B）
    [方針] 要確認
    [対応内容] 未対応
    [所感]

[m-02-B-02] IRM・概念ボトルネックとの実験比較なし
    [指摘]
        Related work で IRM と concept bottleneck を詳述しているが、実験比較がない。
        「IRM で oracle を再訓練して蒸留したら不変性はどうなるか」などの baseline があると
        提案フレームワークの実用的価値が明確になる。（Rev B）
    [方針] 要確認
    [対応内容] 未対応
    [所感]

[m-02-C-01] J_S の t 検定が退化している
    [指摘]
        実験2 reversed_c の J_S は全 10 シードで -1.000（分散ゼロ）。
        この条件での Welch's t-test は分母がゼロとなり d>1000 は人工物。
        論文では「p_adj<0.001, d>1000」として有意差の証拠として示しているが、
        全値が同一という自明な事実に統計検定を適用することは不適切。
        対応案: 「全 10 シードで J_S=-1.000（分散ゼロ）、統計的にも自明」と記述し、
        Mann-Whitney U 等か、あるいは検定なしで記述する。（Rev C）
    [方針] 要確認
    [対応内容] 未対応
    [所感]

[m-02-C-02] 実験横断での多重検定が未制御
    [指摘]
        各実験内では Holm-Bonferroni で補正しているが、実験 2・3・4・5・7 をまたぐ
        ファミリーワイズエラー率の制御については言及がない。（Rev C）
        対応案: 現状を明記（実験ごとに独立した family として補正）するか、
        全実験横断での補正を行う。
    [方針] 要確認
    [対応内容] 未対応
    [所感]

[m-02-X-02] コンピュートリソース・学習時間の記述なし
    [指摘] コンピュートリソース・学習時間を記載するべき。再現性要件にかかわる。
    [方針] 放置
    [対応内容] -
    [所感] 実測値を残してなかったので放置でいいや。学習済みモデルですし、蒸留の回数は書いてあるし。

[m-03-X-02] 序論の新規性が 3 点に分散
    [指摘]
        1) decoupling の設計、2) AA + 不変性の二軸評価、3) 任意 surrogate の比較基盤 — が並列で読め、
        「何が新規性の中心か」が一意に決まらない。対策案: 主文を 1 本に絞り、残り 2 点を補足へ。
    [方針] 却下
    [対応内容] -
    [所感] 並列なんですから並列で読んでくれて結構。

[m-03-X-03] ★★再指摘（三度目） 主要主張が付録実験のみに支持されている
    [指摘]
        Contribution 3（連続システムへの拡張性）・要旨・結論の Hopper DAgger 結果（J_S=63%）は
        付録5（Appendix 5）にのみ記載されており、本文 Section 6 には登場しない。
        NeurIPS フォーマットでは付録は補足であり、本文の主要主張の根拠に付録を使うのは構造的問題。
        対応案: LunarLander / Hopper の主要数値を Section 6 に移動するか、
        Contribution 3 の表現を「付録で検証」と明示して格下げする。
        前回対応済み→再指摘（Section 5.5 を追加実験セクションに改編・付録1〜5へ移動したが不十分と評価）
        → 第3回再指摘（Rev B）: 格下げ後も Contribution 3 に
        「demonstrating a tendency for the evaluation axes to function consistently across
        multiple RL environments」という表現が残っており、main body の2環境（CartPole + GridWorld）
        だけでは「複数の RL 環境で一貫して機能する」という主張を支持しないと再び指摘。
        対応案: 「across multiple RL environments」を「across the two environments tested」等に修正。
    [方針] じゃあしょうがない、「付録で検証」と明示して格下げする方針で
    [対応内容] 対応済み（第1・2回）。Section 1 の Contribution 3 を「付録レベルの予備的検証として、
        LunarLander-v3 および MuJoCo Hopper-v5 への適用（付録4・5）により拡張可能性を示唆するが、
        連続制御タスクへの本格的な検証は今後の課題とする」と格下げした。
        ← 第3回指摘が残存。「across multiple RL environments」の文言が未修正。

# 根幹となる主張
- 良し悪しを論じる方法自体を提供している。
- 説明可能性 vs 性能のトレードオフを回避できる
- モデル非依存の共通軸を提供する。説明可能性の定義が何であれフレームワークとして使えて、Reasoned の中身は何でも差し替えられる。
    決定木でも MoETでもKANでも、どれだけ Intuitive を再現できるか・シフトに強いかが共通の評価軸になりうる。

# 次やりたいfuture work

1. AA の低下が Surrogate model の不変性の欠如によるものか Oracle policy の失敗に伴う必然的な乖離かを区別したい
    > 第三に、本枠組みは Oracle policy が評価分布上でも動作することを前提とする。本実験では pole\_long 条件でも Oracle policy は $J_{\mathrm{oracle}}=376.5$ と動作しており、Surrogate model が $J_{\mathrm{surrogate}}=426.5$ と逆転する現象が観察された。この逆転は蒸留の正則化効果（より単純な構造への圧縮がシフト後の汎化を助ける）を示唆するが、メカニズムの解明は今後の課題である。仮に Oracle policy が OOD で機能不全に陥る条件では、AA の低下が Surrogate model の不変性の欠如によるものか Oracle policy の失敗に伴う必然的な乖離かを区別できないため、注意が必要である。

    [所感] メカニズムを解明というか再現したい
    わざと弱いoracleを使ったら再現できるかもexp007にある学習回数の足りてないhopperのoracleとか

2. シフト選択の自動化（e.g., 因果介入ベース）

    [所感] これば別の話じゃない？まあ補強にはなるんだろうけど。 → いいや、一旦完成ってことで

3. 共同適応の実験 人間評価で不変性の主観的正当性検証
    - 人間が Reasoned model を見ながら Intuitive policy を修正できるか。
    - 対話的説明の利点は、静的な理解ではなく、ユーザの理解が更新される点にある。[^1][^2]

    [所感] 人間が登場するのはまだ先の話だねぇ

4. 実験6拡張でn>20kや低データMoET最適化

    [所感] やってもいいんだろうけど優先順位は低いかなぁ → いいや、一旦完成ってことで

5. **行動一致率以外の忠実性指標**
    - 逐次行動の一致
    - 方策分布の KL
    - 軌跡レベルの一致
    - 介入下での反応差
    - これで「同じ行動を出したが内部は違う」問題を少し減らせる。

    [所感] やってもいいんだろうけど優先順位は低いかなぁ → いいや、一旦完成ってことで

6. **説明生成そのものとの接続実験**
    - Reasoned model からルール列や自然言語説明を生成し、それが AA と不変性にどう結びつくかを見る。
    - ここで初めて、あなたの"夢"に近い「人間と別ブラックボックスの双方に読める」方向へ接続できる。

    [所感] これもまだ先の話だねぇ

# 参考文献/先行研究

重複を少し整理して、この会話で実質候補として出たものを、**引用優先 / 勉強用 / 脇役**で並べました。大きくは、`説明付き知識蒸留・概念ボトルネック・代理モデル` の流れと、`対話的・共同構成的XAI` の流れに分かれます。[^1][^2][^3]

| Paper | Summary |
|---|---|
| Learning Global Additive Explanations of Black-Box Models | **Label: 引用優先.** Distills a black-box model into global additive explanations; the learned feature shapes are meant to preserve fidelity while staying interpretable. Good if you want to say your method is about *compressing behavior into a readable surrogate*, not just drawing local attributions. |
| ConceptDistil: Model-Agnostic Distillation of Concept Explanations (Sousa et al., 2022.) | **Label: 引用優先.** Uses knowledge distillation to bring concept explanations to any black-box classifier. This is one of the closest matches to your "human-readable intermediate representation" idea. |
| Improving Knowledge Distillation with Teacher's Explanation | **Label: 引用優先.** Lets the student learn not only from teacher predictions but also from teacher explanations, using superfeature explanations. Useful for the "explanations can be transferred" framing. |
| Knowledge Distillation Decision Tree for Unravelling Black-Box Machine Learning Models | **Label: 勉強用.** Distills a black-box into a decision tree and emphasizes structural stability, simplicity, and predictivity. Nice conceptual support for why your own structural constraints matter. |
| Learning Interpretation with Explainable Knowledge Distillation | **Label: 引用優先.** Argues that vanilla KD may not transfer explainable knowledge, and adds explanation transfer to improve faithfulness and accuracy. |
| Explainable Knowledge Distillation / Harnessing Teacher's Explanation for Improved Knowledge Distillation | **Label: 引用優先.** Later variants of the same idea: transfer teacher explanations along with predictions so the student learns the "right features." Better as supporting citations than as the core citation. |
| Joint learning of interpretation and distillation | **Label: 勉強用.** Poses the question of whether a distilled model should make similar predictions for similar reasons, especially across different model structures. Very close in spirit to your black-box-to-black-box transfer question. |
| Interpretable & Explorable Approximations of Black Box Models | **Label: 勉強用.** Learns compact transparent approximations of black-box models and lets users steer which subspace is explained. Helpful for the "explorable surrogate" angle. |
| Can Explanations Be Useful for Calibrating Black Box Models? | **Label: 引用優先.** Uses explanations to calibrate a black-box model on a new domain and shows the calibration model can transfer somewhat across tasks. Good if you want one paper that connects explanations to transfer. |
| GLocalX - From Local to Global Explanations of Black Box AI Models | **Label: 勉強用.** Aggregates local explanations into global ones and tries to keep the proxy model both simple and faithful. Useful as a bridge between local and global explanation views. |
| Regularizing Black-box Models for Improved Interpretability | **Label: 勉強用.** Regularizes a model during training so post-hoc explanations become more stable and useful. This is a nice "train-time interpretability" counterpoint to post-hoc distillation. |
| Exploring Multi-Task Learning for Explainability | **Label: 勉強用.** Trains a black-box and a surrogate together so the surrogate tracks the teacher more closely. Helpful if you want a softer alternative to pure post-hoc distillation. |
| Post-hoc Concept Bottleneck Models | **Label: 引用優先.** Turns any neural network into a concept bottleneck model without sacrificing performance, and can transfer concepts from other datasets or natural language descriptions. This is one of the strongest citations for your "another black box can read it" direction. |
| Concepts from Representations: Post-hoc Concept Bottleneck Models via Sparse Decomposition of Visual Representations | **Label: 勉強用.** Retrofits interpretability onto pretrained models by decomposing representations into concepts and filtering them with multimodal LMs. Good for the "post-hoc concept extraction" family. |
| Concept Embedding Models | **Label: 勉強用.** Learns richer concept representations that support interventions and work under sparse concept supervision. Useful if you later want concept-level intervention as part of the story. |
| Do Concept Bottleneck Models Learn as Intended? | **Label: 脇役 / 注意.** A cautionary paper: CBMs can fail to realize the intended semantic interpretability and intervenability. Good as a limitation citation, not as a positive precedent. |
| Learning Bottleneck Concepts in Image Classification | **Label: 勉強用.** Learns bottleneck concepts without explicit concept supervision, showing another route to human-readable intermediate concepts. |
| Incremental Residual Concept Bottleneck Models | **Label: 勉強用.** Adds missing concepts post-hoc and proposes a concept-utilization metric; useful if you want to talk about concept completeness. |
| Explanation Bottleneck Models | **Label: 勉強用.** Generates a text explanation first and then predicts from that explanation, using distillation to keep the explanation fluent and task-aligned. Very relevant if you want natural-language intermediates. |
| Machine Explanations and Human Understanding (Chen et al., 2022.) | **Label: 引用優先.** The key human-centered XAI paper here: explanations can have mixed or negative effects, and human intuitions matter for what they can actually improve. |
| Reflexive Dialogue-Based Explainability for Human-AI Collaboration | **Label: 引用優先.** Reports that reflexive dialogue improves task accuracy, comprehension, and trust calibration relative to static explanations. Good if you want the dialogue/interaction route in one sentence. |
| Editable XAI: Toward Bidirectional Human-AI Alignment with Co-Editable Explanations of Interpretable Attributes | **Label: 引用優先.** Lets users write rules to improve control and deepen understanding; directly supports the bidirectional-alignment framing. |
| Towards Co-Constructed Explanations: CoCoXplain (Mindlin et al., 2025.) | **Label: 引用優先.** Treats explanation as a co-constructed process and reports improved subjective understanding and trust-related measures. Good if you want to say the literature already treats explanation as interaction, not output. |
| Explainable AI as Collaborative Task Solving | **Label: 勉強用.** Uses Theory of Mind to model machine and human beliefs explicitly, with improved trust over saliency maps. A useful conceptual bridge if you later expand the human side. |

Arjovsky, M., et al. (2019). Invariant risk minimization. arXiv:1907.02893.

(ちょっと古いかも、draftからは削除)
Huang, X., Kwiatkowska, M., Wang, S., & Wu, M. (2018). Safety verification of deep neural networks. *Computer Aided Verification (CAV)*. ※ 本文中「重要な状態の特定」として引用; 実装文脈に応じて適切な文献に差し替えること。

(出所不明)
- 2.1: Zhang et al. (2023) 蒸留効率向上（最近の蒸留進展として提案された）
- 2.4: Madumal et al. (2022) RL-XAIレビュー（2022年以降として提案された）

(勉強用、Reasoned候補?)
Weight Agnostic Neural Networks (Adam Gaier, David Ha)
Neural Module Networks（Andreas et al. 2016）「is_red?」「is_cube?」みたいなモジュールを組み合わせて VQA を解くやつです。
KAN（Kolmogorov-Arnold Networks） 「各接続が univariateな学習可能関数」という意味での局所的説明可能性を狙っている。

# draftに不採用の内容

KL divergence
    行動分布間の乖離の補助指標。
    使おうとしたが、AAで十分だったため削除。AAでは説明できない場合は計算してみたら有意差ありなしを確認できるかも

Relative Performance Drop
    $\mathrm{RPD} = (J_I - J_R)/J_I$（$J$: 累積報酬）。不変性の補助指標。
    使おうとしたが、 $J_I$ と $J_R$ の比較で十分だったため削除。

Inv_J = J_R(D_shift) / J_R(D_train)
    Jの崩壊を直接捉えるが、pole_longでJ_R(train)→J_R(shift)の方向が逆転するケースで解釈が難しい

$J_{\mathrm{surrogate}} > J_{\mathrm{oracle}}$ の強調
    実験3で見られた$J$の逆転現象は、説明可能性のための構造制約が、意図せずしてモデルの汎化性能を向上させる可能性を示唆している？
    元アイデアに書いた「説明できるように理解を深める」のポジティブな面が覗いているが、どうもメインの主張のノイズにしかならんので不採用。

MoETとTreeとLinearを比較したいわけじゃないのをもっと明示
    追加する文の例
    本研究の目的はモデル間の優劣を結論づけることではないが、提案する評価軸が構造の違いに応じた挙動の差を捉えられることを確認する
    構造の違いが、再現性と不変性のトレードオフとしてどのように現れるかを観察する

# 元アイデア

元アイデア:ブラックボックスのNN(Intuitive)の横に説明可能な何か(Reasoned)を置いて相互作用させたら、
人間が理解した気になる(Intuitiveだけ)のと説明できるように理解を深める(Intuitive+Reasoned)のとで"深さ"が違うんじゃないか。
RLやらの文脈の「説明可能」は人間を相手にしたものが多いが、必ずしも人間だけを相手にするんじゃなくて、
ブラックボックスが「説明可能」になったら別のブラックボックスに転移できるし人間も読める。
