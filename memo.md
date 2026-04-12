draft.mdには入らないがメモしておきたい事柄を本ファイルに記載。

# TODO - 実験以外

## PEER_REVIEW 指摘（残タスク）

6節: KL divergence の扱いを整理（放置中）
    現状は定義したが Table に数値未掲載。選択肢：
    (a) 実験2・5のKL値をTableに追加する
    (b) 「AAで十分な理由」を明示し、定義セクションからKLを削除または補足扱いに格下げ

    [所管]
        AAが有意差なしだけどKLが有意差ありみたいなのがあれば意味あるかも、そうじゃなきゃ確かに意味ないかも。
        他の実験で使うかもなので一旦放置、最終版直前で不要かを再度判断したい。

RPD の位置づけ整理（放置中）
    定義して CartPole では使わず、GridWorld でも Table に未掲載。
    「補助指標」の位置づけをさらに明示するか、定義を簡略化。

    [所管] 他の実験で使うかもなので一旦放置、最終版直前で不要かを再度判断したい。

参考文献（未追加分）
    以下は未追加。読んでから判断：
    - 2.1: Zhang et al. (2023) 蒸留効率向上（最近の蒸留進展として提案された）
    - 2.4: Madumal et al. (2022) RL-XAIレビュー（2022年以降として提案された）
    - [^13] Huang et al. (2018) 「重要な状態の特定」→ 引用が正確かどうか要確認（draft.md に注記あり）

## 以前からのTODO

4.2 Reasoned Modelの候補
    候補の選択理由をMoETの連続調整性に絞り、追加の正当化（e.g., 計算コスト）を提案

# TODO - 実験

この原稿をフルペーパーとして強くするには、次の実験が必要らしいです。

1. MuJoCoなどの連続制御環境でablation再現

    (a) 連続行動を離散 bin に分割してAAを計算する（実装コスト低、ただし近似的）
    (b) MoET/Tree/Linear を回帰器に書き換え、AAの代わりに MSE や行動分布の KL を使う（実装コスト高）
    (c) 離散行動な連続制御環境（LunarLander-v3等）で代用する（実装コスト低、MuJoCo不使用）

    (a)/(c)採用で「連続制御への適用可能性を示す追加実験」として正直に説明・限界記載で完全に許容されます。
    (b)なしでも「連続制御の実験」と呼べます（preliminary/ablationとして）。NeurIPS査読でも「離散焦点で連続拡張示唆」で通る（e.g., DT系の論文多数）。

    論文挿入例
    4.5 Ablation: Continuous Control Extension (Preliminary)
    We demonstrate framework applicability to continuous-like settings via:
    - Discrete proxy: LunarLander-v3 (discretized continuous dynamics).
    - Action binning: MuJoCo Hopper (10 bins, AA via argmax).
    Results: MoET maintains superior reproducibility (Fig.X), suggesting structural constraints generalize beyond discrete actions. Limitations: Bin approximation may lose fine-grained control; full regression (MSE/KL) remains future work.

    結果によっては、主張「再現性/不変性の構造的優位」が揺るがず、汎用性ボーナス。

2. シフト選択の自動化（e.g., 因果介入ベース）

    [所管] これば別の話じゃない？まあ補強にはなるんだろうけどさ

3. 共同適応の実験 人間評価で不変性の主観的正当性検証
    - 人間が Reasoned model を見ながら Intuitive policy を修正できるか。
    - 対話的説明の利点は、静的な理解ではなく、ユーザの理解が更新される点にある。[^1][^2]

    [所管] 人間が登場するのはまだ先の話だねぇ

4. 実験6拡張でn>20kや低データMoET最適化

    [所管] やってもいいんだろうけど優先順位は低いかなぁ

5. **行動一致率以外の忠実性指標**
    - 逐次行動の一致
    - 方策分布の KL
    - 軌跡レベルの一致
    - 介入下での反応差
    - これで「同じ行動を出したが内部は違う」問題を少し減らせる。

    [所管] やってもいいんだろうけど優先順位は低いかなぁ

6. **説明生成そのものとの接続実験**
    - Reasoned model からルール列や自然言語説明を生成し、それが AA と不変性にどう結びつくかを見る。
    - ここで初めて、あなたの“夢”に近い「人間と別ブラックボックスの双方に読める」方向へ接続できる。

    [所管] これもまだ先の話だねぇ

# 参考文献/先行研究

重複を少し整理して、この会話で実質候補として出たものを、**引用優先 / 勉強用 / 脇役**で並べました。大きくは、`説明付き知識蒸留・概念ボトルネック・代理モデル` の流れと、`対話的・共同構成的XAI` の流れに分かれます。[^1][^2][^3]

| Paper | Summary |
|---|---|
| Learning Global Additive Explanations of Black-Box Models | **Label: 引用優先.** Distills a black-box model into global additive explanations; the learned feature shapes are meant to preserve fidelity while staying interpretable. Good if you want to say your method is about *compressing behavior into a readable surrogate*, not just drawing local attributions. |
| ConceptDistil: Model-Agnostic Distillation of Concept Explanations | **Label: 引用優先.** Uses knowledge distillation to bring concept explanations to any black-box classifier. This is one of the closest matches to your “human-readable intermediate representation” idea. |
| Improving Knowledge Distillation with Teacher's Explanation | **Label: 引用優先.** Lets the student learn not only from teacher predictions but also from teacher explanations, using superfeature explanations. Useful for the “explanations can be transferred” framing. |
| Knowledge Distillation Decision Tree for Unravelling Black-Box Machine Learning Models | **Label: 勉強用.** Distills a black-box into a decision tree and emphasizes structural stability, simplicity, and predictivity. Nice conceptual support for why your own structural constraints matter. |
| Learning Interpretation with Explainable Knowledge Distillation | **Label: 引用優先.** Argues that vanilla KD may not transfer explainable knowledge, and adds explanation transfer to improve faithfulness and accuracy. |
| Explainable Knowledge Distillation / Harnessing Teacher’s Explanation for Improved Knowledge Distillation | **Label: 引用優先.** Later variants of the same idea: transfer teacher explanations along with predictions so the student learns the “right features.” Better as supporting citations than as the core citation. |
| Joint learning of interpretation and distillation | **Label: 勉強用.** Poses the question of whether a distilled model should make similar predictions for similar reasons, especially across different model structures. Very close in spirit to your black-box-to-black-box transfer question. |
| Interpretable & Explorable Approximations of Black Box Models | **Label: 勉強用.** Learns compact transparent approximations of black-box models and lets users steer which subspace is explained. Helpful for the “explorable surrogate” angle. |
| Can Explanations Be Useful for Calibrating Black Box Models? | **Label: 引用優先.** Uses explanations to calibrate a black-box model on a new domain and shows the calibration model can transfer somewhat across tasks. Good if you want one paper that connects explanations to transfer. |
| GLocalX - From Local to Global Explanations of Black Box AI Models | **Label: 勉強用.** Aggregates local explanations into global ones and tries to keep the proxy model both simple and faithful. Useful as a bridge between local and global explanation views. |
| Regularizing Black-box Models for Improved Interpretability | **Label: 勉強用.** Regularizes a model during training so post-hoc explanations become more stable and useful. This is a nice “train-time interpretability” counterpoint to post-hoc distillation. |
| Exploring Multi-Task Learning for Explainability | **Label: 勉強用.** Trains a black-box and a surrogate together so the surrogate tracks the teacher more closely. Helpful if you want a softer alternative to pure post-hoc distillation. |
| Post-hoc Concept Bottleneck Models | **Label: 引用優先.** Turns any neural network into a concept bottleneck model without sacrificing performance, and can transfer concepts from other datasets or natural language descriptions. This is one of the strongest citations for your “another black box can read it” direction. |
| Concepts from Representations: Post-hoc Concept Bottleneck Models via Sparse Decomposition of Visual Representations | **Label: 勉強用.** Retrofits interpretability onto pretrained models by decomposing representations into concepts and filtering them with multimodal LMs. Good for the “post-hoc concept extraction” family. |
| Concept Embedding Models | **Label: 勉強用.** Learns richer concept representations that support interventions and work under sparse concept supervision. Useful if you later want concept-level intervention as part of the story. |
| Do Concept Bottleneck Models Learn as Intended? | **Label: 脇役 / 注意.** A cautionary paper: CBMs can fail to realize the intended semantic interpretability and intervenability. Good as a limitation citation, not as a positive precedent. |
| Learning Bottleneck Concepts in Image Classification | **Label: 勉強用.** Learns bottleneck concepts without explicit concept supervision, showing another route to human-readable intermediate concepts. |
| Incremental Residual Concept Bottleneck Models | **Label: 勉強用.** Adds missing concepts post-hoc and proposes a concept-utilization metric; useful if you want to talk about concept completeness. |
| Explanation Bottleneck Models | **Label: 勉強用.** Generates a text explanation first and then predicts from that explanation, using distillation to keep the explanation fluent and task-aligned. Very relevant if you want natural-language intermediates. |
| Machine Explanations and Human Understanding | **Label: 引用優先.** The key human-centered XAI paper here: explanations can have mixed or negative effects, and human intuitions matter for what they can actually improve. |
| Reflexive Dialogue-Based Explainability for Human-AI Collaboration | **Label: 引用優先.** Reports that reflexive dialogue improves task accuracy, comprehension, and trust calibration relative to static explanations. Good if you want the dialogue/interaction route in one sentence. |
| Editable XAI: Toward Bidirectional Human-AI Alignment with Co-Editable Explanations of Interpretable Attributes | **Label: 引用優先.** Lets users write rules to improve control and deepen understanding; directly supports the bidirectional-alignment framing. |
| Towards Co-Constructed Explanations: CoCoXplain | **Label: 引用優先.** Treats explanation as a co-constructed process and reports improved subjective understanding and trust-related measures. Good if you want to say the literature already treats explanation as interaction, not output. |
| Explainable AI as Collaborative Task Solving | **Label: 勉強用.** Uses Theory of Mind to model machine and human beliefs explicitly, with improved trust over saliency maps. A useful conceptual bridge if you later expand the human side. |

If you want, I can turn this into a **3-column bibliography table** next: `paper / why cite it / where it fits in your draft`, which is probably the most usable form for writing. これは会話ベースの初期スキャンなので、用語を少し変えると近縁論文はまだ増えるはずです。

[^1]: Chen et al., 2022. Machine Explanations and Human Understanding. Trans. Mach. Learn. Res.

[^2]: Sousa et al., 2022. ConceptDistil: Model-Agnostic Distillation of Concept Explanations. arXiv.org.

[^3]: Mindlin et al., 2025. Towards Co-Constructed Explanations: A Multi-Agent Reasoning-Based Conversational System for Adaptive Explanations. International Conference on Human-Agent Interaction.


勉強用、Reasoned候補? Weight Agnostic Neural Networks (Adam Gaier, David Ha)
勉強用、Reasoned候補? Neural Module Networks（Andreas et al. 2016）「is_red?」「is_cube?」みたいなモジュールを組み合わせて VQA を解くやつです。
勉強用、Reasoned候補? KAN（Kolmogorov-Arnold Networks） 「各接続が univariateな学習可能関数」という意味での局所的説明可能性を狙っている。

# 元アイデア

元アイデア:ブラックボックスのNN(Intuitive)の横に説明可能な何か(Reasoned)を置いて相互作用させたら、人間が理解した気になる(Intuitiveだけ)のと説明できるように理解を深める(Intuitive+Reasoned)のとで"深さ"が違うんじゃないか。RLやらの文脈の「説明可能」は人間を相手にしたものが多いが、必ずしも人間だけを相手にするんじゃなくて、ブラックボックスが「説明可能」になったら別のブラックボックスに転移できるし人間も読める。
