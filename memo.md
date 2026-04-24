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

[M-01-B-05] ★★再指摘（三度目） Hopper 実験の Stage 1 / framing の問題
    [指摘]
        「Hopper では解釈可能 surrogate が高忠実性と機能的方策性能を同時に達成したケースが存在しない」ことが明示されていない。
        対応案: Limitations に「Hopper では高忠実性かつ機能的な surrogate を同時達成できたケースはなく、連続制御への適用は未検証のままである」と明記する。
    [方針] 一旦hopperでGBTでDAggerを試す、それでだめならいろいろ試す → memo_hopper.md
    [対応内容] exp016（GBT+DAgger）で R²=0.968±0.004・J_S=oracle比99.7% を達成。両基準を同時達成。付録5を入れ替え（日英両方）。指摘の「同時達成できていない」問題は実験で解消済み。
    [所感]

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
    [方針] 放置
    [対応内容] -
    [所感] 以前reviewで箇条書きが読みやすいと言われて変更した。査読者の好み。

[M-02-A-01] 実験2の設計がトートロジー的
    [指摘]
        Spurious GridWorld を p=0.0 で構成すると c が確定的にゴールを示す。
        この設定では任意の合理的な学習器が c に依存する。その依存を複製した Surrogate が
        c を反転すると失敗することは設計上自明（by construction）であり、
        提案フレームワークの有効性を独立に示す証拠になっていない。
        論文には言及があるが「なぜそれでも価値があるか」の説明が不十分。
        対応案: 「制御された環境での diagnostic criteria の動作検証」であることを明示し、
        フレームワークが既知の ground-truth を持つ設定で正しく機能することの証拠として位置づける。
    [方針] 仰せの通りに
    [対応内容] Section 6.2 冒頭に「設計上の帰結／groud-truth が明確な制御設定での動作確認」の位置づけを追記済み（日英両方）。
    [所感]

[M-02-C-01] ★再指摘 統計報告：AA の有意差が marginal かつ SD/CI の使い分けが不明確
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
        → 第3回再指摘（Rev C, MAJOR）: 95% CI [0.902, 0.982] を追記したが、
        CI 下限 0.902 が診断閾値 θ=0.9 を上回る幅はわずか 0.002 であることへの
        明示的な考察がない。さらに n=10, d=1.14 での検出力（約 0.55〜0.65）が
        未報告。中心的な統計的主張としてはこの脆弱性を開示すべき。
        対応案: CI 下限が閾値をわずかに上回るのみである旨を一言注記し、
        検出力の概算値（≈0.55〜0.65）を Section 6.2 または Section 8 に追記する。
    [方針] これは真摯に対応させていただきます
    [対応内容] [M-03-C-01] と同一対応として Section 6.2 に CI 下限（0.902 vs θ=0.9、差 0.002）と検出力（≈0.55〜0.65）を追記済み（日英）。
    [所感] 検出ってタイトルの論文で検出力の評価は確かに要る。先に言えという気持ちはあるが。

[m-02-B-01] ★再指摘 MoET が主要 surrogate だが広く普及していない
    [指摘]
        実験の大部分が MoET を primary surrogate として使用しているが、MoET は広く使われていない。
        モデル比較（Exp4・5）では MoET と Tree が GridWorld でほぼ同等の AA を示しており、
        MoET のゲーティング機構がこれらの小規模環境で付加価値を持つのか疑問。
        （Rev B）
        → 第3回再指摘（Rev B, Minor）: Section 7 に「Tree の reversed_c AA=0.887 が閾値未達
        のため MoET を primary として選択した」という記述を追加したが、これはデモに必要な
        結果を得るためにモデルを選んだという循環的な選択であり、診断基準が MoET の
        挙動に過適合している可能性を示唆する。
        対応案: この循環性を認めた上で「本実験では θ_AA = 0.9 の閾値設定のもとで
        MoET が唯一適格であることを確認した」と中立的に述べるか、
        あるいは閾値を 0.85 に下げれば Tree でも成立する点（Table 6）を示す。
    [方針] 挙げてくれた対応案のどっちもで
    [対応内容] Section 7 MoET 選択段落末尾に「θ_AA=0.85 に設定すれば Tree も基準を満たすことが感度分析（Table 6）で確認できる」/ "Note that Tree would also pass the criterion if θ_AA were set to 0.85, as confirmed by the sensitivity analysis (Table 6)." を追記（日英）。
    [所感] 場当たり対応が悪い方向に出ちゃいましたね

[m-02-B-02] IRM・概念ボトルネックとの実験比較なし
    [指摘]
        Related work で IRM と concept bottleneck を詳述しているが、実験比較がない。
        「IRM で oracle を再訓練して蒸留したら不変性はどうなるか」などの baseline があると
        提案フレームワークの実用的価値が明確になる。（Rev B）
    [方針] 却下
    [対応内容] -
    [所感] 再訓練の話はfuture workですわ。

[m-02-C-01] ★再指摘 J_S の t 検定が退化している
    [指摘]
        実験2 reversed_c の J_S は全 10 シードで -1.000（分散ゼロ）。
        この条件での Welch's t-test は分母がゼロとなり d>1000 は人工物。
        論文では「p_adj<0.001, d>1000」として有意差の証拠として示しているが、
        全値が同一という自明な事実に統計検定を適用することは不適切。
        対応案: 「全 10 シードで J_S=-1.000（分散ゼロ）、統計的にも自明」と記述し、
        Mann-Whitney U 等か、あるいは検定なしで記述する。（Rev C）
        → 第3回再指摘（Rev C, Minor）: Section 6.2・7 から d>1000 を削除して「全シード自明」に
        書き換えたが、他の箇所（pvalue_summary.csv 参照など）で J_S の p_adj < 0.001 が
        まだ参照されている可能性がある。分散ゼロの場合の p 値は完全に削除するか「退化ケース」と明示すべき。
        対応案: J_S の p_adj < 0.001 への参照をすべて削除または「分散ゼロにより t 検定は適用外」と注記。
    [方針] これは単に反映漏れですよね？反映して再確認で。
    [対応内容] 確認済み：draft.md・draft_en.md に J_S の p_adj<0.001 参照は残っていない（grep 確認済み）。対応完了。

[m-02-C-02] 実験横断での多重検定が未制御
    [指摘]
        各実験内では Holm-Bonferroni で補正しているが、実験 2・3・4・5・7 をまたぐ
        ファミリーワイズエラー率の制御については言及がない。（Rev C）
        対応案: 現状を明記（実験ごとに独立した family として補正）するか、
        全実験横断での補正を行う。
    [方針] 却下
    [対応内容] -
    [所感]
        マジ？そんなまたぎ方してエラー率計算できんの？すげぇ。すげぇけど意味あるんかその数字。
        実験横断補正はほぼ確実にp値を引き上げるため、論旨を強めれそうにない。

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

[m-03-X-03] ★★★再指摘（四度目） 主要主張が付録実験のみに支持されている
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
        → 第4回再指摘（Rev B, MAJOR）: 前回の格下げ後も Contribution 3 に
        「demonstrating a tendency for the evaluation axes to function consistently across
        multiple RL environments」という表現が残っており、main body の2環境のみでは
        「複数の RL 環境で一貫して機能する」という主張を支持しないと再び指摘。
        対応案: 「providing initial evidence that the two-axis evaluation logic applies
        beyond the primary experimental environments」等のより謙虚な表現に変更する。
    [方針] これも前回修正済みやと思ってたけど残っちゃってたってだけよね？修正の上全体を確認。
    [対応内容] Contribution 3 表現を修正（日：「複数のRL環境で一貫した評価軸として機能する傾向を示す」→「主実験環境を超えて評価ロジックが適用できるという初期的な証拠を示す」、英："demonstrating a tendency..."→"providing initial evidence that the two-axis evaluation logic applies beyond the primary experimental environments."）（日英）。
    [所感] 前々回と前回とで修正して全体を見直せって言ってない俺が悪いんか？

[M-03-A-01] フレームワークの非対称性が Abstract に明示されていない
    [指摘]
        「high invariance does not guarantee causal validity」と Section 3.3 には書いてあるが、
        Abstract では「identify states where AA is high but the explanation is wrong」とのみ述べており、
        「検出されなかった = 説明が正しい」が成立しないという非対称性が伝わらない。
        フレームワークは spurious dependency の検出器であり、その不在の確認器ではない。（Rev A, MAJOR）
        対応案: Abstract に「the framework detects spurious dependencies but cannot confirm their absence」
        を一文追加する。
    [方針] 仰せのままに
    [対応内容] Abstract 末尾に「なお、本枠組みはスプリアス依存を検出するが、その不在を確認する機能は持たない。」/ "Note that this framework detects spurious dependencies but cannot confirm their absence." を追記（日英）。

[M-03-A-02] 分布シフト選択の指針がフレームワーク本体にない
    [指摘]
        フレームワークを使うには「何をシフトするか」を決める必要があるが、その方法論が
        Limitations の2文に留まり、フレームワーク記述（Section 3.3 or 4）に組み込まれていない。
        SHAP 重要度をシフト候補の優先順位付けに使うというヒューリスティックは有用であり、
        フレームワークの推奨実践として格上げすべき。（Rev A, MAJOR）
        対応案: Section 3.3 または Section 4 に「SHAP 重要度でシフト候補を優先する推奨実践」を追加。
    [方針] 放置
    [対応内容] -
    [所感] 具体的な方法ってのはこの論文で扱いきれないですfuture workです

[M-03-B-01] Hopper で高忠実性と機能的性能を同時達成した surrogate が存在しない
    [指摘]
        BC surrogate (RegTree d=12) は R²=0.922 で Stage 1 通過だが J_S = 4.5%（機能的方策性能なし）。
        DAgger surrogate は J_S = 63% だが AA_ε = 0.420（Stage 1 基準を大きく下回る）。
        つまりどの surrogate も高忠実性と機能的方策性能を同時には満たしていない。
        この事実が論文で明示されておらず、「preliminary validation」という表現が楽観的すぎる。（Rev B, MAJOR）
        対応案: Limitations に「Hopper では提案フレームワークの両基準を同時に満たした解釈可能
        surrogate は得られなかった」と明記する。
    [方針] AA_epsilonは補助指標であってDAgger surrogate R^2>0.9を満たしている。書き方を整える程度で。
    [対応内容] exp016（GBT+DAgger）で両基準を同時達成（R²=0.968±0.004、J_S=oracle比99.7%）。付録5を全面入れ替え。「両基準を同時達成できなかった」旨の記述はすべて削除済み（日英）。
    [所感] Hopperへの適用はサブ中のサブな上、この難易度の問題を解けるsurrogateがないのが問題なので本論文でどうこうできる範疇ではない。

[M-03-C-01] 検出力（power）の未報告
    [指摘]
        Experiment 2 の中心的な統計的主張（AA, p_adj=0.030, n=10, d=1.14）に対して
        検出力分析が行われていない。n=10, d=1.14, α=0.05 での両側 t 検定の検出力は約 0.55〜0.65 であり、
        35〜45% の確率で真の効果を見逃しうる。これはフレームワーク論文の中心的な実証であるため
        開示が必要。（Rev C, MAJOR）
        対応案: Section 6.2 または Section 8 に検出力の概算値（≈0.55〜0.65）を一文で追記する。
    [方針] 追記
    [対応内容] Section 6.2 に CI 下限注記（0.902 vs θ=0.9、差 0.002）と検出力（n=10, d=1.14, α=0.05 → 約 0.55〜0.65、真の効果見逃し率 35〜45%）を追記（日英）。[M-02-C-01] と同一箇所への対応。
    [所感] こーれはちゃーんと対応したい。「検出」ってタイトルの論文で検出率が書いてないのはダメな感じがする。

[m-03-A-01] 「不変性」の用語が IRM の意味と混同される可能性
    [指摘]
        Section 2.3 で IRM の「不変性」と本論文の「不変性」を区別しているが、
        本文全体では「invariance」が緩やかに使われており、IRM 文献に詳しい読者が混乱しうる。
        対応案: Section 3.3 の初出箇所に「本論文での invariance は AA と J_S の分布シフト後の
        維持を指し、IRM の表現不変性とは異なる」という注記を追加する。（Rev A, Minor）
    [方針] おおせのままに
    [対応内容] Section 3.3 末尾（診断ツールの説明文の後）に「ここでの不変性は AA・J_S の分布シフト後の維持を意味し、IRM（Arjovsky et al., 2019）の不変特徴表現とは異なる概念である」旨を追記（日英）。

[m-03-A-02] 検出から対処へのギャップが実証されていない
    [指摘]
        Section 7 で remedial actions（特徴除去・報酬設計変更・IRM 再訓練）を列挙しているが、
        いずれも実証していない。検出の実用的価値を主張するなら、
        少なくとも1つの対処手順の概念的なデモがあると説得力が増す。（Rev A, Minor）
    [方針] 却下
    [対応内容] -

[m-03-B-02] 実世界環境への適用可能性の議論がない
    [指摘]
        全実験がシミュレータ（既知の力学・制御可能なシフト）であり、
        実世界 RL（ロボティクス・推薦システム等）では spurious feature が事前に不明で
        分布シフトが制御できない。この制約への議論がない。（Rev B, Minor）
        対応案: Limitations に実世界適用時の制約（未知の spurious feature、
        制御不能なシフト）について短く言及する。
    [方針] 却下
    [対応内容] -

[m-03-C-02] ±表記が SD か SE か明記されていない
    [指摘]
        主要結果で mean ± SD を使っているが、初出箇所に「± は標準偏差（SD）」と明記していない。
        95% CI を別途報告するようになったため、± の意味を一度注記することで混乱を防げる。（Rev C, Minor）
        対応案: Section 5.1 か Section 6 の最初の ± 表記の近くに「mean ± SD を表す」と明記。
    [方針] まあ書き足すだけならそれで
    [対応内容] 確認済み：Section 5.1 冒頭に「mean ± standard deviation」（日本語：平均±標準偏差）と明記済み。対応完了。

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
