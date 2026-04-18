draft.mdには入らないがメモしておきたい事柄を本ファイルに記載。

# TODO - 実験以外

## draft.md 構造改編計画

主たる主張のための数値実験と、副として複数モデルへの応用可能性を検証する実験を分け、論旨を伝わりやすくする。

### 目標構成

```
5. 実験
  5.1 実験の目的と主張との対応  ← ほぼ現状維持（実験7→8の番号更新のみ）
  5.2 実験1：CartPole ノイズ拡張
  5.3 実験2：Spurious GridWorld
  5.4 実験3：CartPole 物理シフト
  5.5 追加実験（実験4〜8）     ← NEW: 5本を各1段落にまとめる
  5.6 実装詳細とハイパーパラメータ  ← 現5.7をリナンバーするだけ

6. 結果
  6.1 実験1
  6.2 実験2
  6.3 実験3
  ← 現6.4・6.5は削除（付録へ移動）

7. 議論   ← 付録参照に書き換え
8. 限界   ← 同上
9. 結論

付録
  付録1. 実験4：CartPole モデル比較
  付録2. 実験5：GridWorld モデル比較
  付録3. 実験6：蒸留データ量の感度分析
  付録4. 実験7：LunarLander-v3 への拡張   ← 旧「実験7 LunarLander部分」
  付録5. 実験8：MuJoCo Hopper-v5 への拡張  ← 旧「実験7 Hopper部分」
```

### 作業ステップ（順番通りにやること）

1. **実験番号の確定**
   - 旧「実験7 LunarLander」= 実験7（変更なし）
   - 旧「実験7 Hopper」= 実験8（新番号）
   - Section 5.1 の目的5番を「実験7・8」に更新

2. **Section 5.5 の書き換え**
   - 現5.5（実験4〜6設定）+ 現5.6（実験7設定）を削除
   - 新5.5「追加実験（実験4〜8）」として5段落新規作成：
     - 実験4（1段落）：CartPole N=0,4,8,16 でMoET/Tree/Linear比較
     - 実験5（1段落）：GridWorld p=0,0.2,0.5 で同三種比較
     - 実験6（1段落）：蒸留データ量 n∈{1k,5k,10k,20k} 感度分析
     - 実験7（1段落）：LunarLander-v3、PPO oracle、GBT追加
     - 実験8（1段落）：Hopper-v5、TD3 oracle、RegTree/EBM/SDT、ε-agreement/R²
   - 各段落末に「詳細は付録N参照」を付ける

3. **Section 5.6 リナンバー**
   - 現5.7「実装詳細とハイパーパラメータ」のヘッダーを5.6に変更

4. **Section 6.4・6.5 を削除**
   - 現6.4（実験4〜6結果）を丸ごと付録1〜3へ移動
   - 現6.5（実験7結果）を LunarLander部分→付録4、Hopper部分→付録5 に分割移動
   - 移動先で Table 1（LunarLander）・R²比較（Hopper）の番号を付録内表番号に更新

5. **Section 7（議論）・8（限界）の参照書き換え**
   - 「Section 6.4」「Section 6.5」「実験4〜7」などへの参照を付録N参照に変更
   - 具体的な数値引用（AA=0.876, R²=0.920 等）はそのまま残してよい

6. **全文「実験7（Section 6.5）」等の残存参照をgrepして修正**
   - grep対象: "実験7", "Section 6.4", "Section 6.5", "6.5節"

7. **付録の新設**
   - draft.md末尾（引用文献の後）に付録1〜5を追加
   - 各付録 = 現在の対応セクションの内容をほぼそのまま移動
   - 付録4と付録5は現6.5を LunarLander/Hopper で分割して配置

### 注意点
- Table 1（LunarLander比較表）は付録4内に、Hopper R²表は付録5内に置く
- 本文中で数値を引用する場合は「付録4 Table A3」などの形式で参照
- 実験7と実験8の split は「7-L / 7-H」ではなく「実験7 / 実験8」として統一

---

### 残対応項目

**[旧M1] フレームワークの新規性が薄い** → **[部分対応・保留]**
    標準的な OOD 評価を XRL に適用しただけ、との指摘。
    Section 2.3 で事後診断 vs. 訓練戦略の差別化を記述済み。序論に新規性 1 文追加済み。

    [所感] ここまではっきり書いてダメならもうしょうがないかなぁ。実際そういう側面はあるし、これ以上言い換えしづらいし。

**[旧Minor] コンピュートリソース・学習時間の記述なし（再現性要件）** → 未対応（実測値なし）

**[reviews2-A1] 要旨・序論の主張が強すぎる** → 要確認
    「説明可能性と性能のトレードオフを回避する」は一般命題として強すぎ。「診断する」「評価する」が安全。
    推奨テキスト（要旨主文）:
    「本研究は、学習済み RL 方策に対し、AA と分布シフト下の不変性を用いて Surrogate model の
    説明品質を事後評価する枠組みを提案する。この枠組みは decoupling により Oracle policy を
    変更せず、任意の解釈可能モデルを比較できる。」

**[reviews2-A2] 序論の新規性が 3 点に分散** → 要確認
    1) decoupling の設計、2) AA + 不変性の二軸評価、3) 任意 surrogate の比較基盤 — が並列で読め、
    「何が新規性の中心か」が一意に決まらない。
    対策: 主文を 1 本に絞り、残り 2 点を補足へ。

**[reviews2-A3] 実験 4〜7 の記述が「補強」の分量を超えている** → **[作業計画済み・未実施]**
    実験1〜3が並列の主実験、実験4〜8が並列の追加実験（設計上は「別格」）として再構成する。
    詳細は下記「draft.md 構造改編計画」参照。

---

# TODO - 実験

この原稿をフルペーパーとして強くするには、次の実験がいいらしいです。

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

連続制御用のタスクを離散制御
    Jが低くなる。そりゃそうだ。
    連続制御をしようとするとAAの定義を連続用に作り直さなきゃだけど仕方ない。

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
    わざと弱いoracleを使う exp007にある学習回数の足りてないhopperのoracleとか

# 元アイデア

元アイデア:ブラックボックスのNN(Intuitive)の横に説明可能な何か(Reasoned)を置いて相互作用させたら、
人間が理解した気になる(Intuitiveだけ)のと説明できるように理解を深める(Intuitive+Reasoned)のとで"深さ"が違うんじゃないか。
RLやらの文脈の「説明可能」は人間を相手にしたものが多いが、必ずしも人間だけを相手にするんじゃなくて、
ブラックボックスが「説明可能」になったら別のブラックボックスに転移できるし人間も読める。
