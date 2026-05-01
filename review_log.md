[#003-A-001] 介入の妥当条件がまだ部分的にしか形式化されていない
    [方針]
        介入 family ごとの admissibility 条件を短い小節で明示する。
        ここでの論点は「単に壊したから性能が落ちた（OOD 由来の困惑）」のか、「スプリアス依存があるから落ちた」のかを峻別することにある。
        したがって、妥当な介入とは「対象特徴の予測情報を十分に破壊しつつ、非対象特徴の統計をできるだけ保持する」近似として定義し、破壊型コントロールと構造保持型介入を分けて記述する。
        実装上は、class-consistent な背景置換や foreground マスク摂動のように、target feature だけを狙って壊し、他の特徴を OOD にしすぎない境界線を明示する。
    [対応] 完了。Method 節で admissibility 条件と OOD 破壊との区別を記述済み。
    [証拠ファイル] `draft.md`
[#003-A-002] 検出ルールが top-k と rank-based で揺れている
    [方針]
        判定文言を統一し、rank-based success か top-k inclusion かを明示的に分けて書く。
        Method / Results / Conclusion で同じ評価語彙を使う。
    [対応] 完了。Method / Results で top-k, recall@k を明示済み。
    [証拠ファイル] `draft.md`
[#003-A-003] specialized baseline の proxy score の意味づけがやや弱い
    [方針]
        Spec/PCA は candidate spuriousness proxy、Delta は intervention-based necessity として役割を明示する。
        専用ベースラインを「候補確認」ではなく「functional dependence の直接指標ではない」ものとして位置づける。
    [対応] 完了。Waterbirds 節で proxy score の役割を本文化済み。
    [証拠ファイル] `draft.md`
[#003-B-001] specialized-baseline 比較の domain 上の説明がまだ少し薄い
    [方針]
        Waterbirds 節で、Spec/PCA が何を推定しているのかを1段落で明示する。
        Delta との比較軸を「候補 spuriousness vs 必要性」として固定する。
    [対応] 完了。Waterbirds 節で専用ベースラインの推定対象を説明済み。
    [証拠ファイル] `draft.md`
[#003-B-002] discordant pairs の意味を本文で一言で明示した方がよい
    [方針]
        exp021 の disagreement を「Delta の負け」ではなく「測っている量の違い」として説明する。
        代表的な不一致シードの補助表を短く添える。
    [対応] 完了。Discordant pairs の意味づけと代表シード表を draft に追記済み。
    [証拠ファイル] `draft.md`, `experiments/results/exp021_waterbirds_specialized_baseline/results.csv`
[#003-B-003] conclusion の射程がまだ少し広い
    [方針]
        結論は tested benchmarks と intervention-based diagnosis に限定して書く。
        一般の spurious-feature detection を解決したような言い回しは避ける。
    [対応] 完了。Conclusion の文言を tested benchmarks / intervention-based diagnosis に寄せて修正済み。
    [証拠ファイル] `draft.md`
[#003-C-001] 統計表現がまだ完全には統一されていない
    [方針]
        主結果表と caption で counts / percentages / Wilson CI の見せ方をそろえる。
        主要表だけでも表記ルールを固定する。
    [対応] 完了。主要表と Waterbirds 記述で Wilson CI を含めた表現へ揃え済み。
    [証拠ファイル] `draft.md`
[#003-C-002] exp021 の図キャプションと本文の統計言語を揃える必要がある
    [方針]
        Delta は intervention-based necessity、Spec/PCA は proxy scores という表現に統一する。
        図キャプションも同じ語彙に合わせる。
    [対応] 完了。exp021 の図キャプションを本文と同じ語彙へ統一済み。
    [証拠ファイル] `draft.md`
[#003-C-003] exp021 の disagreement table はもう少し compact にした方がよい
    [方針]
        代表的な seed を 2〜3 例に絞る。
        列定義を明確化し、どの値が何を意味するかを一目で分かるようにする。
    [対応] 完了。代表 3 seed に圧縮した disagreement table を draft に追加済み。
    [証拠ファイル] `draft.md`
[#003-D-001] 手法名のブランディング
    [方針] 手法名を "PerformanceCheck" に統一。アクロニムを避け、「性能という動かぬ証拠で最終確認する」という実用的な本質を強調する。
    [対応] 未
[#003-D-002] 介入マスク（GrabCut）の不確実性の定量的言及
    [方針] GrabCut の失敗が Δ に与える影響について、Limitations または Method で補足する。
        30 seed 全体で、mask radius を変えたときに判定がどれくらい変わるかを exp022 で確認する。
    [対応] 進行中。exp022 で checkpoint 再利用のまま GrabCut mask perturbation を 30 seed 全体で評価する。
[#003-E-001] 診断から判断・修正への接続
    [方針] PerformanceCheck を「ドメイン専門家が修正の優先順位を判断するための、定量的エビデンス提供パーツ」と位置づける。Discussion では、出力された Δ 値を参考に、専門家がどの特徴に Augmentation 等を適用すべきかを選択する、人間を介した（Human-in-the-loop）ワークフローの一環として記述する。
    [対応] 未
[#003-E-002] 統計的な存在と機能的な依存の分離
    [方針] 不一致 12 シードの分析を、「既存手法が『バイアスの存在』を警告した際、PerformanceCheck が『モデルはそれを実用上無視できているか』という補足情報を与える例」として記述する。これにより、専門家がドメイン知識に照らして、検出された特徴がスプリアスか否か、修正が必要か否かを判断するための多角的な視点を提供できることを強調する。
    [対応] 未
[#003-F-001] 図のキャプション情報の充実
    [方針] 各 Figure のキャプションを、「何を示し、何が結論か」まで含めた自己完結的な説明に書き換える。
    [対応] 未
[#003-F-002] 本文と表の数値重複（アンチ・リピティション）
    [方針] 本文中の数値を「有意な向上」「3割程度の低下」などの定性的表現に置き換え、正確な値は表に委ねる。
    [対応] 未
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
    [対応] [#001-B-003] に同じ（完了）。
[#001-X-002] 数値対応はとれているが「相補的」の一般化が過大主張
    [方針] 「常に相補的」を避け、特徴相関が強い条件・符号化制約が強い条件などの条件付き主張へ弱める。
    [対応] 完了。Abstract/Introduction/Discussion/Conclusion の主張を条件付き表現へ修正。
[#001-X-003] CI・誤差棒・有意性検定が完全欠落
    [方針] [#001-C-001] に同じ。
    [対応] [#001-C-001] に同じ（完了）。
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
    [対応] [#001-A-001] に同じ（完了）。
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







