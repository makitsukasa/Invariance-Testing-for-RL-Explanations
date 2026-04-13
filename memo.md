draft.mdには入らないがメモしておきたい事柄を本ファイルに記載。

# TODO - 実験以外

## PEER_REVIEW 残指摘

### Critical

**[C1] ~~不変性の形式的定義がない~~**（Section 3.3）→ **[対応済み]**
    (AA(D_shift), J_R(D_shift)) の組を不変性評価の指標として Section 3.3 と 4.3 に明記。
    診断パターン（AA高+J崩壊=スプリアス、AA低下+J維持=非スプリアス）を記述。
    次回PEER_REVIEWで「この定義で反証可能性の問題が解消されているか」を確認すること。

**[C2] ~~「Reasoned model がスプリアス依存を複製することは自明では？」~~** → **[対応済み]**
    自明性を正面から認め、貢献を「定量的・体系的に検出できる枠組みの提供」に明示的に絞り込んだ。
    変更箇所: Section 1（問題提起段落）・Section 7（議論冒頭）に追記。
    次回PEER_REVIEWで「自明性の認め方が弱腰すぎないか／強すぎないか」を確認すること。

**[C3] ~~OOD ロバスト性文献との対比が欠落~~** → **[対応済み（方針転換）]**
    「OOD文献を引用してRL版と位置づける」ではなく「問いが根本的に違う」として正面から区別した。
    変更箇所:
    - Section 1 貢献リスト：「任意のReasonedモデルへの共通評価軸」「評価方法論の提供」を前面に出した
    - Section 2.3 末尾：OODとの目的の違い（ロバスト性向上 vs 評価方法論）を明示する段落を追加
    - Section 3.2：モデル非依存性（決定木/MoET/KAN何でも差し替え可）を明記
    - Section 7 末尾：本研究の本質が評価方法論の提供にあることを宣言する段落を追加
    次回PEER_REVIEWで「OODとの区別が査読者に伝わっているか」を確認すること。

### Major

**[M1] ~~不変性の判断基準が AA と J の間で揺れている~~** → **[C1と同時に対応済み]**
    Section 3.3 に診断パターン（AA高+J崩壊=スプリアス、AA低下+J非崩壊=非スプリアス）を明記。
    Section 4.3 で AA=再現性指標・J_R=不変性指標として並列定義。
    gravity_lo の J_R > J_I は「Intuitive policy の性能上限が条件依存」として Section 6.3 で説明済み。
    次回PEER_REVIEWで「各パターンの定義が結果の記述と一貫しているか」を確認すること。

**[M2] Section 4.4 がシフト下の AA を報告していない** → **[追加実験待ち]**
    [指摘]
    本枠組みの核心（再現性×不変性の二軸評価）なのに、予備実験では訓練分布上の AA のみ。
    重力条件を定義しておきながらシフト下の AA を測定していない。
    シフト下の AA と J も報告するか、主張を「蒸留の適用可能性の探索的確認」に限定する。

    [現状]
    metrics.csv に eval_condition 列はあるが AA はシフト後状態で再計算されていない
    （全条件で同値になっている）。J_reasoned は条件ごとに正しく計算済み。

    [対応方針]
    追加実験でシフト条件下の状態を収集して AA を再計算する。
    あわせて LunarLander DQN が未収束気味（J≈161、目標 J≧200）なのでステップ数も増やす。
    実験内容：
    - LunarLander: n_steps を 1M→2M 程度に増やして Intuitive を再学習（5シード）
    - Hopper: 現状 500k で MoET AA=0.706 は許容範囲、追加計算のみでも可
    - 各シフト条件（gravity_lo/gravity_hi）の環境でロールアウトして状態収集 → AA 再計算
    - draft Section 4.4 の Table 1 にシフト条件下 AA の列を追加

**[M3] Intuitive policy の学習品質が未報告** → **[追加実験待ち]**
    [指摘]
    CartPole の J=211.7 は解決基準（J≧475）に届いていない。言及も議論も皆無。
    全環境で学習曲線または最終性能を報告し、「十分に学習された方策の蒸留」であることを示す。
    または現状の J で十分とする理由を明示的に議論する。

    [対応方針]
    CartPole N=0 の DQN を 100k→500k ステップに増やして再学習（10シード）。
    影響範囲：exp001 N=0、exp003、exp004 N=0、exp006 N=0 を再走。
    N=4/8/16 はノイズによる J 低下として説明できるため再学習不要。
    文章対応：N>0 の J 低下は Section 5.1 か 8 に一文追記するだけでよい。

**[M4] ~~J が Section 4.3 の評価指標リストに含まれていない~~** → **[C1と同時に対応済み]**

**[M5] ~~多重比較補正が未実施~~**（Section 6.4, 6.5） → **[対応済み]**
    6.4節で約12回、6.5節で約27回の Welch t 検定を実施しているが Bonferroni 等の補正なし。
    p=0.039（MoET vs Tree, N=0）や p=0.027（Linear vs MoET, N=16）は補正後に非有意になる可能性大。
    Holm-Bonferroni 補正または FDR 補正を適用し、補正後 p 値を報告する。

**[M6] ~~循環性問題の過小評価~~** → **[対応済み]**
    Section 8 の限界4を拡充。「実問題では何をシフトすべきか自明でない」を認めた上で、
    既存手法（SHAP→依存特徴の候補提示、IRM→不変特徴との区別）を参照点として紹介。
    自分たちで実践ガイダンスを作るのではなく先行研究を示す形で対処。
    次回PEER_REVIEWで「循環性への対処が誠実に見えるか」を確認すること。

### Medium / Minor

**[Med1] ~~「構造ボトルネック」と概念ボトルネックの「ボトルネック」の差異の説明不足~~**（Section 2.3） → **[対応済み]**
    概念BNは人間定義概念を中間表現に使う。本研究のボトルネックはモデルクラスの表現力制限。
    質的に異なることを明示すると混乱が防げる。

    [対応方針]
    構造ボトルネックだよって明示

**[Med2] ~~N=16 で Linear が逆転する現象の考察不足~~**（Section 6.4） → **[対応済み]**
    [指摘]
    Linear(0.823) > MoET(0.810) > Tree(0.798) と「構造制約が強いほど再現性が高い」前提と矛盾する可能性。
    正則化効果 vs 表現力のトレードオフについて踏み込んだ議論が必要。
    ※ M5（多重比較補正）適用後に有意でなくなる可能性もある。

    [対応方針]
    M5適用後に有意でなくなったので、
    「構造制約の前提に矛盾する逆転」は統計的に裏付けなし、という方向で一文書く

**[Min1] ~~Arjovsky et al. (2019) の脚注番号 [^5] が本文で明示されていない~~** → **[対応済み]**
    [対応方針]
    どっかの修正のついでに引用箇所復活してた、なんなら多すぎるくらい。念のため脚注との対応を全部再確認

**[Min2] ~~Table 2 の J 値に標準偏差が記載されていない~~**（AA には記載あり） → **[対応済み]**
    [対応方針]
    データは exp002 にあるので計算して Table2のJ値 を書き換え

**[Min3] ~~「Intuitive policy」という命名がブラックボックスを指すため直感と逆~~** → **[対応済み]**
    一方が policy、他方が model という非対称性もある。意図的なら Section 3 あたりで理由を明記。

    [対応方針]
    これ「元アイデア」節の言い回しを引きずってるんですよね。今や直感って感じでもないですしmodelにあわせましょうかね

**[Min4] ~~Section 7 の AA 閾値感度分析が数値の記述のみで Table/Figure がない~~** → **[対応済み]**
    再現性のために数値を明示すること。

    [対応方針]
    追記をお願いします

**[Min5] ~~具体的な利用シナリオを議論・結論に追加する~~**（feedback3） → **[対応済み（C3修正で吸収）]**
    現状は「枠組みの提案」止まり。安全クリティカルRL・既存XRLパイプラインへの差し込み方など
    ひと段落の具体例を書くと「使える道具」として格上げされる。
    Section 7 の action flow 段落（スプリアス検出後の対処）と統合しても良い。

    [対応方針]
    min5もC3の修正で「横断比較」って書いたのでどうにかなってないかな？
    解決済みですよみたいな扱いで、また指摘されたら考えましょうかね

**[Min6] ~~pole_length の位置づけを明示する~~**（feedback2） → **[対応済み]**
    実験3で重力シフトとポール長変更を並べているが、「何が違う外乱か」の概念的区別が薄い。
    「重力は動的なスケーリング、ポール長は運動方程式そのものの変形」のように一文加えると
    「同じ物理パラメータシフトの仲間」ではなく「外乱の種類が違う二例」と読まれる。

    [対応方針]
    実験3の記述に「重力はスケーリング・ポール長は運動方程式の変形」という一文追加

**[Min7] ~~pole_long で J_reasoned >> J_intuitive となるメカニズムが未分析~~** → **[却下]**
    J_reasoned=254.0 vs J_intuitive=60.4。構造制約が OOD 汎化を促進している可能性があり、
    論文の主張にとってポジティブな知見になりうる。Section 7 か 8 で言及する。

    [対応方針]
    たまたまじゃないのかな。これで「汎化を促進している！」って主張するのは無理がありそう。
    一応残しとくけどほぼ却下で。

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
    - ここで初めて、あなたの“夢”に近い「人間と別ブラックボックスの双方に読める」方向へ接続できる。

    [所管] これもまだ先の話だねぇ

# 参考文献/先行研究

重複を少し整理して、この会話で実質候補として出たものを、**引用優先 / 勉強用 / 脇役**で並べました。大きくは、`説明付き知識蒸留・概念ボトルネック・代理モデル` の流れと、`対話的・共同構成的XAI` の流れに分かれます。[^1][^2][^3]

| Paper | Summary |
|---|---|
| Learning Global Additive Explanations of Black-Box Models | **Label: 引用優先.** Distills a black-box model into global additive explanations; the learned feature shapes are meant to preserve fidelity while staying interpretable. Good if you want to say your method is about *compressing behavior into a readable surrogate*, not just drawing local attributions. |
| ConceptDistil: Model-Agnostic Distillation of Concept Explanations (Sousa et al., 2022.) | **Label: 引用優先.** Uses knowledge distillation to bring concept explanations to any black-box classifier. This is one of the closest matches to your “human-readable intermediate representation” idea. |
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

# draftに不採用の指標

KL divergence
    行動分布間の乖離の補助指標。
    使おうとしたが、AAで十分だったため削除。AAでは説明できない場合は計算してみたら有意差ありなしを確認できるかも

Relative Performance Drop
    $\mathrm{RPD} = (J_I - J_R)/J_I$（$J$: 累積報酬）。不変性の補助指標。
    使おうとしたが、 $J_I$ と $J_R$ の比較で十分だったため削除。

Inv_J = J_R(D_shift) / J_R(D_train)
    Jの崩壊を直接捉えるが、pole_longでJ_R(train)→J_R(shift)の方向が逆転するケースで解釈が難しい

# 根幹となる主張
- 良し悪しを論じる方法自体を提供している。
- 説明可能性 vs 性能のトレードオフを回避できる
- モデル非依存の共通軸を提供する。説明可能性の定義が何であれフレームワークとして使えて、Reasoned の中身は何でも差し替えられる。
    決定木でも MoETでもKANでも、どれだけ Intuitive を再現できるか・シフトに強いかが共通の評価軸になりうる。

# 元アイデア

元アイデア:ブラックボックスのNN(Intuitive)の横に説明可能な何か(Reasoned)を置いて相互作用させたら、
人間が理解した気になる(Intuitiveだけ)のと説明できるように理解を深める(Intuitive+Reasoned)のとで"深さ"が違うんじゃないか。
RLやらの文脈の「説明可能」は人間を相手にしたものが多いが、必ずしも人間だけを相手にするんじゃなくて、
ブラックボックスが「説明可能」になったら別のブラックボックスに転移できるし人間も読める。
