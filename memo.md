draft.mdには入らないがメモしておきたい事柄を本ファイルに記載。

# 元アイデア

元アイデア:ブラックボックスのNN(Intuitive)の横に説明可能な何か(Reasoned)を置いて相互作用させたら、人間が理解した気になる(Intuitiveだけ)のと説明できるように理解を深める(Intuitive+Reasoned)のとで"深さ"が違うんじゃないか。RLやらの文脈の「説明可能」は人間を相手にしたものが多いが、必ずしも人間だけを相手にするんじゃなくて、ブラックボックスが「説明可能」になったら別のブラックボックスに転移できるし人間も読める。

# review

致命的な問題（desk reject 相当）

- 図表ゼロ — 実験データはあるのに可視化が論文に含まれていない
- Related Work セクションが存在しない — 方策蒸留・解釈可能RLの先行研究との差分が不明
- 引用5本 — NeurIPSは通常30-50本

大きな問題

- 統計的厳密性の不足 — 信頼区間なし、有意性検定なし、シード数n=3は少ない
- 「境界の判定」という主張に対し、閾値・判定基準の定義がない — 実際には変化傾向を観察しているだけ
- MoET のハイパーパラメータ（学習率・損失関数・バッチサイズ等）が未記載
- 線形モデル・決定木との比較がない — MoET 一択の正当化が不十分

軽微な問題

- セクション5のタイトルが「結果の書き方」になっている
- 議論セクションの3点が箇条書きのまま（散文に直すべき）
- p=0.5 の「除外」を結果として考察に組み込むべき


# 実験結果サマリー（2×2診断枠組みとの対応）

| | 不変性：高 | 不変性：低 |
|---|---|---|
| **再現性：高** | **exp003** CartPole N=0 gravity_hi: AA=0.80, J=124–158 ✅ | **exp002** GridWorld reversed_c: AA=0.95, J=−1.000 ✅ |
| **再現性：低** | （未実験） | （未実験） |

exp003（2026-04-11 完了）: CartPole N=0, K=4/d=5 MoET, 重力×ポール長の5条件
- exp001 の N=0 学習済みモデルを再利用（再学習なし）
- gravity_lo: AA=0.822, J_I=208, J_R=272 / gravity_hi: AA=0.804, J_I=158, J_R=124
- pole_short: AA=0.757, J_I=190, J_R=134
- pole_long: AA=0.594, J_I=35, J_R=229 ← Intuitive 自体が OOD 失敗、別ケース
- 対比: exp002 reversed_c AA=0.954, J=-1.000
- `experiments/results/exp003_cartpole_gravity/`
- `experiments/src/shifted_cartpole_env.py` で gravity + pole_length を制御

# 足りない実験

この原稿をフルペーパーとして強くするには、次の実験が必要らしいです。

0. **✅ 再現性高 × 不変性高 セルを埋める実験** → exp003 完了（CartPole N=0 + 重力シフト）

1. **分布シフト条件の拡張**
   - reverse だけでなく、報酬関数変更、ゴール配置変更、観測欠落を追加する。
   - これで「c の反転専用の話」ではないと示せる。

2. **MoET 以外の構造制約との比較**
   - 線形モデル
   - 単一決定木
   - shallow tree
   - soft decision tree
   - 可能ならルールベース表現
   - これで「MoET 固有の話ではない」ことを示せる。

3. **蒸留データ量の感度分析**
   - 1k / 5k / 10k / 20k で再現性がどう変わるかを振る。
   - 再現性がデータ量にどれだけ依存するかがわかる。

4. **複数シードのばらつき評価の強化**
   - 3シードでは弱いので、少なくとも 5〜10 シードほしい。
   - 特に GridWorld のスプリアス条件は分散が出やすいはず。

5. **行動一致率以外の忠実性指標**
   - 逐次行動の一致
   - 方策分布の KL
   - 軌跡レベルの一致
   - 介入下での反応差
   - これで「同じ行動を出したが内部は違う」問題を少し減らせる。

6. **説明生成そのものとの接続実験**
   - Reasoned model からルール列や自然言語説明を生成し、それが AA と不変性にどう結びつくかを見る。
   - ここで初めて、あなたの“夢”に近い「人間と別ブラックボックスの双方に読める」方向へ接続できる。

7. **共同適応の実験**
   - 人間が Reasoned model を見ながら Intuitive policy を修正できるか。
   - 対話的説明の利点は、静的な理解ではなく、ユーザの理解が更新される点にある。[^1][^2]


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


Post-hoc Concept Bottleneck Models
Mert Yuksekgonul, M. Wang, and 1 more
International Conference on Learning Representations, 2022

1
A key benefit of PCBM is that it enables users to quickly debug and update the model to reduce spurious correlations and improve generalization to new distributions.
