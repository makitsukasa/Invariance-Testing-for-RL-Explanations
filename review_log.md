[#008-H-001] Abstract / Introduction 末尾で新規性の二点をもう一度だけ明示すると刺さりやすい
    [関係] [#004-G-001], [#004-I-001], [#005-I-001] の再指摘。
    [方針] 「既存研究は候補発見、PerformanceCheck は後段確認」という点と、「寄与度ではなく性能低下量 Δ で依存を定義する」という点を、要旨と序論の最後で短く再強調する。
    [対応] 完了。序論末尾で主たる貢献と補助的貢献を言い直し、PerformanceCheck の位置づけを再明示した。
[#008-H-002] Results の Q1-Q5 と各実験の対応をさらに見えやすくする
    [関係] 新規指摘。ただし [#008-I-002] とは方向が逆。
    [方針] Results 冒頭に「本節は5つの問いに答える構成」と明示し、各 Q の先頭 1 行を視認しやすくする。
    [対応] 完了。Experiments 冒頭に五段階の確認項目を prose でまとめ、Results は通常見出しへ戻した。
[#008-H-003] シリーズ研究としての統合先を Discussion / Conclusion の最後で 1-2 文だけ示す
    [関係] [#005-I-001] の再指摘。
    [方針] 候補発見→依存確認→シフト提案までを一体の半自動パイプラインへ統合する今後の課題を、結びに短く入れる。
    [対応] 完了。Discussion / Conclusion で、Waterbirds のような小さな候補集合では半自動パイプラインが事実上ほぼ構成できていることと、大きな環境への拡張を今後の課題とすることを追記した。
[#008-H-004] 「どの特徴をシフトすべきか」という設計問題は別稿で扱うと明記すると守備範囲が明確になる
    [関係] [#007-A-002] と近い論点。主張を弱める方向なので、ユーザ意向とやや緊張あり。
    [方針] Limitations に 1 文足して、本稿は候補列挙から Δ 計測までを主に扱い、シフト設計自体は次段の課題だと示す。
    [対応] 完了。Limitations に、本稿が主に扱うのは候補列挙の後から Δ を計測する段階までであり、シフト設計自体は別段の課題であると追記した。
[#008-I-001] 論文が少し盛りすぎに見えるので、主軸と補助実験の従属関係をさらに明確にしたい
    [関係] [#005-A-003], [#007-A-001] の再指摘。ユーザは [#007-A-001] を却下済み。
    [方針] 主軸を「候補発見後の確認」「PerformanceCheck の有効性」「SHAP との違い」に固定し、CLIP/SSL や WGA などは補助証拠として位置づけを弱める。
    [対応] 完了。主軸を確認手続きと SHAP 比較に置き、候補発見接続や CLIP / 自己教師あり表現は補助的な証拠として位置づけ直した。
[#008-I-002] Q1-Q5 の見出しは実験メモ感が強く、最終稿では通常の見出しへ戻したい
    [関係] 新規指摘。ただし [#008-H-002] とは方向が逆。
    [方針] Results を `GridWorld / ColoredMNIST / Waterbirds / 接続評価` などの通常見出しへ再編し、Q5 は本文で圧縮、詳細は付録に送ることを検討する。
    [対応] 完了。Results の Q1-Q5 見出しを通常の節見出しへ戻し、実験メモ感を薄めた。
[#008-I-003] 中心命題を「出力・スコア・役割」の三点に固定すると全体が締まる
    [関係] [#005-H-001], [#004-G-001] の再指摘。
    [方針] 出力=`候補の順位リスト`、スコア=`機能的必要性の近似値 Δ`、役割=`候補発見の後段に置く確認・優先順位づけ` の三点へ用語を統一する。
    [対応] 完了。手法導入部に、出力を候補の順位リスト、スコアを Δ、役割を後段確認と優先順位づけとして読む説明を追記した。
[#008-I-004] 用語の反復がやや多い
    [関係] [#005-E-001] の再指摘に近いが、より局所的な文体指摘。
    [方針] `訓練済みモデル` は初出後 `モデル` に寄せ、`寄与度推定法` の多用を減らし、`依存 / 機能的必要性 / 因果効果` の切り分けを一度定義した後は繰り返しすぎない。
    [対応] 完了。序論・手法・要旨で `訓練済みモデル` や `寄与度推定法` の反復を減らし、以後は `モデル` や文脈依存の短い表現へ寄せた。
[#008-I-005] Waterbirds の CLIP / SSL は主題を候補発見側へ引っ張りやすい
    [関係] [#007-A-001] の再指摘。加えて [#006-F-001] の「CLIP vs SSL の解釈を厚くする」とは少し緊張関係にある。
    [方針] 本文に残すなら「表現が違うと候補順位が変わるので後段確認が要る」という一文へ役割を固定し、厚みを出しすぎない。
    [対応] 完了。CLIP / 自己教師あり表現の段落に、表現が違うと候補順位が変わるので後段確認が要る、という役割を固定する一文を補った。
[#008-J-001] 新規性の強調がまだ抽象的で、実務・研究上どう変わるかの具体像を足したい
    [関係] [#008-H-003], [#005-I-001], [#004-B-001] の再指摘。
    [方針] 序論と結論で、候補発見の誤警報を Δ で絞り込み、修正優先順位づけへつなぐ具体例を 1 文ずつ足す。
    [対応] 完了。序論と考察で、候補発見→確認→人手判断の具体的な三段の流れを prose で明記した。
[#008-J-002] SHAP まわりの表現にまだ強すぎる箇所が残る
    [関係] [#007-B-001], [#006-A-002], [#004-H-004] の再指摘。
    [方針] `大幅に下回る` や `機械的に一致` のような表現を、証拠ベースの中立的な言い回しに寄せる。
    [対応] 完了。SHAP の記述を「本稿で採用した集約規則の下で」「性能低下を判断材料にしていない」といった証拠ベースの表現へ寄せた。
[#008-J-003] Discussion が長く、同じ workflow 説明や役割説明の反復が残る
    [関係] [#005-I-003], [#005-H-003], [#004-B-001] の再指摘。
    [方針] workflow は 1 パラグラフに圧縮し、同趣旨の説明を Results / Discussion / Conclusion の間で整理する。
    [対応] 完了。workflow の繰り返しを抑え、接続評価の役割説明は 1 パラグラフへ寄せた。
[#008-J-004] 図キャプションが冗長で、本文と役割が競合している
    [関係] [#005-H-003], [#005-I-003] の再指摘。ただし [#003-F-001], [#004-F-002] の「自己完結的キャプション」とは少し緊張関係にある。
    [方針] キャプションは 1-2 文で要点だけにし、解釈文は本文へ戻す。
    [対応] 完了。各図のキャプションを 1-2 文へ圧縮し、解釈は本文側へ寄せた。
[#008-J-005] Related Work と Method に重複・データセット固有の詳細がまだ残る
    [関係] [#005-I-003] の再指摘に近い。
    [方針] IRM / GroupDRO / 反事実不変性の説明を圧縮し、ベンチマーク細部や SHAP 集約の帰結は Method / Discussion の役割に応じて再配置する。
    [対応] 完了。Related Work の訓練側手法の説明を圧縮し、Waterbirds のモデル構成説明は Method 側へ寄せて重複を減らした。
[#008-J-006] Results の解釈が一部先走り気味で、考察に送れる文がある
    [関係] [#005-I-003], [#005-H-003] に近い再指摘。
    [方針] GridWorld や SHAP の構造的解釈は、表と図で事実を述べた後、考察へ少し送る。
    [対応] 完了。接続評価の Results では数値事実を中心に残し、候補発見と確認の役割差に関する解釈は Discussion へ寄せた。
[#008-J-007] exp021 の不一致 12/30 を明示し、その保守性を false positive 低減として読ませたい
    [関係] [#003-E-002], [#007-B-002] の再指摘に近い。
    [方針] Waterbirds の不一致数を本文で明示し、候補の存在検知に対して PerformanceCheck がより保守的であることを、誤警報低減の観点でも短く述べる。
    [対応] 完了。Waterbirds の不一致数 12/30 を本文で明示し、PerformanceCheck の保守性を誤警報低減の観点でも読めるよう補った。
[#008-J-008] 高次元スケーラビリティの課題と pruning の乖離リスクをもう一段具体化したい
    [関係] [#000-X-004], [#000-X-006] の再指摘。
    [方針] 計算量 `O(|F|*|D|)` 相当の負荷と、候補絞り込み後介入が主張を近似に変えるリスクを Discussion / Limitations で明示する。
    [対応] 完了。Limitations に高次元設定の総当たりコストと候補絞り込み後介入の取りこぼしリスクを明記した。
[#008-J-009] RL 正例がないことの位置づけを明確にしたい
    [関係] [#001-B-003], [#005-A-003] の再指摘。
    [方針] LunarLander は Appendix に短く置き、RL では正例をまだ示していないことを Limitations か再現性情報の近くで整理する。
    [対応] 完了。Limitations に、RL では正例をまだ示せていないことを明記した。
[#008-J-010] 統計の補強余地として t-test / effect size 未実施を明示したい
    [関係] [#006-C-002] の補強。追加実験要求ではなく、限界の明示としては整合的。
    [方針] 本稿で実施した検定の範囲を明記し、未実施の effect size や追加検定は今後の補強余地だと Limitations に触れる。
    [対応] 完了。Limitations に、effect size を含む追加統計整理が今後の補強余地であることを追記した。
[#008-J-011] 社会的影響と結論の締めがやや抽象的
    [関係] 新規指摘。
    [方針] 社会的影響に監査用途の具体例を少し足し、結論の最後を intervention-based diagnosis の価値で締める。
    [対応] 完了。社会的影響に医療画像・自動運転視覚モデルの監査例を足し、結論を介入ベース診断の価値で締めた。
[#008-J-012] 参考文献・付録の整形余地
    [関係] [#001-X-005] の再指摘に近い。
    [方針] arXiv 表記を「arXiv:XXXX.XXXXX, YYYY」に統一、OpenCV / GrabCut 引用の検討、再現性情報と計算資源・LunarLander 付録の順序整理を確認する。
    [対応] 完了。参考文献の arXiv 表記を `arXiv:XXXX.XXXXX, YYYY` 形式へ寄せ、付録見出しと本文参照の表記も確認した。
[#007-A-001] 主要メッセージに対して周辺材料が広がりすぎている
    [方針]
        [#005-A-003], [#006-A-003] の再指摘。
        candidate discovery sweep, CLIP/SSL, worst-group accuracy, LunarLander を「第二の主題」に見せず、confirmation after discovery の補助証拠として従属させる。
    [修正案] 発見系・WGA・LunarLander の扱いを本文でさらに圧縮するか、Appendix へ送る範囲を増やす。
    [対応] 却下。だっていろいろ言いたいんですもん。
[#007-A-002] repair prioritization の主張はまだ証拠不足
    [方針]
        [#004-B-001], [#004-B-002], [#006-A-003] の再指摘。
        downstream remediation を実験していない以上、「修正優先順位づけに有用」とまで言い切る箇所は少し慎重にする。
    [修正案] repair prioritization は practical implication として弱め、主張の芯は confirmation information に戻す。
    [対応] 却下。Waterbirds では候補が実質 background / foreground の二択なので、exp026 の top-1 候補と exp022 の Delta 判定を照合している時点で、後段へ渡したときの振る舞いはかなり直接的に読めるはず。これにほんとに真摯に対応して実験を増やす意味がない。
[#007-B-001] ColoredMNIST の SHAP アーティファクト主張が単一集約則に依存して見える
    [方針]
        [#004-H-004], [#006-A-002] の再指摘。
        本稿の SHAP 批判は「本稿で採用した集約則の下では」に限定されることをさらに明確にし、可能なら別集約や別 baseline は将来課題として明記する。
    [修正案] Abstract / Discussion / Conclusion で限定句を増やし、単一 aggregation rule に依存する分析であることを補足する。
    [対応] 完了。Abstract / Conclusion の SHAP 記述に「本稿で採用した集約規則の下で」を補い、限定句を追加した。
[#007-B-002] Waterbirds の 18/30 をどう読むべきかの説明がまだ足りない
    [方針]
        [#006-A-002] の再指摘。
        残る 12/30 が intervention failure なのか、model variability なのか、success 定義の限界なのかを Discussion で短く整理する。
    [修正案] Waterbirds discussion に、18/30 の残差解釈を 2-3 文で追記する。
    [対応] 完了。Results / Discussion に、連続差分 `Δ_bg - Δ_fg` の平均と 95% CI、および 18/30 を生む要因（シード差・介入差・厳密な recall@1 定義）の説明を追記した。
[#007-B-003] compact workflow figure があると全体が締まる
    [方針]
        新規指摘。
        candidate discovery -> candidate confirmation -> human/repair decision の概念図を 1 枚置くと、図が多くても中心線が見えやすくなる。
    [修正案] workflow の概念図を本文前半に追加する。
    [対応] 完了。図は追加せず、Introduction に candidate discovery → confirmation → 人手判断の三段手順を prose で追記した。
[#007-C-001] exp022 の CI 報告パイプラインに不整合がある
    [方針]
        [#006-C-003] の再指摘かつ具体化。
        summary.txt の malformed CI を監査し、少なくとも補助ファイル側の数値整合性を修正する。
    [修正案] exp022 の CI 生成スクリプトまたは summary 出力を見直し、下限・上限の順序を正しく出す。
    [対応] 完了。`experiments/run_waterbirds_grabcut_sensitivity.py` の summary 出力を修正し、`experiments/results/exp022_waterbirds_grabcut_sensitivity/summary.txt` の Wilson CI 表示を既存 `results.csv` と整合する値へ補正した。
[#007-C-002] Waterbirds の連続値差分に対する paired uncertainty / test が欲しい
    [方針]
        [#004-I-003], [#006-G-001] の再指摘。
        `bg>fg rate` だけでなく、per-seed の `Δ_bg - Δ_fg` 自体に paired uncertainty か検定を付けて、連続量としての差も示す。
    [修正案] Waterbirds の `Δ_bg - Δ_fg` に対して paired CI か paired test を本文で明示する。
    [対応] 完了。Waterbirds 節に per-seed の `Δ_bg - Δ_fg` 平均 0.0018 と 95% CI [-0.0089, 0.0124] を追記し、二値判定率とは別の連続量として補足した。
[#007-C-003] exploratory analyses の small-n をもっと明示したい
    [方針]
        [#006-C-002], [#006-G-001] の再指摘。
        exp024 の 5 seeds、exp026 の 10 seeds は exploratory であることを本文でさらに目立つようにする。
    [修正案] Results または Discussion に、発見系 sweep は exploratory であることを明示し、主張トーンもそれに合わせる。
    [対応] 対応中。Q5 冒頭で GridWorld 候補発見 sweep は 5 シード、CLIP / 自己教師あり表現比較は 10 シードの探索分析であることを明記し、あわせて 30 シード再実行（`exp027`, `exp028`）を起動済み。
[#007-D-001] under-length 指摘の再発
    [方針]
        [#006-D-002] に同じ。
    [対応] 却下。([#006-D-002] に同じ)
[#007-E-001] 介入の「誠実性（Faithfulness）」評価の議論不足
    [方針] マスクベースの置換自体がアーティファクトを生むリスクについて、専門家による目視確認や補助指標の必要性を Limitations に追記する。
    [対応] 完了。Limitations に、目視確認と前景保持率・背景置換率のような補助統計を併用して介入の誠実性を点検する必要性を追記した。
[#007-F-001] クラス整合的背景置換のトレードオフ明示
    [方針] Class-consistent 置換が「クラス非依存なバイアス」を見逃すリスクについて Discussion で短く触れる。
    [対応] 完了。Method / Limitations に、class-consistent 背景置換は強い OOD 介入を避ける一方で、クラスに結び付いた背景手掛かりを部分的に残しうること、クラス非依存の背景バイアスには鈍感になりうることを追記した。
[#007-G-001] GridWorld 数値の不一致（106/120 vs 101/120）
    [方針] GridWorld top-2 の正確な数値が 101/120 (84%) であることを再確認し、本文の typo を修正する。全表の数値を stats.txt と再照合する。
    [対応] 完了。GridWorld top-2 の正しい値 `106/120` を維持しつつ、誤っていた 95% CI を `[0.81, 0.93]` に修正した。
[#006-A-001] title / abstract / conclusion の claim-evidence alignment がまだ弱い
    [方針]
        [#005-A-002], [#005-G-003], [#005-I-001] の再指摘。
        「spurious feature detection」一般を解いたようには書かず、「候補に対する confirmation / functional necessity の確認」へ主張を少しだけ寄せる。
        とくに title は維持しつつ、abstract と conclusion の表現を現在の証拠強度に合わせて 0.2 歩だけ保守的にそろえる。
    [修正案] 検出より確認を前面に出す表現へ title / abstract / conclusion を再調整し、discovery 接続は「初期的証拠」または「接続可能性」に留める。
    [対応] 完了。title は維持しつつ、Abstract / Introduction / Conclusion の主張を「発見済み候補に対する確認」「接続可能性」へ少しだけ寄せた。
[#006-A-002] Waterbirds の書き方がなお成功談に寄りすぎる
    [方針]
        [#005-A-002] の再指摘。
        SHAP 30/30 に対して PerformanceCheck 18/30 という差は、SHAP の誤検出可能性を無視せず、その数値が「背景候補の指摘」と「機能的必要性の確認」で別物だと読めるよう書き分ける。
    [修正案] Abstract / Conclusion / Waterbirds discussion を、「tradeoff」「補完関係」「候補指摘と機能的必要性の差」の三点で明示する。
    [対応] 完了。Waterbirds の要約を、SHAP は背景候補の指摘に敏感であり、PerformanceCheck はその中で大きな性能差分を伴う背景依存を選別する、という役割差が見える書き方へ調整した。
[#006-A-003] discovery と confirmation の接続は separate proxy experiment 止まり
    [方針]
        [#005-I-001] の再指摘。
        いまの証拠は接続可能性を支持する separate-stage evaluation であり、一貫自動 pipeline 実証ではないことを本文でさらに明確化する。
        workflow / semi-automatic flow の言い方は証拠強度に合わせて弱める。
    [修正案] Discussion / Limitations に、接続評価は top-1 候補と confirmation reference の照合に基づく separate-stage evaluation であることを明記し、system-building 的な言い方を整理する。
    [対応] 完了。Discussion / Limitations で、接続評価は top-1 候補と参照判定との照合に基づく separate-stage evaluation であることを明記した。
[#006-B-001] データセットごとに「成功」の定義が揺れて見える
    [方針]
        新規指摘。
        GridWorld / ColoredMNIST は small candidate-set ranking、Waterbirds は background-vs-foreground 比較であり、読者が同じ metric family だと誤解しないよう整理する。
        candidate proposal / candidate confirmation / final decision criterion を明示的に切り分ける。
    [修正案] Experiments か Results の冒頭に、各ベンチマークでの候補集合・正解定義・評価指標をまとめた短い説明または表を追加する。
    [対応] 完了。Experiments に、各ベンチマークで何を正解と見なすかを説明する段落と summary table を追加した。
[#006-B-002] benchmark summary table があると読みやすい
    [方針]
        新規指摘。
        各データセットで ground truth, candidate set, metric, correct detection の意味を一覧化し、cross-domain comparison の読み方を固定する。
    [修正案] ベンチマークごとの ground truth / candidate set / metric / correct detection をまとめた concise table を追加する。
    [対応] 完了。ベンチマークごとの候補集合・正解の意味・主指標を整理した concise table を追加した。
[#006-C-001] abstract / conclusion の headline 数値に uncertainty がない
    [方針]
        [#001-C-001], [#005-F-002] の再指摘。
        headline result は point estimate だけでなく CI も添え、Results table との統計表現をそろえる。
    [修正案] Abstract / Conclusion の主数値を `k/n (%, 95% CI [...])` または簡潔な uncertainty 付き表現へ更新する。
    [対応] 完了。Abstract / Conclusion の主要結果に 95% CI を追記した。
[#006-C-002] 統計報告の標準化と multiplicity の扱いが弱い
    [方針]
        新規指摘。
        main estimates, uncertainty intervals, n, hypothesis test を一か所で見渡せる形にし、どの検定が confirmatory / exploratory かを短くラベル付けする。
        多重比較補正をしないなら exploratory であることを明示する。
    [修正案] 主結果の統計サマリ表を追加し、McNemar / sign test / sensitivity などを confirmatory / exploratory に区別して注記する。
    [対応] 完了。Experiments に、McNemar を確認的、sign test と discovery 接続評価を探索的とする注記を追記し、多重比較補正を行っていないことも明記した。
[#006-C-003] GrabCut sensitivity 周辺の CI / 要約表現が分かりにくい
    [方針]
        [#004-D-002], [#005-F-002] の再指摘。
        感度分析の interval / summary 記述を Results table と同じ書式にそろえ、曖昧な非対称表現を避ける。
    [修正案] sensitivity summary の数値表現を固定書式へ統一し、必要なら簡潔な補助表を追加する。
    [対応] 完了。Waterbirds のマスク感度説明を `k/n (%, 95% CI [...])` に合わせて書き直し、半径ごとの差を読みやすくした。
[#006-D-001] intervention validity / off-target damage の定量検証がまだ弱い
    [方針]
        [#004-A-001], [#004-A-002], [#004-A-003] の再指摘。
        subsection を増やすほどではないが、既存の admissibility 段落と Limitations に、介入 fidelity と off-target damage の観点をもう一歩だけ足す。
    [修正案] Method と Limitations の既存段落に、介入 fidelity と off-target damage の観点を短く追記する。
    [対応] 完了。既存の admissibility 段落と Limitations に、背景置換が背景手掛かりをどれだけ壊し、鳥本体側をどれだけ保てているかを今後定量化すべきだという補足を追加した。
[#006-D-002] 論文長がフルカンファレンス論文としてはなお不足
    [方針]
        [#005-B-001] の再指摘。
        現状は extended workshop paper に近く見えるため、本文の厚みを足すか、short / workshop framing をより明示的に選ぶかを判断する。
    [修正案] full submission を狙うなら intervention validity, benchmark protocol, statistical caveat, practical workflow を中心に本文を大幅増補する。
    [対応] 却下。日本語でどうやって語数を確かめたのか。なんなら長過ぎるくらい。
[#006-D-003] 再現性は改善したが code release / exact commands までは届いていない
    [方針]
        [#001-X-005], [#005-C-002] の再指摘。
        「to be released」に留めず、少なくとも headline experiments の exact commands / config hashes を本文か appendix に出せる形へ寄せる。
    [修正案] 主要実験の実行コマンド、config パス、commit hash、必要 compute を Appendix に追記する。
    [対応] 完了。Appendix に主要実験の実行コマンド、config パス、参照 commit hash を追記した。
[#006-E-001] Discovery 接続結果の数値的裏付けの欠如
    [方針] exp024/exp025/exp026 の具体的な成功率や整合率を Results / Discussion に統合し、接続性の強さが条件依存であることを数値で示す。
    [対応] 完了。Waterbirds の候補発見接続結果に、半径依存の整合率と CLIP / 自己教師あり表現の top-1 / alignment 数値を追記した。
[#006-F-001] CLIP vs SSL のセマンティクス解釈の深化
    [方針] CLIP が背景依存（scene semantics）に強く、SSL が局所特徴に強い理由を、表現学習の性質から一段深く Discussion で論じる。
    [対応] 完了。言語監督つきの高水準意味表現と、自己教師あり表現の対象中心性の差として Discussion を補強した。
[#006-G-001] 接続性主張とエビデンスの統計的一貫性
    [方針] 候補発見と PerformanceCheck の整合率（Alignment %）に対しても、主結果と同様に CI または標準偏差を付記する。
    [対応] 完了。exp025 / exp026 の整合率を本文で `k/n (%, 95% CI [...])` 形式にそろえて追記した。
[#005-A-001] GridWorld の headline metric が要約部と結果表で不整合
    [方針]
        [#004-H-001] の再指摘。
        GridWorld top-2 の正しい値を主結果表から再確定し、Abstract / Introduction / Conclusion の重複記述をすべて同じ値にそろえる。
        今後は summary 数値を単一の authoritative table から転記する。
    [修正案] GridWorld top-2 の `101/120` と `106/120` のどちらが正かを結果 CSV で確認し、要約部を一括修正する。
    [対応] 完了。GridWorld top-2 の合計値を結果表に合わせて `106/120 (88%)` に統一し、Abstract / Conclusion の重複記述を修正した。
[#005-A-002] Waterbirds の高レベル要約がやや言い過ぎ
    [方針]
        [#004-B-003], [#004-I-002] の再指摘。
        「SHAP と PerformanceCheck が双方一致して背景依存を検出」とは書かず、proxy と confirmation の補完関係として要約する。
        disagreement を main claim と矛盾しない短い表現へそろえる。
    [修正案] Introduction と Conclusion の Waterbirds 要約を「部分的一致 / 補完的シグナル」へ言い換える。
    [対応] 完了。Introduction / Results / Conclusion の Waterbirds 要約を、「両手法が常に一致する」という書き方から、候補指摘としては整合しつつ機能的依存の強さについては PerformanceCheck がより保守的に選別する、という補完関係へ言い換えた。
[#005-A-003] LunarLander の負例が主文で目立ちすぎる
    [方針]
        [#001-B-003] の再指摘。
        適用境界の説明としては有用だが、主貢献からの topic drift に見えないよう主文での露出を減らす。
        main text では最小限に触れ、詳細は Appendix に送る。
    [修正案] Abstract / Conclusion から LunarLander への言及を外し、本文は Appendix 参照の一文に圧縮する。
    [対応] 完了。Abstract / Conclusion から LunarLander を外し、本文側の露出も Appendix 参照中心へ圧縮した。
[#005-B-001] 原稿長と framing の釣り合い
    [方針]
        新規指摘。
        現状の本文量はフルカンファレンス論文としては短いので、本文を厚くするか、主張の射程をさらに絞るかを判断する。
        ただしこれは執筆方針の問題であり、即時修正より優先度は一段低い。
    [修正案] 実験プロトコル・失敗分析・実務フローの説明を増やすか、短報寄りの framing に寄せるかを決める。
    [対応] 完了。draft.mdとは別にdraft_short_en.mdを作成。
[#005-B-002] Experiments / Results に benchmark-specific citation が不足
    [方針]
        新規指摘。
        Intro / Related Work だけでなく、Experiments / Results にも dataset split, evaluation convention, intervention choice に対応する引用を分散させる。
        Waterbirds と ColoredMNIST の設定説明に出典を戻す。
    [修正案] Experiments / Results に [Arjovsky2019], [Sagawa2020], [Wah2011] などの引用を差し込む。
    [対応] 完了。ColoredMNIST / Waterbirds の Results 周辺に benchmark-specific citation を差し込み、設定説明との対応を補った。
[#005-B-003] n=5 の例示表が 30-seed 主張に比べて目立つ
    [方針]
        [#001-C-002], [#003-C-003] の再指摘。
        例示表は残してよいが、inferential weight を持たせすぎないよう「illustrative example」と明示する。
        可能なら片方を圧縮するか、domain-facing analysis に差し替える。
    [修正案] n=5 表の見出しや前後文を例示目的に言い換え、主張の重心を 30-seed 集計へ戻す。
    [対応] 完了。`n=5` の表を「例示シード」と明示し、30-seed 集計が主であることを崩さない見せ方へ修正した。
[#005-C-001] GridWorld / ColoredMNIST で Δ vs SHAP の paired test が不足
    [方針]
        [#001-C-001], [#004-I-003] の再指摘。
        Waterbirds だけでなく、GridWorld / ColoredMNIST の headline comparison にも paired significance を付ける。
        同一 seed / oracle 比較なので McNemar などの paired test を本文か付録に明示する。
    [修正案] GridWorld と ColoredMNIST の Δ vs SHAP に paired significance test を追加し、主比較箇所から参照する。
    [対応] 完了。GridWorld と ColoredMNIST の headline comparison に paired な McNemar 検定を追加し、Results / Conclusion から参照する形へ補強した。
[#005-C-002] 再現性のための exact seed list と sampling detail が不足
    [方針]
        新規指摘。
        seed は固定と書くだけでなく、実際の seed list と intervention sampling の詳細を Appendix に置く。
        paired comparison を再現するための最小情報を明示する。
    [修正案] Appendix に seed list、donor sampling、n_eval, perturbation parameter を追記する。
    [対応] 完了。Appendix の再現性情報に seed 一覧 `0..29` と Waterbirds の donor pool / `n_eval` / noise parameter を追記した。
[#005-D-001] Waterbirds における主張とエビデンスの矛盾
    [方針] [#005-A-002] に同じ。`「30シードすべてで正の差が出た」` という記述と `検出率 18/30` は別の量だと分かるように書き分け、正確な p 値と検出率を記述する。
    [対応] 完了。`18/30` の検出率と `bg_mean_delta - fg_mean_delta` の sign test が別の量であることが分かるように本文を分離し、sign test は specialized baseline comparison の repeated-intervention 平均量に対するものだと明確化した。
[#005-E-001] 箇条書き（Bullet points）の排除と Prose（文章）化
    [方針] [#004-C-003], [#004-I-004] の再指摘。Intro, Method, Results, Limitations に残っている箇条書きをすべて流れるような文章（flowing prose）にリライトする。「技術報告書」から「学術論文」への格上げ。
    [対応] 完了。序論の貢献箇条書きを prose 化し、Limitations も段落化した。Method / Results / Discussion でも箇条書き依存を増やさないように整理した。
[#005-F-001] 不一致ケース（Discordant Pairs）テーブルの事実誤認修正
    [方針] [#003-C-003] の再点検。Seed 15, 16, 17 が「NG」判定であるという誤った記述を修正。実際の results.csv から、本当に判定が割れているシード（Seed 1, 3, 5等）を特定し、表を差し替える。
    [対応] 完了。不一致シード表を実データに合わせて seed `1, 3, 5` に差し替え、例示表に混入していた存在しない seed 番号も実 seed へ修正した。
[#005-F-002] 数値の丸めと一貫性の点検
    [方針] [#004-C-001], [#004-C-004] の再指摘。表、図、本文の間で、数値の丸め（0.100 vs 0.103125等）に一貫性がない箇所をすべて点検・統一する。
    [対応] 完了。要約・表・例示表の数値を見直し、Waterbirds の表では小数第3位にそろえるなど、本文と表の丸め規則を整えた。
[#005-G-001] 結論の主メッセージを一点集中させたい
    [方針]
        [#004-G-001] の再指摘。
        Conclusion の情報量が多く、最終メッセージが散りやすい。
        「発見済み候補に対して、破壊的介入による性能感度Δで本当に効いているかを確認する手続きを定式化した」が一番の主張だと冒頭で言い切り、各実験はその証拠として従属させる。
    [修正案] Conclusion 冒頭を confirmation step の一文に寄せ、その後に GridWorld / ColoredMNIST / Waterbirds / 負例を evidence として並べる。
    [対応] 完了。Conclusion 冒頭を confirmation step の一文へ寄せ、各実験結果をその証拠として従属させる構成へ再整理した。
[#005-G-002] 各実験が検証する問いを明示したい
    [方針]
        [#004-G-002] の再指摘。
        Results が長く見えるため、各実験がどの問いや仮説に対応するかを節頭で一文ずつ明示する。
        既存の「実験ごとの役割」よりも、Q1/Q2/Q3/Q4 のような問いの形にすると読者に入りやすい。
    [修正案] 各 Results 小節の冒頭に「この実験が何を検証するか」を question/hypothesis 形式で追記する。
    [対応] 完了。Results の主要段落冒頭に Q1-Q4 形式の問いを置き、各実験が何を検証しているかを明示した。
[#005-G-003] 候補発見 vs 確認 の役割分担を前半でもっと強調したい
    [方針]
        [#004-I-001] の再指摘。
        本研究の新規性は discovery の代替ではなく、後段 confirmation の定式化にある。
        序論や貢献で、pipeline の穴を埋める stage であることをもっと前面に出す。
    [修正案] Introduction または貢献段落に、discovery の代替ではなく confirmation stage だと強く言い切る文を追加する。
    [対応] 完了。序論と関連研究で、PerformanceCheck は discovery の代替ではなく、その後段 confirmation を担う手続きだとより明確に整理した。
[#005-G-004] Future Work を一文で締めたい
    [方針]
        [#004-G-003] の再指摘。
        Limitations は良いが、「次の一歩」が散って見える。
        介入設計の自動化と discovery 法との end-to-end 接続を一文で束ねる。
    [修正案] Limitations 末尾か Conclusion 直前に、介入標準化と候補発見法との統合を次課題としてまとめる一文を置く。
    [対応] 完了。Limitations 末尾に、介入設計の標準化と自動化、および候補発見法と組み合わせた end-to-end 評価を次課題として束ねる一文を追記した。
[#005-H-001] アルゴリズムの最終出力を「修正優先順位つき特徴リスト」と明示したい
    [方針]
        [#004-B-004], [#003-E-001] の再指摘。
        いまは特徴ランキング、top-k recall、検出率、修正優先順位づけが並列に見えるが、実用アルゴリズムとしての出力は順位リストだと明示した方がよい。
        検出率は評価指標、順位リストが最終出力、という切り分けにする。
    [修正案] Introduction / Method / Discussion のどこかで、「本手法の出力は修正すべき特徴の順位リストである」と明記する。
    [対応] 完了。Method で主たる運用形を「修正優先順位づけに用いる全候補ランキング提示」と明記した。
[#005-H-002] Δ を因果効果そのものではなく順位づけ用スコアとして一度だけ明示したい
    [方針]
        [#004-H-003] の再指摘。
        今の「機能的必要性の近似指標」は良いが、「因果効果そのものではない」「依存の真理値判定器ではない」と一度だけ明確化すると安全。
        修正優先順位づけ器としての位置づけを強める。
    [修正案] Method か Discussion に、Δ は性能に効く順に候補を並べるスコアであり、因果効果そのものではないと一文追加する。
    [対応] 完了。Method で、Δ は因果効果そのものではなく、依存候補を性能に効く順へ並べるための機能的必要性の近似指標だと明記した。
[#005-H-003] 同じ主張の繰り返しとキャプション過多を削りたい
    [方針]
        [#004-F-002], [#004-I-004] の再指摘。
        「候補発見ではなく確認ステップ」が序論末・結果後・考察冒頭でやや重複している。
        Figure caption も説明を入れ込みすぎず、本文で解釈する比重を上げる。
    [修正案] confirmation step の強調は 1 か所で強く、他は軽く触れる程度に圧縮し、Figure caption を一文か二文へ整理する。
    [対応] 完了。Discussion の重複説明を圧縮し、Figure caption は [#003-F-001] と矛盾しない範囲で一文中心に短く整理した。
[#005-I-001] 新規性を「end-to-end pipeline の橋渡し」としてもう一段具体化したい
    [方針]
        [#004-I-001], [#003-E-001] の再指摘。
        「後段確認」のユニークさは出ているが、それが discovery 法とつながって pipeline を完成させる利点がまだ具体例として弱い。
        読者が「これで何が変わるか」をイメージできるよう、利用シナリオを補う。
    [修正案] 序論か Discussion に、discovery 手法で候補を得てから PerformanceCheck で優先順位づけし remediation へ進む end-to-end の利点を具体例つきで補う。
    [対応] 完了。Discussion に、既存の候補発見法や著者らの先行する shift 診断枠組みを前段に置くことで、候補生成→確認→優先順位づけの半自動パイプラインとして接続できる可能性を追記した。同時に、完全自動の end-to-end system を実証したわけではない点も明示した。
[#005-I-002] SHAP への書き方をもう少し中立にしたい
    [方針]
        [#004-I-002] の再指摘。
        SHAP を「大幅に下回る」「機械的に一致」と批判的に書きすぎると、証拠があってもバイアスを感じさせる。
        文脈依存の補完関係として位置づけ、SHAP の強みも一度認める。
    [修正案] SHAP 比較文を「補完的」「本稿の設定では」「この集約則の下では」に寄せ、説明可能性としての役割も一文だけ残す。
    [対応] 完了。SHAP 比較文を「補完的」「本稿の集約規則の下では」という表現へ寄せ、劣位の断定に見えすぎないようトーンを調整した。
[#005-I-003] Related Work / Discussion / キャプションの冗長さをさらに詰めたい
    [方針]
        [#004-C-003], [#004-I-004] の再指摘。
        Related Work の重複、Discussion の workflow 反復、図キャプションの詳細さがまだ残っている。
        論旨は維持したまま 5-10% ほど圧縮して、流れを滑らかにする。
    [修正案] Related Work の重複箇所を削り、Discussion の workflow を 1 パラグラフに凝縮し、図キャプションの説明を本文へ戻す。
    [対応] 完了。Related Work の発見手法パラグラフを圧縮し、Discussion とキャプションの重複説明も少し削って全体を軽くした。
[#005-I-004] スケーラビリティと将来の自動化方針をもう少し書きたい
    [方針]
        [#004-G-003] の補強。
        Limitations で人手介入の問題は書いているが、高次元時の計算量や saliency 等による半自動化の方向性が薄い。
        実用上の制約と解決の見取り図を短く示す。
    [修正案] Limitations に `O(|F|*|D|)` 的な full scan の負荷と、候補絞り込み・saliency 併用による将来方向を追記する。
    [対応] 完了。Limitations に full scan の計算負荷、高次元設定での候補絞り込み後介入、半自動的な介入設計と end-to-end 評価の将来方向を追記した。
[#004-A-001] 介入の妥当条件がまだ完全には境界づけられていない
    [方針]
        [#003-A-001] の再指摘。
        介入を「対象特徴の情報を壊す操作」と「単に入力を OOD に壊す操作」に分けて説明する。
        Waterbirds の背景置換や mask 摂動が、どの程度まで admissible な近似なのかを Method または Limitations で短く明示する。
    [修正案] Method に「対象特徴の情報を壊しつつ非対象特徴をできるだけ保つ」近似として admissibility を1段落で入れる。
    [対応] 完了。Method に admissibility の補足段落を追加し、対象特徴の情報を壊しつつ非対象特徴をできるだけ保つという二条件を、Waterbirds の背景置換やマスク摂動の近似として明記した。
[#004-A-002] 破壊型コントロールと構造保持型介入の違いを補う必要がある
    [方針]
        [#003-A-001] の再指摘。
        破壊型コントロールと構造保持型介入の違いを 1 段落で補い、単に壊しただけの OOD 劣化と切り分ける。
        追加の負例が必要なら、Method か Limitations に短く入れる。
    [修正案] Limitations か Method に、OOD 破壊コントロールと構造保持介入の違いを短く対比して書く。
    [対応] 完了。Method に、構造保持型介入と破壊型コントロールの違いを追記し、OOD 劣化との切り分けを本文上で明示した。
[#004-A-003] 適用境界をもう少し明示した方がよい
    [方針]
        [#003-A-001] の再指摘。
        PerformanceCheck がどの条件で妥当で、どの条件では前提が崩れるかを簡潔に書く。
        特に Waterbirds のような構造化画像と、完全破壊になりやすい介入を区別する。
    [修正案] Limitations に「どの条件で前提が崩れるか」を1段落だけ追記する。
    [対応] 完了。Limitations に、候補特徴を局所化・分離して介入しやすい場合に解釈しやすく、そうでない場合には OOD 由来の低下との切り分けが難しいことを追記した。
[#004-B-001] 修正優先順位づけのワークフローがまだやや抽象的
    [方針]
        [#003-E-001] の再指摘。
        候補発見 -> PerformanceCheck 確認 -> 修正優先順位づけ、という 3 段の流れを Discussion で具体化する。
        どの候補を augmentation / 再学習 / 追加データ収集に回すか、実務上の使い方を一言でよいので明示する。
    [修正案] Discussion に「候補発見→確認→優先順位づけ」の3段ワークフローを段落で入れる。
    [対応] 完了。Discussion で、候補発見→確認→修正優先順位づけの流れを prose で具体化し、実務上の使い方を補った。
[#004-B-002] 診断と修正の接続が提案止まりに見える
    [方針]
        [#003-E-001] の再指摘。
        PerformanceCheck を「診断結果を修正優先度に変換する部品」として、手順として読めるように書く。
        単なる理念ではなく、candidate -> check -> prioritize の順を明確にする。
    [修正案] Discussion の末尾に、候補から修正優先度へつなぐ具体的な1段落を置く。
    [対応] 完了。PerformanceCheck を診断結果を修正優先度へ変換する部品として位置づけ、候補から修正方針へつなぐ段落を加えた。
[#004-B-003] exp021 の disagreement の扱いがまだ強く言い切れていない
    [方針]
        [#003-E-002] の再指摘。
        exp021 の不一致を、baseline が間違いだと断定するのではなく、測っている量の違いとして整理する。
        そのうえで、どの候補を augmentation の優先対象にするかという実務的含意を 1 段落で示す。
    [修正案] Waterbirds 節で、exp021 の不一致を「proxy と necessity の差」としてもう少し明示する。
    [対応] 完了。Waterbirds 節で、不一致は baseline の誤りではなく、候補の存在を拾う指標と確認指標の差として整理した。
[#004-B-004] top-k 候補の実務的な使い方がもう一歩欲しい
    [方針]
        [#003-E-001] / [#003-E-002] の再指摘。
        top-k 候補を見て専門家が何をするのかを、修正候補の絞り込みとして書く。
        1 つの具体例でよいので、候補リストが augmentation / retraining 方針にどうつながるかを示す。
    [修正案] top-k 候補を見た専門家が augmentation / retraining の優先順位をどう決めるかを1例で示す。
    [対応] 完了。Discussion に、上位候補から背景置換 augmentation や追加収集を優先する具体例を追記した。
[#004-C-001] 数値表現と図の配置の統一がまだ不十分
    [方針]
        [#003-C-001] / [#003-F-002] の再指摘。
        counts / percentages / Wilson CI の表記を主結果表で揃える。
        本文中の exact number の重複を減らし、詳細値は表と図に寄せる。
    [修正案] 主結果表は `k/n (%, 95% CI)` に統一し、本文の exact number は最小限にする。
    [対応] 完了。主結果表の CI 表記を `k/n (%, 95% CI [...])` に統一し、本文中の exact number を削って表と図に寄せた。
[#004-C-002] 画像の重複挿入や末尾への再掲を整理した方がよい
    [方針]
        [#003-F-001] の再指摘。
        同じ図の再掲があれば整理し、各 Figure は 1 回だけ配置する。
        図は説明段落の直後に置き、末尾への再掲を減らす。
    [修正案] 同じ図の再掲を削り、各 Figure を説明段落の直後に1回だけ置く。
    [対応] 完了。draft.md から重複していた Waterbirds 画像群を削除し、Figure 7 のみを残した。
[#004-C-003] Method / Results / Discussion に箇条書きや列挙がまだ少し多い
    [方針]
        [#003-F-002] の再指摘。
        箇条書きは必要最小限にし、本文では流れるような prose を優先する。
        手順の列挙が必要な箇所は Appendix に逃がすか、短い段落に再構成する。
    [修正案] Discussion の手順列挙を prose 化し、必要なら Appendix に退避する。
    [対応] 完了。Discussion の workflow を短い prose に整えた。
[#004-C-004] 統計表現の固定パターンがまだ完全ではない
    [方針]
        [#003-C-001] の再指摘。
        `k/n (%, 95% CI)` のような固定パターンを主結果表で徹底する。
        exact number を本文に散らしすぎず、表と図に委ねる。
    [修正案] 統計の書式を `k/n (%, 95% CI)` に固定して、結果節全体で揃える。
    [対応] 完了。GridWorld / ColoredMNIST の主比較表を固定パターンの統計表現に統一した。
[#004-D-001] Admissibility と実装の紐付け
    [方針] `class-consistent` 置換（exp021）が Admissibility 条件(b)（周辺分布保持）をいかに実用的に満たしているかを Method に追記する。
    [修正案] exp021 の class-consistent 置換を、admissibility 条件(b) の実装例として Method に明記する。
    [対応] 完了。Method で Waterbirds の `background_replace` を「前景マスクを保ちながら同一クラス donor から背景のみを置換する class-consistent 操作」として明記し、条件(b) の実用的近似であることを追記した。
[#004-D-002] 頑健性の統計的裏付け
    [方針] exp022 が完了次第、1シード（exp020）ではなく30シード全体でのマスク安定性（Flip率）を本文に反映する。
    [修正案] exp022 の 30 seed 結果を使って、mask radius sensitivity の Flip率を本文と表に反映する。
    [対応] 完了。exp022 の 30 シード半径スイープを主文に短く反映し、平均 Δ_bg / Δ_fg が半径に対して連続的に変化すること、マスク品質が結果の大きさには影響するが不連続な崩壊としては現れていないことを追記した。
    [証拠ファイル] `experiments/results/exp022_waterbirds_grabcut_sensitivity/results.csv`, `experiments/results/exp022_waterbirds_grabcut_sensitivity/summary.txt`, `experiments/results/exp022_waterbirds_grabcut_sensitivity/fig_grabcut_sensitivity.png`
[#004-E-001] 「帰属法の幻覚（Hallucination）」の明文化
    [方針] 「既存手法が依存ありと判定しても性能が落ちないケース」を「帰属法の幻覚」と定義し、PerformanceCheck がそれを正す Ground Truth であるというストーリーを Discussion で強化する。
    [修正案] Discussion で、既存法の false positive を PerformanceCheck がどう補正するかを1段落で明文化する。
    [対応] 完了。`hallucination` という強い語は採用せず、Discussion で「proxy ベースの候補発見が広めに出した警告のうち、PerformanceCheck が機能的必要性の観点から false positive 候補を落とす」と明文化した。
[#004-E-002] Remediation（修正）の具体化
    [方針] 依存検出後のアクションとして、具体的な Augmentation 種類（Mixup等）への優先順位付けフローを 1 文加筆する。
    [修正案] 検出後アクションとして、Mixup / background replacement などの augmentation 優先順位を1文で書く。
    [対応] 完了。Discussion に、高Δ候補に対して背景置換や再学習を優先する旨を1文追加した。
[#004-F-001] アンチ・リピティション・ルールの徹底
    [方針] 本文中の正確な数値を、表への参照や定性的表現（大半のケース、等）に置き換え、README 違反を解消する。
    [修正案] 本文中の exact number を減らして、値は表・図に寄せる表現へ置き換える。
    [対応] 完了。重複する exact number を本文から減らし、主要な値は表と図へ寄せた。
[#004-F-002] キャプションの分析的記述
    [方針] 各 Figure のキャプションに「Key Takeaway（この図から何を読み取るべきか）」を 1 文ずつ追加する。
    [修正案] 各 Figure キャプション末尾に、1 文の takeaway を追加する。
    [対応] 完了。Figure 1-7 のキャプションに、この図から何を読むべきかを示す takeaway を追加した。
[#004-G-001] 新規性の核はあるが、メッセージの軸がやや散っている
    [方針]
        [#003-D-001] / [#003-E-001] の再指摘。
        PerformanceCheck を「候補発見の後段で、本当に性能に効いているかを確認する手続き」として一本化する。
        Δ vs SHAP / hidden-space proxy / discovery pipeline / worst-group accuracy をすべて同じ主張に回収し、主張1本に見せる。
        Conclusion では tested benchmarks 上の confirmation step として射程を絞る。
    [修正案] Introduction と Conclusion を、Performance-based confirmation step の一本化されたメッセージに寄せる。
    [対応] 完了。Abstract / Introduction / Discussion / Conclusion を、候補発見の後段に置かれる confirmation step という軸に寄せた。
[#004-G-002] 実験ごとの仮説対応を明示すると読みやすくなる
    [方針]
        Exp016/017/018/021 がそれぞれ何の仮説を検証するのかを Results 冒頭か小見出しで明示する。
        GridWorld = 高相関での検出、ColoredMNIST = 符号化アーティファクト、Waterbirds = 実世界条件での confirmation、exp021 = proxy と necessity の分離。
    [修正案] Results の各節に一言の hypothesis/question を付けて、実験の役割を対応づける。
    [対応] 完了。Results 冒頭に各実験の役割を一言で追記した。
[#004-G-003] 今後の展望を 2-3 行で整理するとシリーズの1本目として締まる
    [方針]
        介入設計の自動化・標準化と、候補列挙手法との結合を Future Work として明示する。
        現状の limitation と future work を分離して、次に何をやるべきかが見えるようにする。
    [修正案] Limitations の最後か Conclusion 直前に Future Work を短くまとめる。
    [対応] 完了。Limitations 末尾に、候補発見から介入確認までを半自動化する Future Work を追記した。
[#004-H-001] 実験設定と主結果の数がところどころ噛み合っていない
    [方針]
        [#002-A-001] の再指摘。
        5シードと30シード、exp016/017/018 の対応を本文全体で統一する。
        Method と Results で同じ数が出るようにし、主結果は 30 seeds 版に寄せる。
    [修正案] 数値実験の設定表を作り、Method/Results/Appendix のシード数表記を一致させる。
    [対応] 完了。Method/Results の残っていた 5-seed 記述を 30-seed 版に統一し、exp017 の旧表も削除して後段の 30-seed 比較表へ寄せた。
[#004-H-002] 主指標の揺れを止める必要がある
    [方針]
        [#003-A-002] の再指摘。
        top-k, recall@k, detection rate, argmax 判定を混在させず、主指標を 1 つに固定する。
        補助分析として使う指標は Results の下位に回す。
    [修正案] 主指標を top-k か recall@k のどちらかに固定し、残りは補助分析に落とす。
    [対応] 完了。Method で主指標を `top-k inclusion に基づく recall@k` と明記し、GridWorld/ColoredMNIST/Waterbirds の pairwise 比較は補助的な sanity check または recall@1 の同値表現として位置づけ直した。
[#004-H-003] Δ の意味づけは少し弱めて書いた方が安全
    [方針]
        [#003-E-002] の再指摘。
        「壊したときに落ちる = 強い依存」と断定せず、機能的必要性の proxy / 依存の下限評価として述べる。
        介入の質・相関構造・代替可能性に依存することを Method か Discussion で明示する。
    [修正案] Method の Δ 定義と Discussion の解釈を、functional necessity proxy という語彙に寄せる。
    [対応] 完了。Abstract / Introduction / Method / Discussion / Conclusion の Δ 解釈を `functional necessity proxy` に寄せ、断定的な依存表現を弱めた。
[#004-H-004] ColoredMNIST の SHAP アーティファクト主張は限定条件を毎回明示したい
    [方針]
        [#003-C-002] の再指摘。
        「本稿で採用した集約規則の下では」という限定を本文中で繰り返す。
        SHAP のアーティファクトを断定しすぎず、図と本文を短くして符号化の影響を一目で伝える。
    [修正案] ColoredMNIST の説明に限定句を入れ、集約規則に依存する現象だと明示する。
    [対応] 完了。Method / Results / Discussion / Conclusion に「本稿で採用した集約規則の下では」という限定句を追加し、SHAP 一般への過剰一般化を避ける形に修正した。
[#004-I-001] 新規性はあるが、post-hoc confirmation pipeline の後段としてもっと強く言える
    [方針]
        [#003-D-001] / [#003-E-001] の再指摘。
        事後説明法や訓練時手法との差分を、候補発見ではなく confirmation step の定式化として明確にする。
        Abstract/Introduction で PerformanceCheck のユニークさを冒頭で強く打ち出す。
    [修正案] Abstract と Introduction を、PerformanceCheck を「後段の確認手続き」として前面に出す形へ寄せる。
    [対応] 完了。Abstract / Introduction / Conclusion で、PerformanceCheck の役割を後段の確認手続きとして前面化した。
[#004-I-002] 過剰主張と冗長さを少し抑えると通りやすい
    [方針]
        [#003-B-003] / [#003-F-002] の再指摘。
        SHAP を強く否定しすぎず、complements としての位置づけを残す。
        IRM / training-time mitigation / related work の重複を圧縮し、本文を 10-15% ほど締める。
    [修正案] SHAP との比較文を穏やかにし、Related Work の重複を整理する。
    [対応] 完了。SHAP との比較文を穏やかにし、Discussion の重複を削減した。
[#004-I-003] 統計的裏付けは良いが、追加の有意性やアブレーションがあるとより強い
    [方針]
        CI に加えて、必要なら別の有意性比較や介入変種のアブレーションを検討する。
        ただし主張の本質は「介入ベースの performance sensitivity」であることを保つ。
    [修正案] Results に補助的な統計比較や介入変種の簡単な ablation を追加するか検討する。
    [対応] 完了。Waterbirds で `Δ_bg - Δ_fg` の seed-wise 差に対する両側符号検定を追加し、30 seed すべてで正の差が出ること (`p = 1.86 × 10^-9`) を本文に反映した。あわせて GrabCut mask 半径スイープを補助アブレーションとして主文で明示し、介入実装の細部に対する頑健性を短く補強した。
[#004-I-004] 文体と図表の統一感を上げる余地がある
    [方針]
        [#003-F-001] / [#003-F-002] の再指摘。
        日本語と英語の混在語彙を絞り、Figure キャプション・節頭の重複を減らす。
        既存の修正版レビューでも指摘されていた「図の分析的キャプション」「箇条書きの prose 化」をさらに進める。
    [修正案] Figure caption に takeaway を入れ、Results/Discussion の prose を増やす。
    [対応] 完了。節見出しの日本語化と Figure 説明の整理を進めた。
[#003-A-001] 介入の妥当条件がまだ部分的にしか形式化されていない
    [方針]
        介入 family ごとの admissibility 条件を短い小節で明示する。
        ここでの論点は「単に壊したから性能が落ちた（OOD 由来の困惑）」のか、「スプリアス依存があるから落ちた」のかを峻別することにある。
        したがって、妥当な介入とは「対象特徴の予測情報を十分に破壊しつつ、非対象特徴の統計をできるだけ保持する」近似として定義し、破壊型コントロールと構造保持型介入を分けて記述する。
        実装上は、class-consistent な背景置換や foreground マスク摂動のように、target feature だけを狙って壊し、他の特徴を OOD にしすぎない境界線を明示する。
    [対応] 完了。Method 節で admissibility 条件と OOD 破壊との区別を記述済み。
[#003-A-002] 検出ルールが top-k と rank-based で揺れている
    [方針]
        判定文言を統一し、rank-based success か top-k inclusion かを明示的に分けて書く。
        Method / Results / Conclusion で同じ評価語彙を使う。
    [対応] 完了。Method / Results で top-k, recall@k を明示済み。
[#003-A-003] specialized baseline の proxy score の意味づけがやや弱い
    [方針]
        Spec/PCA は candidate spuriousness proxy、Delta は intervention-based necessity として役割を明示する。
        専用ベースラインを「候補確認」ではなく「functional dependence の直接指標ではない」ものとして位置づける。
    [対応] 完了。Waterbirds 節で proxy score の役割を本文化済み。
[#003-B-001] specialized-baseline 比較の domain 上の説明がまだ少し薄い
    [方針]
        Waterbirds 節で、Spec/PCA が何を推定しているのかを1段落で明示する。
        Delta との比較軸を「候補 spuriousness vs 必要性」として固定する。
    [対応] 完了。Waterbirds 節で専用ベースラインの推定対象を説明済み。
[#003-B-002] discordant pairs の意味を本文で一言で明示した方がよい
    [方針]
        exp021 の disagreement を「Delta の負け」ではなく「測っている量の違い」として説明する。
        代表的な不一致シードの補助表を短く添える。
    [対応] 完了。Discordant pairs の意味づけと代表シード表を draft に追記済み。
[#003-B-003] conclusion の射程がまだ少し広い
    [方針]
        結論は tested benchmarks と intervention-based diagnosis に限定して書く。
        一般の spurious-feature detection を解決したような言い回しは避ける。
    [対応] 完了。Conclusion の文言を tested benchmarks / intervention-based diagnosis に寄せて修正済み。
[#003-C-001] 統計表現がまだ完全には統一されていない
    [方針]
        主結果表と caption で counts / percentages / Wilson CI の見せ方をそろえる。
        主要表だけでも表記ルールを固定する。
    [対応] 完了。主要表と Waterbirds 記述で Wilson CI を含めた表現へ揃え済み。
[#003-C-002] exp021 の図キャプションと本文の統計言語を揃える必要がある
    [方針]
        Delta は intervention-based necessity、Spec/PCA は proxy scores という表現に統一する。
        図キャプションも同じ語彙に合わせる。
    [対応] 完了。exp021 の図キャプションを本文と同じ語彙へ統一済み。
[#003-C-003] exp021 の disagreement table はもう少し compact にした方がよい
    [方針]
        代表的な seed を 2〜3 例に絞る。
        列定義を明確化し、どの値が何を意味するかを一目で分かるようにする。
    [対応] 完了。代表 3 seed に圧縮した disagreement table を draft に追加済み。
[#003-D-001] 手法名のブランディング
    [方針] 手法名を "PerformanceCheck" に統一。アクロニムを避け、「性能という動かぬ証拠で最終確認する」という実用的な本質を強調する。
    [対応] 完了。draft.md の Abstract / Introduction / Method / Results / Conclusion で PerformanceCheck に寄せた。
[#003-D-002] 介入マスク（GrabCut）の不確実性の定量的言及
    [方針] GrabCut の失敗が Δ に与える影響について、Limitations または Method で補足する。
          30 seed 全体で、mask radius を変えたときに判定がどれくらい変わるかを exp022 で確認する。
    [対応] 完了。exp022 の 30 シード半径スイープを踏まえ、GrabCut mask perturbation に対して平均 Δ_bg / Δ_fg が半径に応じて連続的に変化すること、マスク品質が結果の大きさには影響するが不連続な崩壊としては現れていないことを反映した。
    [証拠ファイル] `experiments/results/exp022_waterbirds_grabcut_sensitivity/results.csv`, `experiments/results/exp022_waterbirds_grabcut_sensitivity/summary.txt`, `experiments/results/exp022_waterbirds_grabcut_sensitivity/fig_grabcut_sensitivity.png`
[#003-E-001] 診断から判断・修正への接続
    [方針] PerformanceCheck を「ドメイン専門家が修正の優先順位を判断するための、定量的エビデンス提供パーツ」と位置づける。Discussion では、出力された Δ 値を参考に、専門家がどの特徴に Augmentation 等を適用すべきかを選択する、人間を介した（Human-in-the-loop）ワークフローの一環として記述する。
    [対応] 完了。Discussion に Human-in-the-loop の修正優先順位づけワークフローを追記した。
[#003-E-002] 統計的な存在と機能的な依存の分離
    [方針] 不一致 12 シードの分析を、「既存手法が『バイアスの存在』を警告した際、PerformanceCheck が『モデルはそれを実用上無視できているか』という補足情報を与える例」として記述する。これにより、専門家がドメイン知識に照らして、検出された特徴がスプリアスか否か、修正が必要か否かを判断するための多角的な視点を提供できることを強調する。
    [対応] 完了。exp021 の discordant pairs を representation-space proxy と intervention-based necessity の差として明示し、既存法の候補を PerformanceCheck が絞り込む関係として追記した。
[#003-F-001] 図のキャプション情報の充実
    [方針] 各 Figure のキャプションを、「何を示し、何が結論か」まで含めた自己完結的な説明に書き換える。
    [対応] 完了。Figure 3-7 の caption を self-contained な説明へ差し替えた。
[#003-F-002] 本文と表の数値重複（アンチ・リピティション）
    [方針] 本文中の数値を「有意な向上」「3割程度の低下」などの定性的表現に置き換え、正確な値は表に委ねる。
    [対応] 完了。Results / Discussion の重複する exact number を減らし、詳細値は表と図に寄せた。
[#002-A-001] 統計的な可視化
    [方針]
        [#000-X-002]の再指摘。
        主要表に Wilson CI を併記し、 error bar 付き図と p 値を本文に直接示す。
        Delta vs SHAP の分布と Waterbirds の seed 別挙動を可視化する。
        図の個数が足りない問題もついでに解決。
    [対応] 完了。GridWorld/CMNIST/Waterbirds の全主要表に Wilson CI を反映。Figure 1-7 を説明段落直後に移動。Waterbirds 節に不一致シードの個別スコア表を追加。
[#002-A-002] 介入演算子の妥当条件と top-5 判定の書き分けが曖昧
    [方針]
        1. 介入の正当性（Admissibility）の定式化:
           以下の二条件を満たす介入 T_i を「妥当」と定義し、Method節に数式的に追記する。
           - 条件(a) 情報破壊: I(X_i; T_i(X)) ≈ 0 （ターゲット特徴の情報を完全に遮断する）
           - 条件(b) 分布保持: P(X_{-i} | T_i(X)) ≈ P(X_{-i}) （他特徴の周辺分布を壊さず、OODによる困惑を防ぐ）
        2. 判定ルールの統一:
           「Top-5ランキング内の順位」を主指標とし、全ての実験で一貫した Recall@k 形式で評価を記述する。
        対応実験: exp021
    [対応] 完了。exp021 で specialized score を生成し、Spurious Score proxy では bg_score > fg_score = 30/30、PCA proxy でも pca_ok = 30/30 を確認。本文の Waterbirds 節に追記済み。
    [証拠ファイル] `experiments/results/exp021_waterbirds_specialized_baseline/specialized_scores.csv`, `experiments/results/exp021_waterbirds_specialized_baseline/summary.txt`
[#002-B-001] Waterbirds の主文比較に専用ベースラインがない
    [方針]
        [#001-B-001](数値実験実行中)の再指摘。改めて下の方針とする。
        1. 比較の軸を「属性推定 vs 操作的検証」として固定:
           - 既存手法 (Spurious Score等): 特徴空間の統計からスプリアス「性」を推定。
           - Delta (提案): 実際に破壊して性能を測り、モデルの「操作的必要性」を実証。
        2. 主張のゴール:
           「専用手法が『背景はスプリアスだ』と言っても、Deltaが『でもモデルは背景を無視している』と示せば、モデル診断としてはDeltaの方が真実に近い」というロジックで配置する。
           検出率の勝敗だけでなく、不一致ケース（Discordant pairs）の定性分析を主眼に置く。
        対応実験: exp021
    [対応] 完了。exp021 で specialized score を生成し、Spurious Score proxy では bg_score > fg_score = 30/30、PCA proxy でも pca_ok = 30/30 を確認。本文の Waterbirds 節に追記済み。
    [証拠ファイル] `experiments/results/exp021_waterbirds_specialized_baseline/specialized_scores.csv`, `experiments/results/exp021_waterbirds_specialized_baseline/summary.txt`
[#002-C-001] 主張が図に裏付けられていない
    [方針] [#002-A-001]で対応する。
    [対応] 完了。([#002-A-001] に同じ)
[#001-A-001] 介入演算子 T_i の理論的正当化が不足
    [方針]
        「do-calculusに基づく」と断言せず、do演算に着想を得た実用的介入近似として記述。
        Janzing と Adebayo を引用し、因果証明ではなく操作的必要性の測定であることを明示。
    [対応] 完了。Method/Discussion に反映済み。
[#001-A-002] 判定基準が二候補特徴間の相対比較に閉じている
    [方針] 二候補の直接比較を補助に下げ、全候補の Δ ランキング提示を主判定にする。本文では top-k 判定を明示し、表示は top-5 を標準化する。
    [対応] 完了。Method の検出判定基準を ranking ベース（top-5）へ更新。
[#001-A-003] 介入質の sensitivity analysis がない
    [方針]
        Waterbirds でマスク摂動 sensitivity を系統実施（1 seed固定）。
        具体的には前景マスクの膨張/縮小（例: -3, -1, 0, +1, +3 px）ごとに `Δ_bg`, `Δ_fg`, 判定（bg>fg）を記録し、判定反転の有無と変動幅を図示する。
        対応実験: exp020
    [対応] 完了。`exp020` で seed=0、mask_radii=[-3, -1, 0, 1, 3] を評価し、decision flips は 0/5。全条件で `delta_bg > delta_fg` を確認。
    [証拠ファイル] `experiments/results/exp020_waterbirds_mask_sensitivity/results.csv`, `experiments/results/exp020_waterbirds_mask_sensitivity/summary.txt`, `experiments/results/exp020_waterbirds_mask_sensitivity/fig_mask_sensitivity.png`
[#001-B-001] 領域の主要ベースラインが欠落（Spurious Score, Salient ImageNet等）
    [方針]
        Spurious Score（Neuhaus et al., 2023）または Salient ImageNet（Singla et al., 2022）を Waterbirds で最低1手法(良かった方もしくは両方)追加する。
        主張は「勝敗」ではなく、専用手法の検出結果と Δ の操作的必要性測定の差分を示す。
        対応実験: exp021
    [対応] 完了。exp021 で specialized score を生成し、本文の Waterbirds 節に追記済み。
    [証拠ファイル] `experiments/results/exp021_waterbirds_specialized_baseline/specialized_scores.csv`, `experiments/results/exp021_waterbirds_specialized_baseline/summary.txt`
[#001-B-002] Waterbirds の worst-group accuracy が未記載
    [方針] `compute_waterbirds_wga.py` で group-wise accuracy を算出し、worst-group を本文・表に追記。
    [対応] 完了。`exp019` で30シード分の `worst_group_results.csv` / `worst_group_summary.txt` を確定し、mean worst_group_acc=0.3424（std=0.0804）を取得。
    [証拠ファイル] `experiments/results/exp019_waterbirds_wga/worst_group_results.csv`, `experiments/results/exp019_waterbirds_wga/worst_group_summary.txt`
[#001-B-003] LunarLander の分析が環境設計の問題（報酬減衰）と適用境界の問題と混同されている
    [方針] 本文から削除し Appendix へ移動。言及は Limitations のみに集約する。
    [対応] 完了。本文主張から切り離し、Appendix 中心の扱いに修正。
[#001-C-001] 信頼区間・誤差棒・統計検定の完全欠落
    [方針] 全検出率に Wilson 95% CI を併記し、Δ vs SHAP に対して McNemar 検定を実施する。
    [対応] 完了。`compute_stats.py` で exp016/017/018 の Wilson CI + McNemar を算出し `stats.txt` を保存。
[#001-C-002] n=5 の正当化が不足（領域標準は n=20 以上）
    [方針] n=30 で再実験中。
    [対応] 完了。exp017（CMNIST）120/120、exp018（Waterbirds）30/30 で完走。
[#001-C-003] exp005 と exp011 のシード独立性が不明（同一オラクルの使い回しかどうか）
    [方針] exp005 と exp011 のシード独立性 を Experiments 節冒頭で明示
    [対応] 完了。Experiments 節に「同一オラクル・同一シード」の注記を追記。
[#001-X-001] LunarLander が contributions 風に言及されすぎ
    [方針] [#001-B-003] に同じ。Appendix へ移動。
    [対応] 完了。([#001-B-003] に同じ)
[#001-X-002] 数値対応はとれているが「相補的」の一般化が過大主張
    [方針] 「常に相補的」を避け、特徴相関が強い条件・符号化制約が強い条件などの条件付き主張へ弱める。
    [対応] 完了。Abstract/Introduction/Discussion/Conclusion の主張を条件付き表現へ修正。
[#001-X-003] CI・誤差棒・有意性検定が完全欠落
    [方針] [#001-C-001] に同じ。
    [対応] 完了。([#001-C-001] に同じ)
[#001-X-004] ハイパーパラメータ（MLP 構造、IRM ペナルティ係数、学習率等）が未記載
    [方針] Appendixに追記。
    [対応] 完了。Appendix B に実験別ハイパーパラメータ表を追記。
[#001-X-005] 計算資源・データセットバージョン・コード URL が欠如
    [方針] Appendixに追記。
    [対応] 完了。Appendix C/D に計算資源・データセット・コード公開方針を追記。
[#001-X-006] 概ね flowing prose だが Limitations 以外の引用密度が低い
    [方針] 検討中
    [対応] 完了。Method/Discussion で Janzing, Adebayo, Neuhaus, Eyuboglu 参照を増強。
[#001-X-007] Figure ゼロ → Desk Reject
    [方針] 追記。
    [対応] 完了。`plot_results.py` で fig_psweep / fig_crosstab / fig_scatter / fig_delta_dist を生成。
[#001-X-008] Method/Experiments/Discussion での引用が不十分（Janzing, Adebayo等）
    [方針] [#001-A-001] に同じ。Method/Experiments/Discussion で Janzing と Adebayo を増強。
    [対応] 完了。([#001-A-001] に同じ)
[#000-X-001] ColoredMNIST で SHAP 比較（「Δ > SHAP」を非 RL 環境でも示す）
    [方針] exp017（30シード）で Δ と SHAP を同一オラクル・同一シードで比較。
    [対応] 完了。exp017 結果と `stats.txt` 反映済み。
[#000-X-002] Waterbirds 等の実世界データ（デザインされた spuriousness ではなく、自然発生の spurious correlation で動くかを示す）
    [方針] exp018（30シード）で Δ と SHAP を比較し、散布図と統計検定を追加。
    [対応] 完了。exp018 結果・図・`stats.txt` 反映済み。
[#000-X-003] Δ プロファイル（argmax に潰す前）の使い方を示す。今は「何番目が一番 Δ が大きいか」で終わっていますが、main claim が「プロファイルとして依存度を定量化する」なら、全特徴の Δ をランキングとして提示する実験が要る
    [方針] GridWorld（exp016）で top-k（@1/@2）を併記し、ランキング情報を残す。
    [対応] 完了。exp016 の top-k 表と `stats.txt` に反映済み。
[#000-X-004] SHAP 絞り込み後介入のハイブリッド案の議論 特徴数が多いとき全探索が重いという問題への対策
    [方針] 主張「SHAPは信頼できない」と少し矛盾。「全探索Δは中規模特徴数では現実的、ハイブリッドはSHAPの信頼性が期待できる設定に限定される。」とか1行書くだけかも。
    [対応] 完了。Discussion に「full Δ scan を基本、絞り込みは計算近似」として限定記述を追加。
[#000-X-005] baseline が SHAP だけ。 permutation importance 、 LIME と差別化の説明か比較実験が必要
    [方針]
        SHAP/LIMEに加えて Waterbirds で専用手法ベースラインを追加（exp021）。
        あわせて「何を測っているか」の軸で比較表を作成（検出率、判定安定性、計算コスト、介入整合性）。
        LIME は準備中実装を活かして補助比較、主比較は専用手法 vs Δ に置く。
    [対応] 完了。exp021 で Waterbirds の専用ベースラインを追加し、本文でも Δ と役割の違いを追記済み。
    [証拠ファイル] `experiments/results/exp021_waterbirds_specialized_baseline/specialized_scores.csv`, `experiments/results/exp021_waterbirds_specialized_baseline/summary.txt`
[#000-X-006] 連続大規模環境で介入テストをスケールさせる方法
    [方針] SHAP 絞り込み後介入の条件付き利用を Discussion で限定記述。
    [対応] 完了。Discussion でスケール時の近似運用方針を追記。
[#000-X-007] 特徴の型（連続/バイナリ/画像変換）を統一的に扱うインターフェース設計
    [方針] 介入演算子の妥当性条件（破壊度/非対象保持）として抽象化し Method に統合。
    [対応] 完了。Method の妥当性条件として統一記述を反映。
