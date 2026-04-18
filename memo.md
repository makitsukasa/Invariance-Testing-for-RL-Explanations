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

[C-rv01-C-01] 主要主張に形式的統計検定なし
    [指摘]
        中心的な主張（スプリアス vs 非スプリアスの識別）に対して、p値・効果量・信頼区間が報告されていない。
        exp003 の J_oracle=428.1±148.5 のような大きな分散は、formal test の欠如をより深刻にする。
        現状は exp004/005 の一部（Holm-Bonferroni 補正済み p 値）のみが報告されている。
    [方針] 記載する。ただし実験の整理が先。
    [対応内容] 対応済み。pvalue_summary.csv（compute_pvalues.py で再生成）を元に以下を draft.md に追記:
        - Section 6.2: exp002 train vs reversed_c の AA (p_adj=0.030, d=1.14) と J_S (p_adj<0.001) を明記
        - Section 6.3: exp003 pole_long AA 有意差 (p_adj=0.0004, d=2.65)・他条件は非有意を明記
        - Section 7: 統計検定の概要段落を追加
        - Section 8 限界: 「統計検定が必要」→「補正後非有意条件の解釈注意」に更新
        - 付録4: exp009 gravity_lo AA/J_S の有意差 (p_adj<0.001, d≈3.3) を追記
    [所感]
        書けっていうんならやぶさかでない。嘘はついてないし隠すことはないので。
        ただ整理ができてない。その場でclaudeがpython書いて出した値もちょこちょこあるので先に整理したい。

[C-rv01-X-01] 語数が NeurIPS 目安（5,000〜6,500語）に対して不足
    [方針] 付録に書いた実験設定とかを本文へ戻すとか？
    [対応内容] 未対応
    [所感]
        まあ普通これくらいの長さがいいっていう基準があるんであれば従って損はないでしょうけど
        ところで英訳してないのに語数ってなんの話？

[C-rv01-X-02] 参考文献リストの形式
    [指摘] 脚注スタイル（[^n]）は Markdown 表記では問題ないが、投稿フォーマット依存。提出先のテンプレートに応じて調整。
    [方針] 対応しない
    [対応内容] -
    [所感] 投稿の予定はございませんでして。

[M-rv01-A-01] exp001 の数値が論文本文と実験ファイルで食い違い
    [指摘]
        Section 6.1 の記載: N=0,K=4,d=5: AA=0.915±0.028。
        summary.txt の実測値: AA=0.910±0.016。
        N=16,K=4,d=5 も 0.819 vs 0.809 で食い違い。
        異なるシードセットで取った数値を混在させているのが原因。論文内の数値は単一の実験ランからトレースできなければならない。
    [方針] 実験結果を整理(所感を参照)
    [対応内容] 対応済み。exp001系ディレクトリを未使用と整理し、実験1・実験4 の正規ソースを exp004 に統一。
        Section 6.1 の N=16 値を exp004 に合わせて 0.819±0.033 → 0.820±0.032 に修正。
        EXPERIMENT_MAP.md に記録済み。
    [所感]
        これ一回指摘されて走らせ直したんじゃなかったっけ？004か何かの結果を001に書いてたはず。
        exp001が実験1に書いてあると思ってエージェントに渡したんならそりゃ食い違うかもね。
        まあ実験結果を整理しておくべきという指摘だと思いましょうかね。

[M-rv01-A-02] Hopper の R² 値が実験ファイルにトレースできない
    [指摘]
        exp011/exp012 の summary.txt は AA のみ記録しており、論文が主張する R²=0.920±0.009 (d=12) や
        R²=0.698±0.009 (d=5) の出所が不明。R² はおそらく action_diffs NPZ から事後計算したものだが、
        その計算スクリプトが残っていない。
    [方針] 要対応
    [対応内容] 対応済み。experiments/scripts/compute_r2.py を作成。
        action_diffs/*.npz から sklearn.metrics.r2_score(multioutput='uniform_average') で計算。
        exp011/r2_summary.csv・exp012/r2_summary.csv に出力済み。
        exp011 は標準10シード再実行後の値: RegTree train R²=0.922±0.008（旧0.920±0.009）。
        draft.md も新値に更新済み。
    [所感]
        R² は sklearn の r2_score(oracle, pred, multioutput='uniform_average') で計算した。
        再計算スクリプトを残すか、summary.txt を再生成するかどちらかが必要。

[M-rv01-A-03] LunarLander（実験7）は 5 シードなのに本文に「10 シード」と書いてある
    [指摘]
        Section 5.1 で「各条件は乱数シード10本で実行」と宣言しているが、
        exp009（LunarLander）の実験ファイルには 5 シード分のデータしかない。矛盾。
        対応案:Section 5.1 か Section 5.5 のLunarLander段落で「各 5 シード」と明記するのが最小コスト対応。
    [方針] 全実験を10シードで統一
    [対応内容] 対応済み。exp009 を LunarLander 専用 config（hopper セクション削除）に整理し、
        標準10シード（42〜2526）で再実行。metrics.csv・summary.txt を10シード値で更新。
        draft.md の付録4 Table A6・本文数値（AA=0.870±0.021、J_S=237）も更新済み。
    [所感] わかりやすさを優先したい

[M-rv01-B-01] 検出後の対処法が論文に記載されていない
    [指摘]
        論文自身が「検出と対処の組み合わせで初めて実用的意義を持つ」と述べているにもかかわらず、
        スプリアス検出後の具体的な対処法（IRM再学習・特徴選択・正則化蒸留など）が議論されていない。
        読者は「で、どうすればいいのか」と感じる。
    [方針] 過去のdraft.mdに「気付きを与える。具体的な対処法は知らん。」ってかいてあったはず。記載を探して復活させる。
    [対応内容] 対応済み。旧バージョン（commit 2077ed2）の文章を復活。
        「スプリアス特徴の除去・環境再設計・IRM 再訓練」を後続アクション例として明示しつつ、
        「本研究では実証的に評価していない」と範囲を限定する記述に戻した。
    [所感]
        読者は「で、どうすればいいのか」と感じる。←ちょっとおもしろい。勝手に感じてろ。

[M-rv01-B-02] Hopper の J_S が oracle の 5〜10% しかなく、不変性評価が成立していない
    [指摘]
        RegTree d=12 の R²=0.920 は再現性の証拠だが、J_S が oracle の 5〜10% にとどまる（訓練分布上ですら機能しない）。
        これでは「分布シフト下での J_S 維持」という不変性の評価が意味をなさない。
        現状、Hopper 結果は枠組みの強さではなく弱さを示している。
        対応案:付録5でのフレーミングをもう少し「限界・今後の課題」寄りにするのが現実的か。
    [方針] J_Sを維持できる実験条件を模索。Surrogateのモデルを変更、蒸留時間を伸ばす、など。
    [対応内容] 未対応
    [所感]
        これは枠組みの弱さを示しているんじゃなくてうまく蒸留できないsurrogateの弱さを示している。とはいえこんなの言い訳に聞こえるでしょうな。
        学習時間を伸ばすとかで対応できないかしら

[M-rv01-C-02] exp003 で収束失敗シードが統計を汚染している
    [指摘]
        J_oracle=428.1±148.5 の変動係数は約 35%。10 シード中 2 シードが収束に失敗していることが原因。
        収束失敗 oracle を含む統計は AA・J_S の平均と分散を歪める。
        対応案:閾値（J≥450）以上のシードのみで再集計する「フィルタ済み」値と、全シードの値を両方報告するのが誠実。
    [方針] 対応案の通りで
    [対応内容] 対応済み。seed=2223（J=159.2）と seed=2526（J=134.0）が収束失敗と特定。
        Table 2 を全10シード／収束8シード（J≥450）の2行構成に更新。
        収束8シードでは J_oracle の分散が大幅縮小（train: 148.5→3.8）し AA も若干上昇するが、
        主要な結論（壊滅的崩壊なし、スプリアスなし判定）は変わらない旨を本文に明記。
        Table 6 の感度分析行も全10シード/収束8シードの2行構成に更新。
    [所感]
        「汚染している」って言い回しをするんですね
        10シードで実験した、っていうわかりやすさがちょっと削れるけどやむ無し。

[M-rv02-X-01] フレームワークの新規性が薄い
    [指摘] 標準的な OOD 評価を XRL に適用しただけ、との指摘。
    [方針] 部分対応済み。これ以上の対応は保留。
    [対応内容] Section 2.3 で事後診断 vs. 訓練戦略の差別化を記述済み。序論に新規性 1 文追加済み。
    [所感] ここまではっきり書いてダメならもうしょうがないかなぁ。

[m-rv01-A-04] exp012 の summary.txt の標準偏差が ±nan
    [指摘] 集計スクリプトのバグ。再現性の懸念。
    [方針] 実験の整理の後で再確認
    [対応内容] 対応済み。1シードのみ集計していたバグを修正し、全10シードで再集計。
        exp012/summary.txt: RegTree train AA=0.649±0.016 に更新済み。
    [所感]

[m-rv01-A-05] MoET エキスパート木の可視化が seed=42 単一シードのみ
    [指摘] 「全4エキスパートが同一構造」という主張が 10 シード全体で検証されていない。
    [方針] (考えます)
    [対応内容] 未対応
    [所感] これって全部示さんとダメなの？今直書きだけど語数制限とかがあるなら図にする？

[m-rv01-B-03] GridWorld 環境が現象を示すために設計されている
    [指摘]
        p=0.0 の c は決定論的にゴールを指す——実世界のスプリアス相関はこれほど綺麗でない。
        対応案:p=0.2/0.5 の結果を部分的スプリアスとして明示することでカバーできるとして許容する。
    [方針] (考えます)
    [対応内容] 未対応
    [所感] まあ確かにそうなんだよな。さーすがにもうちょっとマシな実験考えるか？でもうまいこと主張できてるんだよな

[m-rv01-B-04] 序論の Mindlin (2025) 引用が本文中で孤立している
    [指摘]
        対話的説明への言及が序論のみで、議論で拾われていない。
        対応案:削除もしくは Discussion で回収する
    [方針] (考えます)
    [対応内容] 対応済み。Section 2.4 末尾に 2 文追加。
        「対話の前段として分布変化への有効性を自動評価しておくことが土台を与える。本枠組みはその前段評価として機能しうる。」
        Section 7 での回収より Section 2（関連研究）のほうが自然な位置と判断。
    [所感]
        ダメなの？引用ってそんなもんじゃない？
        「Discussionで回収」って7章のこと？そこは違うんじゃない？
        やるとしたら2章にちょっと書くとか？人間で評価する前にシフトだけ見とこうぜみたいな感じで

[m-rv01-C-04] α 感度分析（Table 7）が自明すぎる
    [指摘] スプリアス条件の J_S/J_train が −1.03 と 0.06 なので、どの α でも検出される。境界ケースがない。
        対応案:（説明として許容範囲内）
    [方針] 実験4以降も表に入れてみる
    [対応内容] 対応済み。Table 7 に実験7（LunarLander GBT）の gravity_hi/gravity_lo 行を追加。
        gravity_lo は J_S 比=0.58 と閾値付近まで低下するが AA=0.712 < 0.9 のため非検出。
        AA 条件と J_S 条件の組み合わせ判定の挙動が見えるようになった。
        合わせて draft.md 全体の exp002/003/... 表記を「実験2/3/...」に統一。
    [所感] うーんたしかに言う通りなんやこの表は。何も考えずに査読に入れてるのがバレた。

[m-rv01-C-05] 多重比較補正の手法名が inconsistent
    [指摘] exp004 で「Holm–Bonferroni 補正」と書いているが、他の実験での補正方法が明示されていない。
    [方針] 要確認・統一
    [対応内容] 対応済み。付録3の「t-test $p<0.01$」を「Welch $t$ 検定 $p_\text{adj}<0.01$」に統一。
        その他の箇所はすでに「Welch $t$ 検定（Holm–Bonferroni 補正）」で統一されていることを確認。
    [所感]

[m-rv02-X-02] コンピュートリソース・学習時間の記述なし
    [指摘] コンピュートリソース・学習時間を記載するべき。再現性要件にかかわる。
    [方針] 放置
    [対応内容] 未対応
    [所感] 実測値を残してなかったので放置でいいや。学習済みモデルですし、蒸留の回数は書いてあるし。

[m-rv03-X-01] 要旨・序論の主張が強すぎる
    [指摘]
        「説明可能性と性能のトレードオフを回避する」は一般命題として強すぎ。「診断する」「評価する」が安全。
        推奨テキスト（要旨主文）:
        「本研究は、学習済み RL 方策に対し、AA と分布シフト下の不変性を用いて Surrogate model の
        説明品質を事後評価する枠組みを提案する。この枠組みは decoupling により Oracle policy を
        変更せず、任意の解釈可能モデルを比較できる。」
    [方針] 所感の通り修正（検討中）
    [対応内容] 対応済み。要旨冒頭を「説明可能性と性能のトレードオフを回避する」から
        「性能を低下させることなく任意の解釈可能モデルの説明品質を事後的に診断する枠組みを提案する」に変更。
        「回避する」→「診断する」の方向で、実際に何をするかをより正確に表現。
    [所感]
        要旨の「トレードオフを回避する」と序論の「診断する枠組みを提案する」が微妙にずれてる感はある。
        でも実際トレードオフは回避できてるんですよね。
        「性能を低下させずに説明可能性を後付けし、それが真に説明と言えるかを診断する」みたいなニュアンスで書くのがいいかな。
        結論の1行目とかがそれっぽい感じに見える。

[m-rv03-X-02] 序論の新規性が 3 点に分散
    [指摘]
        1) decoupling の設計、2) AA + 不変性の二軸評価、3) 任意 surrogate の比較基盤 — が並列で読め、
        「何が新規性の中心か」が一意に決まらない。対策案: 主文を 1 本に絞り、残り 2 点を補足へ。
    [方針] 不採用
    [対応内容] 未対応
    [所感] 並列なんですから並列で読んでくれて結構。

[m-rv03-X-03] 実験 4〜7 の記述が「補強」の分量を超えている
    [指摘] 主たる主張のための数値実験と、副として複数モデルへの応用可能性を検証する実験を分けるべき
    [方針] 実験1〜3が並列の主実験、実験4〜8が並列の追加実験として再構成。
    [対応内容] 対応済み - Section 5.5 を「追加実験（5段落）」に改編、6.4/6.5 を付録1〜5へ移動。

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
