draft.mdには入らないがメモしておきたい事柄を本ファイルに記載。

# TODO - 実験以外

## PEER_REVIEW 残指摘

### Critical

**[C1] 不変性の形式的定義がない**（Section 3.3）
    再現性は AA の数式があるが、不変性には定量的な判断基準がない。
    AA(D_shift) / AA(D_train) の比率など、再現性と同程度の形式性を持つ指標を提案する。
    閾値感度分析とあわせて示すことが望ましい。

**[C2] 「説明可能性」と「構造的圧縮可能性」のギャップ**（全体）
    高AA・高不変性 → 説明可能、の橋渡しが不足。
    K=4,d=5 の MoET が 80本のリーフを持ちうるが、それが「説明可能」かは自明でない。
    対応案：(a) 「説明可能性」を主張せず「構造的圧縮可能性と分布シフト耐性の評価」と再定義、
    または (b) 構造制約モデルが人間に解釈可能という仮定を明示し、限界を議論に含める。

### Major

**[M1] 不変性の判断基準が AA と J の間で揺れている**（Section 6.2, 6.3）
    実験2は J の崩壊で「不変性低」と判定、実験3は J が崩壊しないことで「不変性高」と判定。
    AA と J のどちらが不変性の指標か不明確。環境をまたいで J を直接比較できない問題もある。
    対応案：$\Delta$AA（シフト前後の AA 差）を不変性の主指標として統一する。

**[M2] Section 4.4 がシフト下の AA を報告していない**
    本枠組みの核心（再現性×不変性の二軸評価）なのに、予備実験では訓練分布上の AA のみ。
    シフト下の AA と J も報告するか、主張を「蒸留の適用可能性」に限定する。

**[M3] Intuitive policy の学習品質が未報告**（Section 5 全般）
    CartPole の J=211.7 は解決基準（J≧475）に届いていない。
    全環境で学習曲線または最終性能を報告し、「十分に学習された方策の蒸留」であることを示す。
    または現状の J で十分とする理由を述べる。

### Medium / Minor

**[Med1] 「構造ボトルネック」と概念ボトルネックの「ボトルネック」の差異の説明不足**（Section 2.3）
    概念BNは人間定義概念を中間表現に使う。本研究のボトルネックはモデルクラスの表現力制限。
    質的に異なることを明示すると混乱が防げる。

**[Med2] N=16 で Linear が逆転する現象の考察不足**（Section 6.4）
    Linear(0.823) > MoET(0.810) > Tree(0.798) と「構造制約が強いほど再現性が高い」前提と矛盾する可能性。
    正則化効果 vs 表現力のトレードオフについて踏み込んだ議論が必要。

**[Med3] 再現性だけで「説明可能性の度合い」を決める理論的根拠**（Section 3.3）
    圧縮可能性は必要条件かもしれないが十分条件ではない。
    「構造制約下の再現性は説明可能性の必要条件であって十分条件ではない」と明記するだけでも可。

**[Min1] Arjovsky et al. (2019) の脚注番号 [^5] が本文で明示されていない箇所がある**

**[Min2] Figure の欠番（実験4・5 に対応する Figure がない）**
    Table のみで視覚的把握が難しい。余裕があれば追加。

**[Min3] 「Intuitive policy」と「Reasoned model」の命名の非対称性**
    一方が policy、他方が model。意図的なら理由を明記。

**[Min4] 各実験が何を示しているかの対応を明示する**（feedback3）
    実験1〜6がそれぞれフレームワークのどの主張を裏付けているかを、
    Section 5 冒頭か Section 7 に一段落（または小さな表）として整理すると読者の理解コストが下がる。
    4象限を廃止した今は「実験2=高AA×低不変性の実証、実験3=スプリアスなし環境での観察」のような形で。

**[Min5] 具体的な利用シナリオを議論・結論に追加する**（feedback3）
    現状は「枠組みの提案」止まり。安全クリティカルRL・既存XRLパイプラインへの差し込み方など
    ひと段落の具体例を書くと「使える道具」として格上げされる。
    Section 7 の action flow 段落（スプリアス検出後の対処）と統合しても良い。

**[Min6] pole_length の位置づけを明示する**（feedback2）
    実験3で重力シフトとポール長変更を並べているが、「何が違う外乱か」の概念的区別が薄い。
    「重力は動的なスケーリング、ポール長は運動方程式そのものの変形」のように一文加えると
    「同じ物理パラメータシフトの仲間」ではなく「外乱の種類が違う二例」と読まれる。

# TODO - 実験

この原稿をフルペーパーとして強くするには、次の実験がいいらしいです。

2. シフト選択の自動化（e.g., 因果介入ベース）

    [所管] これば別の話じゃない？まあ補強にはなるんだろうけどさ

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

(ちょっと古いかも、draftからは削除)
Huang, X., Kwiatkowska, M., Wang, S., & Wu, M. (2018). Safety verification of deep neural networks. *Computer Aided Verification (CAV)*. ※ 本文中「重要な状態の特定」として引用; 実装文脈に応じて適切な文献に差し替えること。

(出所不明)
- 2.1: Zhang et al. (2023) 蒸留効率向上（最近の蒸留進展として提案された）
- 2.4: Madumal et al. (2022) RL-XAIレビュー（2022年以降として提案された）

(勉強用、Reasoned候補?)
Weight Agnostic Neural Networks (Adam Gaier, David Ha)
Neural Module Networks（Andreas et al. 2016）「is_red?」「is_cube?」みたいなモジュールを組み合わせて VQA を解くやつです。
KAN（Kolmogorov-Arnold Networks） 「各接続が univariateな学習可能関数」という意味での局所的説明可能性を狙っている。

# 削除した要素

KL divergence
    行動分布間の乖離の補助指標。
    使おうとしたが、AAで十分だったため削除。AAでは説明できない場合は計算してみたら有意差ありなしを確認できるかも

Relative Performance Drop
    $\mathrm{RPD} = (J_I - J_R)/J_I$（$J$: 累積報酬）。不変性の補助指標。
    使おうとしたが、 $J_I$ と $J_R$ の比較で十分だったため削除。

# 元アイデア

元アイデア:ブラックボックスのNN(Intuitive)の横に説明可能な何か(Reasoned)を置いて相互作用させたら、人間が理解した気になる(Intuitiveだけ)のと説明できるように理解を深める(Intuitive+Reasoned)のとで"深さ"が違うんじゃないか。RLやらの文脈の「説明可能」は人間を相手にしたものが多いが、必ずしも人間だけを相手にするんじゃなくて、ブラックボックスが「説明可能」になったら別のブラックボックスに転移できるし人間も読める。
