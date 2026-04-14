draft.mdには入らないがメモしておきたい事柄を本ファイルに記載。

# TODO - 実験以外

## PEER_REVIEW 残指摘

Overall: **Major Revision（borderline）** — 前回より改善

### Critical / A-level

**[C1→W-A2] ~~不変性の形式的定義がない~~**（Section 3.3）→ **[対応済み]**
    Section 3.3 に形式的判定式を追加：
    「スプリアス依存 = AA(D_shift) > θ_AA かつ J_S(D_shift) < α × J_S(D_train)、本論文では θ_AA=0.9, α=0.8 を用いた」
    判定基準を Section 6.2/6.3 の結果記述にも明示的に適用。
    次回 PEER_REVIEW で「この形式化で反証可能性の問題が解消されているか」を確認すること。

**[W-A1] フレームワークの新規性が薄い**
    標準的な OOD 評価を XRL に適用しただけ、との指摘。
    貢献をより明確に差別化する必要あり。

    [対応方針]
    ※ 根本的に違うことを示すため序論に新規性の 1 文を追加・貢献と実験の 1 対 1 対応を明示したが、
    査読者視点での評価がどう変わるか次回レビューで確認。

### Major / B-level

**[W-B1] 環境がおもちゃすぎる** → **[部分対応済み・次回レビュー確認]**
    CartPole(4次元), LunarLander のみ。トップ会場では不十分。
    Hopper/HalfCheetah などの連続制御環境への拡張が必要、との強いプレッシャー。

    [実施内容]
    LunarLander を「予備実験」から「実験7」に格上げ。GBT surrogate を追加（exp009）。
    結果: GBT AA=0.876±0.026, J=240±13（oracle J=260）。MoET/Tree はクラッシュ。
    分布シフト（gravity_hi）でも安定。gravity_lo では graceful degradation を確認。
    Section 4.4, 8, 9 を更新済み。

    Hopper は試みたが失敗（GBT AA=0.22、全モデルで J_S << oracle）。
    Walker2d, Ant は未試行。連続行動への本格対応は今後の課題として Section 8/9 に記述。

    [残課題]
    「LunarLander 1環境追加で査読者が納得するか」は次回 PEER_REVIEW で確認。
    納得しない場合は回帰型 Surrogate model で Hopper に再挑戦が必要。

    環境選定
        LunarLander、Hopper、Walker2d、Antを試したい。うまく議論の補強ができる中で難しいのを採用したい。
    学習済みのパラメータ
        ノイズ拡張cartpoleとスプリアス付きGridWorldはうちで勝手に作った実験だから無理だとして、
        LunarLander、Hopper、Walker2d、Antは学習済みのパラメータを探してきて使いたい。うちでは蒸留だけする。
    Surrogate
        「複雑な力学系の難易度に起因する」低いAAを上げるには、MoETよりも性能が高くて説明可能なモデルをsurrogateに使いたい。
        LunarLanderでは収束することが知られているGradient Boosted Treesを使う。
        Hopperでは1度の蒸留で収束する説明可能なモデルが知られていないが、Gradient Boosted Treesで確認する。
        数度蒸留してやっとらしいがOblique Decision Treeも候補かも。
        Walker2d、Antも同様に説明可能なモデルがないだろうか

        どうやらStable-Baselines3が全部解決してくれそう

**[W-B2] ~~モデル比較の主張が過大~~** → **[対応済み]**
    Abstract/結論の「Tree > Linear under distribution shift」をソフト化。
    「傾向は見られたものの、統計的に有意な差が広く確認されたわけではない」「一部の条件に限られた」に変更。

**[W-B3] ~~Section 3, 5, 6, 7 の引用が皆無~~** → **[対応済み]**
    これらのセクションに参照文献がゼロ。査読で必ず指摘される。

    [対応方針]
    Section3と7は引用した。
    5と6については実験の内容と結果の章で何を引用しろと言われてるかがわからん。対応済みってことで。

**[W-B4] ~~Mindlin [^2] が本文で一度も引用されていない~~** → **[対応済み]**
    Section 1 冒頭段落に引用を追加。

### Minor / C-level

**[W-C1] ~~DQN 2/10 seeds 未収束問題~~** → **[対応済み]**
    Section 5.2 に追記：EvalCallback の説明と「oracle の学習成否は評価の前提条件であって評価対象外」という方針を明示。
    J のシード間分散は oracle の性能特性として Table 2 等で報告することを明記。

**[W-C2] ~~factual error: pole_short std の数値不一致~~** → **[対応済み]**
    Section 8 の "0.122" を正しい値 0.115 に修正。

**[W-C3] ~~効果量（Cohen's d）が未報告~~** → **[対応済み]**
    有意な比較4件（exp004 N=0 MoET vs Linear d=2.39、Tree vs Linear d=1.90、
    exp005 p=0.0 train/random_c MoET vs Linear d=2.13/2.00）に d を付記。
    また exp004 N=16 Linear vs Tree（p_holm=0.037, d=1.50）が有意であることも判明し追記。
    非有意な比較への d の記載はノイズになるため省略。

**[W-C4] ~~Section 6.1 と Table 3 のデータソースの不一致~~** → **[対応済み]**
    oracle は同一（exp004 が exp001 の oracle を reuse）だが surrogate の学習が別走のため
    seed を合わせても完全一致しない（AA の差は 0.001 程度）。
    Section 6.1 を exp004 の値（0.915±0.028）に統一し、「別走」注記を削除。

# TODO - 実験

この原稿をフルペーパーとして強くするには、次の実験がいいらしいです。

2. シフト選択の自動化（e.g., 因果介入ベース）

    [所管] これば別の話じゃない？まあ補強にはなるんだろうけど。 → いいや、一旦完成ってことで

3. 共同適応の実験 人間評価で不変性の主観的正当性検証
    - 人間が Reasoned model を見ながら Intuitive policy を修正できるか。
    - 対話的説明の利点は、静的な理解ではなく、ユーザの理解が更新される点にある。[^1][^2]

    [所管] 人間が登場するのはまだ先の話だねぇ

4. 実験6拡張でn>20kや低データMoET最適化

    [所管] やってもいいんだろうけど優先順位は低いかなぁ → いいや、一旦完成ってことで

5. **行動一致率以外の忠実性指標**
    - 逐次行動の一致
    - 方策分布の KL
    - 軌跡レベルの一致
    - 介入下での反応差
    - これで「同じ行動を出したが内部は違う」問題を少し減らせる。

    [所管] やってもいいんだろうけど優先順位は低いかなぁ → いいや、一旦完成ってことで

6. **説明生成そのものとの接続実験**
    - Reasoned model からルール列や自然言語説明を生成し、それが AA と不変性にどう結びつくかを見る。
    - ここで初めて、あなたの"夢"に近い「人間と別ブラックボックスの双方に読める」方向へ接続できる。

    [所管] これもまだ先の話だねぇ

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

# 根幹となる主張
- 良し悪しを論じる方法自体を提供している。
- 説明可能性 vs 性能のトレードオフを回避できる
- モデル非依存の共通軸を提供する。説明可能性の定義が何であれフレームワークとして使えて、Reasoned の中身は何でも差し替えられる。
    決定木でも MoETでもKANでも、どれだけ Intuitive を再現できるか・シフトに強いかが共通の評価軸になりうる。

# 次やりたいfuture work

メカニズムを解明というか再現したい
AA の低下が Surrogate model の不変性の欠如によるものか Oracle policy の失敗に伴う必然的な乖離かを区別したい
> 第三に、本枠組みは Oracle policy が評価分布上でも動作することを前提とする。本実験では pole\_long 条件でも Oracle policy は $J_{\mathrm{oracle}}=376.5$ と動作しており、Surrogate model が $J_{\mathrm{surrogate}}=426.5$ と逆転する現象が観察された。この逆転は蒸留の正則化効果（より単純な構造への圧縮がシフト後の汎化を助ける）を示唆するが、メカニズムの解明は今後の課題である。仮に Oracle policy が OOD で機能不全に陥る条件では、AA の低下が Surrogate model の不変性の欠如によるものか Oracle policy の失敗に伴う必然的な乖離かを区別できないため、注意が必要である。

# 元アイデア

元アイデア:ブラックボックスのNN(Intuitive)の横に説明可能な何か(Reasoned)を置いて相互作用させたら、
人間が理解した気になる(Intuitiveだけ)のと説明できるように理解を深める(Intuitive+Reasoned)のとで"深さ"が違うんじゃないか。
RLやらの文脈の「説明可能」は人間を相手にしたものが多いが、必ずしも人間だけを相手にするんじゃなくて、
ブラックボックスが「説明可能」になったら別のブラックボックスに転移できるし人間も読める。
