draft.mdには入らないがメモしておきたい事柄を本ファイルに記載。

# 残対応項目
指摘番号の形式 : [重大度]-[rv+レビュー番号]-[レビュワー]-[指摘連番]
重大度 : C=Critical, M=Major, m=Minor
レビュー番号 : rv01=review1.md（今回）, rv02=reviews.md（ARC #1）, rv03=reviews2.md（第2レビュワー）。都度区別ができるように連番か何かを振る。
各フィールドの役割:
- [指摘]    : レビュアーの指摘内容。Claudeが追加・更新する。指摘の中で対応案が示されていたら本フィールド内に「対応案:xx」と書く。
- [方針]    : ユーザが記入する対応方針。Claudeは上書きしない。空欄なら「要確認」と書いておく。
- [対応内容] : Claudeが実際に行った作業の記録。未着手なら「未対応」。完了時に内容を書く。
- [所感]    : ユーザの私的メモ。Claudeにも読んで欲しいが、書き込みはしない。

---

[C-rv01-X-02] 参考文献リストの形式
    [指摘] 脚注スタイル（[^n]）は Markdown 表記では問題ないが、投稿フォーマット依存。提出先のテンプレートに応じて調整。
    [方針] 対応しない
    [対応内容] -
    [所感] 投稿の予定はございませんでして。

[M-rv01-B-05] 連続行動空間でのStage 1 fidelity基準が曖昧
    [指摘]
        Section 3.3 の「AA > 0.9 または R² > 0.9 を高忠実性の目安とする」という記述に対し、
        Hopper（連続行動空間）では RegTree d=12 が R²=0.922（合格）かつ AA_ε=0.703（不合格）という状態になる。
        どちらの基準が連続行動空間で適用されるのかが Section 3.3 からは読み取れない。
    [方針] 要確認
    [対応内容] 未対応
    [所感]

[M-rv01-B-06] 形式的な判定手続き（Algorithm 1）がない
    [指摘]
        2段階評価を提案しているが、「いつ Surrogate を合格/不合格/要調査とするか」の形式的な手続きがない。
        スレッショルドが borderline の場合に何をするかが不明。概念的な枠組みに留まっており、
        実践者が使うには操作的な定義が不足している。
        対応案: Algorithm 1 または決定フローチャートを追加。
    [方針] 要確認
    [対応内容] 未対応
    [所感]

[M-rv01-C-06] 実験3の非有意結果の文脈が不足
    [指摘]
        「他条件は非有意 (p_adj>0.18)」と記載しているが、Holm補正前の raw p 値（gravity_hi は ≈0.03〜0.09 程度）
        を報告していない。補正によって有意が消えた条件があることを読者が把握できない。
        「不変性が保たれている」という解釈の根拠として、raw p 値の文脈が重要。
        対応案: 全 Experiment 3 の比較について raw と adjusted の p 値を両方報告する。
    [方針] 要確認
    [対応内容] 未対応
    [所感]

[M-rv01-C-07] Hopper gravity_lo 逆転（127%）の CI が非頑健
    [指摘]
        DAgger surrogate の gravity_lo 条件で J_S=493±483 vs J_oracle=389 という「逆転」を強調しているが、
        J_S の標準偏差が 483 と非常に大きく、95% CI は J_oracle=389 を容易に下回る範囲を含む。
        「127% reversal」のヘッドライン数値は統計的に支持されていない。
        対応案: CI を明示し、「逆転の傾向、CartPole pole_long と整合的」という穏やかな表現に変更する。
    [方針] 要確認
    [対応内容] 未対応
    [所感]

[m-rv01-A-06] 「任意の解釈可能モデル」という主張の適用条件が未定義
    [指摘]
        Contribution 1 で「任意の解釈可能モデルを共通軸で比較できる」と主張しているが、
        実験では3ファミリー（線形・木・MoET）＋GBT のみ。
        フレームワークが適用できる Surrogate モデルの形式的な条件（決定論的出力、有限行動空間など）が述べられていない。
        対応案: 必要な性質を明示するか、限界として言及する。
    [方針] 要確認
    [対応内容] 未対応
    [所感]

[m-rv01-B-04] ★再指摘 序論の Mindlin (2025) 引用の接続が弱い
    [指摘]
        Section 2.4 で「対話の前段評価として機能しうる」と記述したが、
        新レビューでも「接続が hand-waved」と指摘。
        具体的な統合経路なしに "could serve as" という言い回しだけが残っている。
        対応案: 具体的な統合シナリオを示すか、引用を削除する。
    [方針] 追加（前回対応済み→再指摘）
    [対応内容] 対応済み（初回）。Section 2.4 末尾に 2 文追加。ただし再指摘あり。
    [所感]
        ダメなの？引用ってそんなもんじゃない？
        「Discussionで回収」って7章のこと？そこは違うんじゃない？
        やるとしたら2章にちょっと書くとか？人間で評価する前にシフトだけ見とこうぜみたいな感じで

[m-rv01-C-08] 収束フィルタリング（J≥450）の post-hoc 性
    [指摘]
        Experiment 3 で seed=2223/2526 を「収束失敗」として除外しているが、
        この閾値は事前登録されていない post-hoc な基準。
        統計検定が 8 シードと 10 シードのどちらを使ったかも不明確。
        対応案: post-hoc 性を明記し、どちらのシードセットで検定を行ったか明示する。
    [方針] 要確認
    [対応内容] 未対応
    [所感]

[m-rv01-C-09] 実験4の多重比較族が局所的に制御されているのみ
    [指摘]
        実験4（CartPole モデル比較）の Holm-Bonferroni は N レベルごとに 3 比較に適用されているが、
        全 N レベルにわたる 12 比較全体のファミリーワイズエラー率が制御されていない。
        対応案: 12 比較全体を family として Holm-Bonferroni を適用し直すか、現状を明記する。
    [方針] 要確認
    [対応内容] 未対応
    [所感]

[m-rv01-X-03] Section 4（提案フレームワーク）と Section 5（実験）での引用が希薄
    [指摘]
        Method・Experiments セクションでの先行研究引用が少ない（Section 4 は Vasic 2019 のみ）。
        環境設計や学習アルゴリズムの選定理由に関する先行研究への言及がない。
    [方針] 要確認
    [対応内容] 未対応
    [所感]

[m-rv02-X-02] コンピュートリソース・学習時間の記述なし
    [指摘] コンピュートリソース・学習時間を記載するべき。再現性要件にかかわる。
    [方針] 放置
    [対応内容] 未対応
    [所感] 実測値を残してなかったので放置でいいや。学習済みモデルですし、蒸留の回数は書いてあるし。

[m-rv03-X-02] 序論の新規性が 3 点に分散
    [指摘]
        1) decoupling の設計、2) AA + 不変性の二軸評価、3) 任意 surrogate の比較基盤 — が並列で読め、
        「何が新規性の中心か」が一意に決まらない。対策案: 主文を 1 本に絞り、残り 2 点を補足へ。
    [方針] 不採用
    [対応内容] 未対応
    [所感] 並列なんですから並列で読んでくれて結構。

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
