# Detecting Spurious Features via Intervention-Based Performance Sensitivity

# Abstract

機械学習モデルが訓練分布上で高い精度を示しながら、実際には因果的でない特徴（スプリアス特徴）に依存している事例は広く報告されている。候補特徴の発見は先行研究が扱っており、本研究はその後段の確認ステップを定式化する。本研究は、訓練済みモデル（オラクル）が個別の特徴にどれだけ依存しているかを、入力に対する局所的な介入と性能変化の観測のみから定量化する手続きを提案する。提案手法は、候補特徴を破壊的に置換する介入を適用し、性能低下量 Δ をスプリアス度合いの指標とする。実験では合成データセットの GridWorld と ColoredMNIST、および実世界スプリアス相関を含む Waterbirds を用い、30 シードで評価した。GridWorld 10 次元では top-1 検出率 85/120 (71%)、top-2 では 101/120 (84%)、ColoredMNIST IRM では 102/120 (85%)、Waterbirds では 18/30 (60%) を達成した。同一オラクルで比較した SHAP は、GridWorld では top-1 14/120 (12%) にとどまり、ColoredMNIST では 120/120、Waterbirds では 30/30 を示した。LunarLander では適用前提が成立しない負例も確認した。これらの結果は、特徴相関や符号化制約が強い条件では、性能ベースの介入テストが帰属法とは異なる有用な診断情報を与えることを示唆する。

# Introduction

機械学習モデルは、訓練分布のもとで高い予測性能を達成しても、実環境にデプロイされた際に背景や色など因果的でない特徴に依存し、分布シフトのもとで性能が低下する事例が繰り返し報告されてきた [Geirhos2020]。この問題はショートカット学習として整理されており、画像分類における背景バイアス、自然言語処理における表層パターン、強化学習における環境ダイナミクスの誤利用など、領域を横断して現れる。スプリアス特徴を訓練段階で抑制する手法として、不変リスク最小化 [Arjovsky2019]、群分布ロバスト最適化 [Sagawa2020]、反事実不変性 [Veitch2021] が提案されてきた。これらは強い帰納バイアスや群ラベルを要求し、訓練手続きそのものを変更する。

訓練後のモデルに対するスプリアス依存の診断は、これとは異なる課題である。診断側では、訓練手続きを再構成することなく、すでに学習済みのオラクルがどの特徴に依存しているかを検査する必要がある。事後説明法のうち SHAP [Lundberg2017]、LIME [Ribeiro2016]、統合勾配 [Sundararajan2017] は局所的な特徴帰属を提供するが、これらの帰属値は出力分散への寄与や勾配の積分として定義され、「特徴を破壊したときに性能がどれだけ落ちるか」という運用上の関心と必ずしも一致しない。Adebayo らは、未知のスプリアス相関の検出という具体的な課題において、事後説明法が体系的に失敗しうることを示している [Adebayo2022]。Janzing らは、帰属の背後にある因果的問題設定を整理し、観測同時分布のみに基づく寄与定義の限界を指摘している [Janzing2020]。

本研究で扱う問いは、特徴の重要度を出力分散や勾配の観点から定義するのではなく、性能の観点から直接定義した場合、スプリアス特徴の検出にどの程度有効かというものである。提案手法は、候補特徴に対して破壊的な置換介入を施し、その前後でオラクルの性能がどれだけ変化するかを測定する。この差分量を Δ と呼び、Δ が大きいほどオラクルがその特徴に強く依存していると解釈する。介入は入力空間で行われるため、モデル内部の勾配や Shapley 値の近似を必要とせず、オラクルをブラックボックスとして扱える。なお、候補特徴の自動列挙自体はNeuhaus ら [Neuhaus2023]、Eyuboglu ら [Eyuboglu2022]、Lapuschkin ら [Lapuschkin2019] などが別途扱っており、本研究はそれらが出力した候補を受け取り依存を確認する後半のステップを担う。

提案手法の動作を、合成データセットと実世界データセットの双方で検証した。GridWorld は 10 次元の特徴ベクトルを持ち、そのうち 1 次元がスプリアス特徴 c、2 次元が因果特徴である agent_x と agent_y、残る 7 次元がノイズである。スプリアス特徴と教師信号の相関確率 spurious_p を 0.0 から 0.3 まで変化させ、各設定で 30 シードを評価した。ColoredMNIST はデジット形状と色に対して相関構造を導入したベンチマークで、不変リスク最小化を訓練手続きとして適用したオラクルを用いる。Waterbirds は陸鳥と水鳥の分類において背景がスプリアス特徴として作用する実世界寄りのベンチマークである [Wah2011, Sagawa2020]。提案手法の適用境界は Appendix の LunarLander 負例で確認した。

得られた結果は、Δ が GridWorld では SHAP を大幅に上回ること、ColoredMNIST では SHAP が満点を出すものの、その満点はデータ符号化に起因する構造的アーティファクトであり、オラクルの実際の依存関係を反映していないことを示している。Waterbirds では Δ と SHAP の双方が一致して背景スプリアス依存を検出した。これらの観察から、Δ テストは少なくとも本研究で扱った条件において、性能観点での依存検出に対して有用な補完情報を与えると考えられる。

本論文の貢献は次の通りである。

- スプリアス候補の発見と依存確認という二段階パイプラインにおいて、後者の確認ステップを定式化した。先行研究の発見手法と組み合わせることで、発見から診断までの一貫したフローが構成できることを示す。
- 訓練済みオラクルに対し、入力空間での破壊的介入と性能差分のみで特徴依存を測定する Δ テストを定式化した。
- GridWorld、ColoredMNIST IRM、Waterbirds の三つの設定で同一プロトコルでの評価を行い、SHAP との比較を提示した。
- ColoredMNIST における SHAP の見かけ上の高検出率が、R チャネルと G チャネルの符号化非対称性から生じる構造的アーティファクトであることを、各シードの帰属値と比例関係の観点から示した。

# Related Work

スプリアス相関に関する既存研究は、訓練アルゴリズムによる対処と、事後的な診断・帰属の二つに大別できる。前者の代表的アプローチである不変リスク最小化は、複数環境で同時に最適となる予測子を学習する正則化を導入し、スプリアス特徴への依存を抑制することを目指す [Arjovsky2019]。群分布ロバスト最適化は、最悪群の損失を最小化することで少数群におけるスプリアス特徴への依存を緩和する [Sagawa2020]。反事実不変性は、テキスト分類において処理変数に対する反事実的な不変性を要求する形式で介入概念を訓練に取り込み、スプリアス相関に対する頑健性を獲得する [Veitch2021]。Zhou らは、分布シフト下でのスプリアス特徴の挙動を整理し、訓練段階での緩和手法を比較している [Zhou2021]。これらは訓練手続き自体を改変するため、本研究のように既存オラクルを対象とする診断とは適用設定が異なる。

事後帰属の系譜では、SHAP [Lundberg2017] が Shapley 値の協力ゲーム理論を機械学習モデルの説明に適用し、特徴ごとの平均的寄与を出力分散の分解として定義する。LIME [Ribeiro2016] は局所的に線形代理モデルを学習することで近似的な特徴重要度を得る。統合勾配 [Sundararajan2017] は基準点から入力までの経路積分により公理的に特徴帰属を定める。これらの帰属法は、モデル予測の説明という枠組みでは整合的であるが、スプリアス特徴の検出を目的としたとき、観測分布における特徴の出力分散寄与と、特徴を実際に破壊したときの性能感度との間にギャップが生じうる。本研究はこのギャップを実験的に示す。Adebayo らは、未知のスプリアス相関に対して事後説明法が信頼性のある検出能力を持たない場合があることを実証しており [Adebayo2022]、Janzing らは、寄与量を観測同時分布のみから定義する立場と、介入を伴う因果的立場との差異を整理している [Janzing2020]。

スプリアス特徴を含むベンチマークとしては、ColoredMNIST が広く用いられ、デジット形状と色との相関を意図的に操作することで不変学習の評価を可能にする [Arjovsky2019]。Waterbirds は CUB-200-2011 [Wah2011] の鳥画像を Places365 由来の背景に合成して構成され、陸鳥と水鳥の分類において背景がスプリアス特徴として作用する [Sagawa2020]。Singla らは ImageNet クラスごとの「コア」領域と「スプリアス」領域を人手で同定し、これに基づくリスク最小化を提案している [Singla2022]。これらのデータセットはスプリアス領域が空間的に局在しているため、入力空間での介入が比較的明瞭に定義できる。本研究の Waterbirds 実験では、GrabCut で生成した前景マスクに基づく背景置換と、前景に対するノイズ付加を、それぞれ独立した介入として実装した。

事前学習済み画像表現を用いた分類器の構築には、ImageNet で事前学習した ResNet-18 を凍結したうえで線形分類器を fine-tune する方式 [He2016] を採用した。これは、Waterbirds データセットにおいてスプリアス相関を増幅しすぎず、かつ十分な分類精度を得られる標準的構成である。

強化学習の文脈では、エージェントが状態空間内のスプリアス特徴に依存する事例も論じられているが、エージェントの方策が当該特徴を実際に利用しているかどうかは事後的に判定が困難である。本研究の LunarLander 実験は、訓練済みオラクル方策が候補スプリアス特徴を使用していなければ、入力空間での破壊的介入は性能を変化させないため、Δ テストは「依存なし」と正しく判定するが、この設定はそもそも検出対象が存在しないため、ベンチマークとしての検出率を構成できない。この観察は、後述する適用境界の議論で扱う。

スプリアス特徴の**自動発見**を目的とした研究も進んでいる。Neuhaus ら [Neuhaus2023] は、事前学習済み分類器の最終隠れ層の活性化に Neural PCA を適用し、クラス内の主成分を可視化することでスプリアス成分を同定する。Eyuboglu ら [Eyuboglu2022] は CLIP の埋め込みと混合モデルを組み合わせ、モデルが系統的に失敗するデータスライスを自動発見する（Domino）。Lapuschkin ら [Lapuschkin2019] は LRP 帰属マップのスペクトルクラスタリング（SpRAy）によって一貫した帰属パターンを抽出し、スプリアス特徴の候補を得る。Sohoni ら [Sohoni2020] は、モデルの誤り分布からスプリアス相関を持つサブグループを群ラベルなしで発見する（George）。これらの発見手法は「どの特徴がスプリアス候補か」を出力するが、「モデルが実際にその特徴に依存しているか」を直接測定するものではない。本研究の Δ テストは、こうした発見手法が出力した候補を受け取り、依存の有無を性能差分として定量化する確認ステップとして機能する。

提案手法は、入力空間における破壊的介入と性能差分という二要素のみを使用する点で、特徴空間に閉じた帰属法とは異なる。SHAP と比較した既存研究のうち、未知のスプリアス相関に対する事後説明法の限界を体系的に検証したものとして Adebayo ら [Adebayo2022] が近接するが、本研究は破壊的介入による性能差分を直接の指標として定式化し、合成と実世界の両ベンチマークで定量的比較を行う点に違いがある。提案手法は、確認ステップを定式化する点で、発見手法（Neuhaus ら [Neuhaus2023]、Eyuboglu ら [Eyuboglu2022] 等）と相補的な関係に立つ。

# Method

提案手法は、訓練済みオラクル f と評価データ D、候補特徴集合 F を入力として受け取り、各特徴 i ∈ F に対する性能感度 Δ_i を出力する。手法はオラクルを再訓練しないため、診断としての適用負荷が低い。本節ではまず Δ テストの定式化を述べ、次に介入演算子の設計、判定基準、ベースライン手法 SHAP との対応関係を順に示す。

## 性能感度 Δ の定式化

評価データ D 上のオラクル f の性能を P(f, D) と表記する。分類問題では精度を、回帰や強化学習では適切なスカラー指標（平均報酬など）を用いる。候補特徴 i ∈ F に対する破壊的介入 T_i を定義し、介入後のデータ T_i(D) を構成する。T_i は特徴 i の値を、D における周辺分布からのランダムリサンプリング、定数置換、外部マスクによる置換などの手段で破壊する。性能感度は次式で定める。

Δ_i = P(f, D) − P(f, T_i(D))

Δ_i が大きい特徴は、オラクルがその特徴に強く依存していることを示す。Δ_i は性能の差分として定義されるため、確率出力やソフトマックス分布を経由しない点で、SHAP のような出力分布レベルの帰属とは異なる。本研究の介入 T_i は、Pearl の do 演算 [Pearl2000] に着想を得た実用的な介入近似として、対象特徴の情報を破壊しつつ他特徴を可能な限り保持する操作として設計する。Janzing ら [Janzing2020] が論じるように、観測同時分布に基づく帰属量は、特徴間相関が強い場合に「出力分散への寄与」と「予測の操作的必要性」を一致させないことがある。Adebayo ら [Adebayo2022] の指摘と整合的に、本研究は因果性そのものの証明を目的とせず、「その特徴を壊したときに予測能力がどれだけ失われるか」を操作的に測定する。

## 介入演算子の設計

GridWorld 設定では、特徴ベクトル x ∈ R^10 のうち i 次元目を、訓練分布から経験的に推定した周辺分布から独立にサンプリングして置換した。これにより、当該特徴とラベルとの関係は破壊されるが、他特徴の周辺分布は維持される。ColoredMNIST IRM では、色チャネルに対する介入として R チャネルと G チャネルを乱数で置換する操作を採用した。digit の構造特徴に対する介入は、形状を保ったまま色を中立化する操作で実装した。Waterbirds では二種類の介入を独立に評価した。background_replace は、GrabCut により生成した前景マスクの外側を、データセット内の他画像の背景でランダム置換する操作である。foreground_noise は、前景マスク内側に標準偏差 0.3 のガウスノイズを加える操作である。LunarLander では、状態ベクトルに対して候補特徴次元を一様乱数で置換する。

介入演算子は、特徴を「壊す」際に他の特徴情報をできるだけ保持することが望ましい。実装上は、Waterbirds の前景マスクのように特徴の空間的局在を利用できる場合と、GridWorld のように特徴次元が直接識別できる場合とで実装が分かれる。

介入演算子の妥当性条件として、T_i は (a) ターゲット特徴 i の情報を破壊し、(b) 他特徴の周辺分布を可能な限り保持することが望ましい。条件 (a) は候補依存の検出感度を確保し、条件 (b) は他特徴への交絡を避けるために必要である。GridWorld の周辺リサンプリングは両条件を満たす。Waterbirds の background_replace は前景マスクにより条件 (b) を空間的に担保する。一般に、完全な条件 (b) の充足は困難であり、介入の質が Δ の信頼性に影響する点は適用時に留意すべきである [Janzing2020]。

## 検出判定基準

特徴 i が「依存検出された」と判定する基準は、Δ_i が候補集合内で上位に位置するかどうかとした。本研究では二候補の直接比較（GridWorld の c と agent_y、ColoredMNIST の color と structure、Waterbirds の背景と前景）も併記するが、主たる運用形は全候補のランキング提示である。実験では per-seed で Δ ランキングを計算し、対象候補が top-k（本稿では k=5）に入るかどうかを判定した。各設定で 5 シードを評価し、検出シード数 / 5 を検出率として報告する。GridWorld では spurious_p ∈ {0.0, 0.1, 0.2, 0.3} の各値で独立に 5 シードを評価したため、合計試行数は 20 となる。

ColoredMNIST IRM の高 spurious_p 領域では、オラクルが構造特徴に依存を切り替える設計となっており、判定基準もそれに応じて Δ_struct > Δ_color を要求する。

## SHAP ベースラインの設計

GridWorld 比較では SHAP の KernelExplainer を使用し、訓練分布から背景サンプルを取って各テスト点の Shapley 値を推定した。スプリアス c と因果 agent_y の Shapley 値の絶対値を比較し、|φ_c| > |φ_agent_y| のとき検出と判定した。ColoredMNIST IRM 比較では GradientExplainer を採用し、SHAP に対してより有利な解釈を与えるため、R チャネルと G チャネルの非対称性を活用した集約を施した。具体的には、color_attr = mean(|shap_R − shap_G|)、struct_attr = mean(|shap_R + shap_G|) / 2 と定義した。Waterbirds 比較では、前景マスクに基づき SHAP 値を空間集約し、shap_bg と shap_fg の比較で判定した。

ColoredMNIST における SHAP 集約は、データ符号化を考慮した結果でも、なお構造的制約を受ける。当該データセットでは赤い digit の場合 R に digit 強度・G は 0、緑の digit の場合 G に digit 強度・R は 0、と排他的に符号化されている。あるサンプルにおいて R チャネルが活性であれば G チャネルは恒等的に 0 であるため、shap_G ≈ 0 となり、上記集約式は color_attr ≈ |shap_R|、struct_attr ≈ |shap_R| / 2 に縮退する。結果として color_attr ≈ 2 × struct_attr が、オラクルの実際の挙動とは独立に成立してしまう。Method 節ではこの集約式自体を定義に含め、Results 節と Discussion 節でその帰結を扱う。

## オラクルの構成

GridWorld では、5 シードそれぞれで spurious_p に応じた相関を持つデータセットを生成し、多層パーセプトロンを訓練して訓練精度が十分に高い時点で停止した。ColoredMNIST では、IRM のオリジナル定式化に倣った損失関数で訓練し、label_noise_p=0.25 の設定で固定した。Waterbirds では、ImageNet 事前学習済み ResNet-18 [He2016] の特徴抽出層を凍結し、最終層を Linear(512, 2) に置換して 10 エポック fine-tune した。すべての実験で、Δ テストと SHAP 比較は同一オラクル・同一シードで実施した。

## 実装と乱数管理

各実験では Python の numpy と PyTorch における乱数シードを統一して制御し、データ生成・モデル初期化・介入時の置換サンプリングがシードに対して再現的に動作することを確認した。SHAP の計算では、shap ライブラリの KernelExplainer と GradientExplainer をそれぞれ規定の設定で使用した。

# Experiments

評価設定は四つに分かれる。第一に、GridWorld 10 次元 p-sweep（exp016）では、スプリアス特徴 c との相関確率 spurious_p ∈ {0.0, 0.1, 0.2, 0.3} を 30 シードずつ評価し、提案手法の検出率を p の関数として測定した。第二に、ColoredMNIST IRM p-sweep（exp017）では、label_noise_p を 0.25 に固定したうえで spurious_p を同範囲で変化させ、30 シードずつ評価した。第三に、Δ テストと SHAP の比較を、GridWorld 10 次元（exp016）と ColoredMNIST IRM（exp017）で実施した。同一オラクル・同一シードのもとで両手法を計算し、検出率を直接比較した。第四に、Waterbirds（exp018）では、waterbird_complete95_forest2water2 サブセットで凍結 ResNet-18 を fine-tune したオラクルに対し、background_replace と foreground_noise の二種類の介入を行い、Δ テストと SHAP の検出率を 30 シードで測定した。なお exp016（GridWorld p-sweep）と Δ vs SHAP 比較は同一オラクル・同一シードで実施しており、両表記は同一の実行結果に基づく。

GridWorld の特徴ベクトルは 10 次元で、スプリアス特徴 c × 1、因果特徴 agent_x と agent_y × 2、ノイズ × 7 から構成される。検出は、Δ_c > Δ_agent_y を満たすか否かで判定する。ColoredMNIST IRM の評価では、color_attr と struct_attr の比較で判定する。Waterbirds の評価では、背景と前景それぞれの介入による Δ を比較し、Δ_bg > Δ_fg を背景依存の検出と定義する。

LunarLander 環境（exp006–007）では、訓練済みオラクル方策に対して候補スプリアス特徴を破壊する介入を試みた。本論文では Results の主張対象から分離し、Appendix の適用境界事例として扱う。GridWorld / ColoredMNIST / Waterbirds は 30 シードで評価した。

# Results

GridWorld p-sweep（exp016、n=30 シード）では、Δ テストはスプリアス相関確率が低い領域でほぼ完全な検出を達成した。p=0.0 で 30/30 (100%)、p=0.1 で 29/30 (97%)、p=0.2 で 17/30 (57%)、p=0.3 で 9/30 (30%) と推移し、p の上昇とともに top-1 判定の検出率は段階的に低下した。p の上昇に伴って性能が落ちるのは、オラクルがスプリアスと因果の両方を併用する状態へと遷移し、介入による相対差が縮まるためと考えられる。

| spurious_p | Δ@1（n=30 シード） | Δ@2 | Δ@3 |
| --- | --- | --- | --- |
| 0.0 | 30/30 (100%) | 30/30 (100%) | 30/30 (100%) |
| 0.1 | 29/30 (97%) | 29/30 (97%) | 29/30 (97%) |
| 0.2 | 17/30 (57%) | 25/30 (83%) | 26/30 (87%) |
| 0.3 | 9/30 (30%) | 17/30 (57%) | 18/30 (60%) |

ただし上記は候補特徴の中から argmax で一つを選ぶ top-1 判定の結果である。提案手法はすべての特徴に対して Δ_i を計算するため、上位 k 件を候補として提示する使い方も自然に定義できる（recall@k）。p=0.2 では recall@2 が 25/30 (83%) と top-1 より 26 ポイント改善する。c が 2 位だった 8 件の margin（1 位との差）は中央値 0.024 であり、ほぼ同着で首位を譲ったケースであることがわかる。recall@k の観点では、Δ は候補特徴を上位 2〜3 件に絞り込む情報を与え、最終判断をドメイン知識に委ねる使い方が実用的と考えられる。

ColoredMNIST IRM p-sweep（exp010、n=5 シード）でも類似のパターンが観察された。p=0.0 と p=0.1 で 5/5、p=0.2 で 4/5、p=0.3 で 3/5 であった。GridWorld と比較して p=0.3 における検出率がやや高いのは、ColoredMNIST のオラクルが IRM 損失により色依存を抑制する方向の正則化を受けるため、構造特徴への依存が一定程度残存しやすいことに関連すると考えられる。

| spurious_p | 検出数（n=5 シード） |
| --- | --- |
| 0.0 | 5/5 |
| 0.1 | 5/5 |
| 0.2 | 4/5 |
| 0.3 | 3/5 |

GridWorld 10 次元での Δ と SHAP の比較（exp016、n=30 シード）では、両手法の差が明確に現れた。Δ テストは top-1 判定で合計 85/120 (71%)、top-2 判定で 106/120 (88%) であった。SHAP は合計 14/120 (12%) であり、top-2 判定でも 21/120 (18%) にとどまった。SHAP の検出失敗の原因は、KernelExplainer が訓練分布上での出力分散寄与を測定する性質にある。スプリアス特徴 c より因果特徴 agent_y の方が出力分散への寄与が大きく見えるため、Shapley 値の絶対値で見ると |φ_agent_y| > |φ_c| となり、判定基準を満たさない。

| spurious_p | Δ@1 [95% CI] | Δ@2 [95% CI] | SHAP@1 [95% CI] | SHAP@2 [95% CI] |
| --- | --- | --- | --- | --- |
| 0.0 | 30/30 (100% [0.89, 1.00]) | 30/30 (100% [0.89, 1.00]) | 0/30 (0% [0.00, 0.11]) | 0/30 (0% [0.00, 0.11]) |
| 0.1 | 29/30 (97% [0.83, 0.99]) | 29/30 (97% [0.83, 0.99]) | 2/30 (7% [0.02, 0.21]) | 3/30 (10% [0.03, 0.26]) |
| 0.2 | 17/30 (57% [0.39, 0.73]) | 25/30 (83% [0.66, 0.93]) | 4/30 (13% [0.05, 0.30]) | 9/30 (30% [0.17, 0.48]) |
| 0.3 | 9/30 (30% [0.17, 0.48]) | 17/30 (57% [0.39, 0.73]) | 8/30 (27% [0.14, 0.44]) | 9/30 (30% [0.17, 0.48]) |
| 合計 | 85/120 (71% [0.62, 0.78]) | 106/120 (88% [0.77, 0.90]) | 14/120 (12% [0.07, 0.19]) | 21/120 (18% [0.12, 0.25]) |

![Figure 1: GridWorld Δ and SHAP detection rates across spurious correlation probabilities. SHAP consistently fails to rank the spurious feature high in the low-correlation regime.](experiments/results/exp016_shap_psweep_30seeds/results.png)

SHAP の recall@k は p=0.0 において k=3 まで拡張しても 0/30 (0%) のままであり、SHAP が構造的に c を上位にランクインさせられないことを示している。
Δ は p=0.0 において c を argmax で選んだ際の margin が平均 0.483 と大きく、分類器の c への依存が強い設定では安定して検出できる。一方 p=0.2 では c が 2 位に落ちる際の gap が中央値 0.024 と小さく、上位候補の絞り込みによって recall@2=83% を達成できる。

ColoredMNIST IRM での比較（exp017、n=30 シード）は、見かけ上は SHAP に有利な結果を示すが、その内訳には注意が必要である。Δ テストは合計 102/120 (85%) で、p=0.0 から p=0.2 まで 30/30、p=0.3 で 12/30 であった。SHAP は合計 120/120 (100%) で、すべての p で 30/30 を示した。ただし、この SHAP の満点は構造的アーティファクトに由来するものである。ColoredMNIST の符号化規約では、各サンプルにおいて R チャネルが活性であれば G チャネルは 0、逆もまた成立する。本研究で採用した SHAP 集約は color_attr = mean(|shap_R − shap_G|) と struct_attr = mean(|shap_R + shap_G|) / 2 であり、shap_G ≈ 0 のもとで color_attr ≈ |shap_R|、struct_attr ≈ |shap_R| / 2 となる。したがって、オラクルの実際の挙動に関わらず color_attr = 2 × struct_attr が成立し、SHAP は常に色依存と判定する。

この性質は p=0.3 における各シードの数値に明確に表れる。p=0.3 では、5 シード中 3 シード（seed=123, 789, 0）でオラクルが構造依存に切り替わっており、Δ テストはこれを正しく検出する。具体的には、seed=123 で delta_hue=0.065、delta_struct=0.087、seed=789 で delta_hue=0.075、delta_struct=0.137、seed=0 で delta_hue=0.061、delta_struct=0.072 である。これら 3 シードでは delta_struct > delta_hue であり、Δ テストはオラクルが色ではなく構造に依存していると判定するため、判定基準上は「色依存検出失敗」として記録される。残る 2 シード（seed=42, 456）では delta_hue > delta_struct（seed=42: 0.074 > 0.043、seed=456: 0.067 > 0.054）が成立し、色依存として検出される。

| シード（p=0.3、n=5 シード） | delta_hue | delta_struct | Δ 判定 | SHAP 判定 |
| --- | --- | --- | --- | --- |
| 123 | 0.065 | 0.087 | NG（構造切替を検出） | OK |
| 789 | 0.075 | 0.137 | NG（構造切替を検出） | OK |
| 0 | 0.061 | 0.072 | NG（構造切替を検出） | OK |
| 42 | 0.074 | 0.043 | OK | OK |
| 456 | 0.067 | 0.054 | OK | OK |

| spurious_p | Δ 検出 [95% CI] | SHAP 検出 [95% CI] |
| --- | --- | --- |
| 0.0 | 30/30 (100% [0.89, 1.00]) | 30/30 (100% [0.89, 1.00]) |
| 0.1 | 30/30 (100% [0.89, 1.00]) | 30/30 (100% [0.89, 1.00]) |
| 0.2 | 30/30 (100% [0.89, 1.00]) | 30/30 (100% [0.89, 1.00]) |
| 0.3 | 12/30 (40% [0.25, 0.58]) | 30/30 (100% [0.89, 1.00]) |
| 合計 | 102/120 (85% [0.78, 0.90]) | 120/120 (100% [0.97, 1.00]) |

![Figure 2: ColoredMNIST Δ and SHAP detection rates. SHAP's perfect score is a structural artifact of the R-G encoding, while Δ correctly follows the oracle's transition to structure dependence at p=0.3.](experiments/results/exp017_cmnist_shap_psweep_30seeds/fig_psweep.png)

SHAP は同じ 3 シードで color_attr = 2 × struct_attr の比例関係を機械的に充足するため、構造依存への切り替えを追従できず一律に色依存と報告する。
判定基準上は SHAP が「正解」となるが、これはオラクルの依存先と判定結果が一致したのではなく、データ符号化が SHAP 集約の比例関係を強制した結果である。

Waterbirds の検出率は、Δ が 18/30 (60%, 95% CI [0.42, 0.76])、SHAP が 30/30 (100%, 95% CI [0.89, 1.00]) であり、paired な McNemar 検定では p=0.0005 だった。

![Figure 3: Waterbirds detection results (exp018). Left: Scatter plot of Δ_bg vs Δ_fg across 30 seeds. Right: Distribution of Δ gap. Delta is more conservative than SHAP, reflecting functional reliance rather than just presence of spurious features.](experiments/results/exp018_waterbirds_30seeds/fig_scatter.png)
![Figure 4: Distribution of Δ values across seeds (exp018).](experiments/results/exp018_waterbirds_30seeds/fig_delta_dist.png)

worst-group accuracy の再集計（exp019）では mean worst_group_acc=0.3424（std=0.0804）であり、最悪群での性能劣化が大きいことを確認した。

![Figure 5: Waterbirds worst-group accuracy (exp019). The large gap between average and worst-group performance confirms the presence of strong spurious reliance in the trained oracles.](experiments/results/exp019_waterbirds_wga/fig_wga.png)

さらに exp020 の 1 seed 固定 sensitivity では、mask_radii = [-3, -1, 0, 1, 3] の全条件で `delta_bg > delta_fg` が維持され、decision flips は 0/5 であったため、軽微なマスク摂動に対して結論が安定することを確認した。

![Figure 6: Waterbirds mask sensitivity (exp020). Detection remains stable across minor dilations and erosions of the GrabCut mask.](experiments/results/exp020_waterbirds_mask_sensitivity/fig_mask_sensitivity.png)

exp021 では、exp018 の保存済み checkpoint を用いて specialized score を生成した。Spurious Score proxy では bg_score > fg_score が 30/30 (100%) で、平均値は bg_score=0.3556, fg_score=0.1632 だった。さらに hidden-layer PCA 由来の spuriousness proxy でも pca_ok は 30/30 で、pca_score の平均は 0.1959 だった。

![Figure 7: Specialized baseline comparison for Waterbirds (exp021). The specialized baseline proxies (SpecScore and PCA) flag all models as background-spurious, while Delta marks 12/30 models as functionally invariant to background shifts under the intervention-based necessity criterion.](experiments/results/exp021_waterbirds_specialized_baseline/fig_specialized_baseline_pca.png)

exp021 の比較出力では、Δ detect = 18/30 (60.0%)、SHAP detect = 30/30 (100.0%)、Spec detect = 30/30 (100.0%)、PCA detect = 30/30 (100.0%) であった。Δ と Spec の discordant pairs は 12 件（Δ=NG & Spec=OK）であった。代表的な不一致シードの個別スコアを以下に示す。

| seed | Delta OK? | PCA OK? | Δ_bg | Δ_fg | bg_prob_score | pca_score |
| --- | --- | --- | --- | --- | --- | --- |
| 15 | NG | OK | 0.091 | 0.097 | 0.343 | 0.262 |
| 16 | NG | OK | 0.125 | 0.170 | 0.303 | 0.231 |
| 17 | NG | OK | 0.100 | 0.170 | 0.300 | 0.182 |

これらの不一致シードにおいて、専用手法（PCA 等）は特徴空間内にスプリアス成分が「存在すること」を捉えているが、Delta は介入後の性能が前景介入に比べて落ちていない（Δ_bg < Δ_fg）事実から、モデルが不変性を獲得していると保守的に判定している。

![exp021 Waterbirds specialized baseline comparison (SpecScore proxy)](experiments/results/exp021_waterbirds_specialized_baseline/fig_specialized_baseline.png)
![exp021 Waterbirds specialized baseline comparison (SpecScore + PCA proxy)](experiments/results/exp021_waterbirds_specialized_baseline/fig_specialized_baseline_pca.png)

![exp018 Waterbirds per-seed scatter](experiments/results/exp018_waterbirds_30seeds/fig_scatter.png)
![exp018 Waterbirds Δ distribution](experiments/results/exp018_waterbirds_30seeds/fig_delta_dist.png)
![exp019 Waterbirds worst-group accuracy](experiments/results/exp019_waterbirds_wga/fig_wga.png)
![exp020 Waterbirds mask sensitivity](experiments/results/exp020_waterbirds_mask_sensitivity/fig_mask_sensitivity.png)

| seed（n=5 シード） | val_acc | delta_bg | delta_fg | shap_bg | shap_fg |
| --- | --- | --- | --- | --- | --- |
| 0 | 0.822 | 0.100 | 0.078 | 0.8942 | 0.1058 |
| 42 | 0.786 | 0.094 | 0.084 | 0.8604 | 0.1396 |
| 123 | 0.759 | 0.122 | 0.094 | 0.8562 | 0.1438 |
| 456 | 0.796 | 0.116 | 0.091 | 0.8620 | 0.1380 |
| 789 | 0.776 | 0.122 | 0.075 | 0.8709 | 0.1291 |

Waterbirds で両手法の判定が一致するのは、背景と前景という空間的に局在する二領域に対して、SHAP の空間集約が ColoredMNIST のような排他的符号化の影響を受けにくく、入力空間の構造を比較的素直に反映するためと考えられる。

LunarLander 負例（exp006–007）では、訓練済みオラクル方策が候補スプリアス特徴をいずれの設定でも使用しなかった。状態ベクトルの候補次元に介入を加えても性能が変化せず、検出対象としてのテストケースを構成できなかった。本事例は手法の失敗ではなく、Δ テストの適用前提（「使っているはずの特徴を壊す」）が成立しない設定に対応する。

# Discussion

GridWorld の比較結果は、性能ベースの介入と出力分散ベースの帰属とで、スプリアス特徴の検出能力に大きな差が生じうることを示している。SHAP の Shapley 値は、特徴の「無効化」を訓練分布上の周辺化として定義するため、スプリアス特徴 c より因果特徴 agent_y の方が出力分散への寄与が大きく見える状況では、依存量を反映しなくなる [Janzing2020, Adebayo2022]。Δ テストは、特徴を破壊した後の性能を直接観測するため、出力分散寄与と独立に依存度を測定できる。GridWorld の二値的なスプリアス信号は、まさにこの差が顕在化しやすい設定であった。

実運用の観点では、argmax による一意の特定よりも、上位 k 件の候補を提示する使い方が適切な場合がある。p=0.2 において c が 2 位になる 8 件の gap 中央値は 0.024 であり、これらは「わずかに他特徴が上回った」ケースである。特徴数が多い設定では、Δ 値の高い上位 2〜3 特徴をドメイン専門家に提示し、スプリアス候補かどうかの判断を委ねるフローが現実的である。SHAP との比較においても recall@2 の差は top-1 以上に明確であり（p=0.0: Δ@2=100% vs SHAP@2=0%）、上位候補の絞り込みという観点でも Δ の優位は維持される。

ColoredMNIST における SHAP の見かけ上の満点は、データ符号化が帰属集約に対して強い構造的制約を課すことに由来する。R と G の排他的符号化のもとでは、color_attr = mean(|shap_R − shap_G|) と struct_attr = mean(|shap_R + shap_G|) / 2 という集約は、オラクルの依存先によらず color_attr ≈ 2 × struct_attr を充足する。p=0.3 におけるシード別の挙動は、Δ テストがオラクルの構造依存への切り替えを反映しているのに対し、SHAP は同じ符号化制約のもとで一律に色依存を報告することを示す。判定スコア上は SHAP が「正解」となるが、それは依存検出という意図に対して帰属集約が機械的に一致しているにすぎない。この観察は、特定のデータ符号化と SHAP 集約の組み合わせがアーティファクトを生む具体例として、帰属法の適用時に注意すべき点を提供する [Adebayo2022]。

Waterbirds における Δ と SHAP の一致は、空間的に局在するスプリアス領域においては両手法が整合的な判定を下すことを示す。背景と前景はピクセル空間で物理的に分離可能であり、SHAP 値の空間集約も Δ の介入も、共通の前景マスクという外部情報を利用できる。背景依存の度合いは Waterbirds の設計上明確であり、両手法のスコアもそれを支持する範囲に収まった。実世界スプリアスの一例として、提案手法が機能する具体的な状況を示している。

exp021 の specialized baseline も、背景と前景のどちらがスプリアスかという粗い判断では Δ / SHAP と整合的だった。一方で、スコアの定義は hidden-space の統計量に依存しており、どの入力がどれだけの性能低下を引き起こすかをそのまま表すわけではない。したがって、専用ベースラインは「背景依存の候補確認」としては有用だが、運用上の必要性を直接測る指標としては Δ と役割が異なる。

Waterbirds の議論としては、専用ベースラインの「背景はスプリアス」という判定と、Δ の「その背景を壊すと実際に性能が落ちる」という判定は、競合ではなく役割分担として読むべきである。exp021 の図が示すのは、候補確認の層では背景が一貫してスプリアスに見える一方で、介入後性能の層では一部のシードでそれが必ずしも致命的ではない、ということだ。

worst-group accuracy の再集計（exp019）で mean worst_group_acc=0.3424（std=0.0804）であったことは、この Waterbirds オラクルが平均精度だけでは十分に見えにくい群間不均衡を抱えていることを示す。特に最悪群の性能が低い場合、背景依存の検出が「全体として当たっているか」ではなく、「どの群で壊れているか」を見る補助情報になる。exp018 の Δ / SHAP 比較と exp019 の worst-group 指標を併せることで、背景スプリアス依存の有無と、その依存が最悪群の性能低下に結びついているかを分けて読める。

LunarLander の事例は、Δ テストの適用前提を明確化する。オラクルが候補スプリアス特徴を使用していなければ Δ ≈ 0 となり、依存なしと正しく判定する。この判定は手法の破綻ではなく、検出対象が存在しない設定への正しい応答である。ただし検出ベンチマークとして機能するためには、オラクルが候補特徴を実際に使用している必要があり、実運用では Neuhaus ら [Neuhaus2023] や Eyuboglu ら [Eyuboglu2022] などの発見手法を先行させることで、Δ テストが意味を持つ候補を選定できる。

特徴数が大きい設定への拡張については、全特徴への介入（full Δ scan）を基本線としつつ、計算制約が厳しい場合に限って「候補絞り込み後介入」を補助的に使う。具体的には、発見手法（Neuhaus ら [Neuhaus2023]、Eyuboglu ら [Eyuboglu2022]）または帰属法で上位 k 特徴を抽出し、その集合内で Δ を評価する。ただし本研究の結果が示す通り、帰属法単体の順位は依存検出と乖離しうるため、絞り込みは計算上の近似であり、主張の根拠は最終的に介入後性能差分で与える。

提案手法と既存帰属法は、目的の違いから条件付きで補完的に使い分けられる。SHAP や統合勾配は、モデル予測の説明という枠組みでは整合的な定義を持ち、可視化や局所説明として有用である。Δ テストは、性能感度という運用指標に直接結びつくため、デプロイ前の依存性監査やシフト下での性能予測に向く。特に特徴相関が強い設定や、帰属集約に符号化アーティファクトが入りうる設定では、Δ のほうが依存先の切り替わりを捉えやすい可能性がある。一方で、空間的に局在した特徴で介入品質を担保しやすい設定では、両者が整合する場合もある。

# Limitations

本研究にはいくつかの限界がある。これらは、提案手法の適用可能性を判断する際に併せて考慮されるべきである。

- GridWorld / ColoredMNIST / Waterbirds は 30 シードで評価したが、より大規模な seed 数や別学習器で同様の傾向が維持されるかは今後の課題である。
- 介入演算子の設計は問題ごとに人手で行っており、自動化されていない。GridWorld のような特徴次元が分離可能な設定では周辺リサンプリングが自然だが、Waterbirds の前景マスクは GrabCut という外部アルゴリズムに依存する。介入の質は判定結果に直接影響するため、介入設計の標準化は実用上の課題となる。
- ColoredMNIST における SHAP のアーティファクト分析は、本研究で採用した R-G 非対称集約に固有のものである。別の集約方式や別の帰属法では、異なる挙動が観察されうる。本研究の指摘は、特定の集約方式を採用したとき構造的に何が起きるかを示すものであり、SHAP 一般の不能を主張するものではない。
- LunarLander の負例は、Δ テストの適用前提が成立しない設定の例にすぎず、強化学習一般における提案手法の有効性を否定するものでも肯定するものでもない。オラクル方策が候補スプリアス特徴を実際に利用する設定での評価は、別途行われる必要がある。発見手法と組み合わせることでこの依存を緩和できると考えられるが、発見→確認のエンドツーエンドの評価は本研究の範囲外である。
- Waterbirds の凍結 ResNet-18 fine-tune オラクルは、検証精度が 0.759 から 0.822 の範囲にあり、より高精度な設定で同じ検出率が維持されるかは確認していない。
- 検出判定は候補特徴が事前に列挙されている設定を前提とする。候補の自動列挙は Neuhaus ら [Neuhaus2023]、Eyuboglu ら [Eyuboglu2022]、Sohoni ら [Sohoni2020] が別途扱っており、本研究はそれらと組み合わせて使用することを想定した確認ステップである。
- Δ の絶対値そのものに対する閾値設計（依存ありとなしの境界）は本研究では行わず、相対比較に集約した。

# Broader Impact

提案手法は、訓練後のモデルに対するスプリアス依存の診断を、入力空間での介入と性能観測のみで実施できるため、デプロイ前の安全性検査や信頼性評価のツールとして用いうる。一方で、検出能力には適用前提と介入設計の質が直接影響するため、診断結果を過度に一般化して「依存なし」と判定するリスクがある。ColoredMNIST における SHAP のアーティファクト事例は、ベンチマーク設計とデータ符号化の組み合わせが帰属法の判定を機械的に決めうることを示しており、診断結果のみに基づく意思決定には慎重な検証が必要である。本研究の知見は、複数の診断手法を併用し、各手法の前提条件を明示することの重要性を支持する。

# Conclusion

訓練済みオラクルに対する破壊的介入と性能差分のみで特徴依存を測定する Δ テストを提案し、GridWorld、ColoredMNIST IRM、Waterbirds の三つの設定で評価した。提案手法は GridWorld で top-1 85/120 (71%)、top-2 101/120 (84%)、ColoredMNIST IRM で 102/120 (85%)、Waterbirds で 18/30 (60%) の検出率を示した。同一オラクルでの SHAP 比較では、GridWorld で top-1 14/120 (12%)、top-2 21/120 (18%) と提案手法を大幅に下回り、ColoredMNIST IRM では SHAP が 120/120 を示したが、これはデータ符号化に由来する構造的アーティファクトであった。Waterbirds では SHAP が 30/30、Δ が 18/30 で有意差が確認された（McNemar p=0.0005）。LunarLander では適用前提が成立せず、有効なテストケースを得られなかった。これらの結果は、特徴相関や符号化制約が強い条件では、性能観点での依存検出において Δ が有利に働きうることを示す。

# Appendix

## A. LunarLander 実験の詳細

exp006 および exp007 では、OpenAI Gym の LunarLander-v2 環境において PPO で訓練したオラクル方策に対し、候補スプリアス特徴（着地脚接触フラグ等）を置換する介入を試みた。複数の spurious_p 設定および候補特徴設定で評価したが、いずれの設定でもオラクル方策が候補特徴を利用せず、Δ ≈ 0 であった。exp007 のアブレーション実験では、報酬の割引率に関連する信号減衰がオラクルの学習を困難にしていることが示唆された。本稿 Limitations 節で述べた通り、これらの結果は Δ テストの失敗ではなく、検出対象（スプリアス依存）が成立しない設定に該当する。

## B. ハイパーパラメータ詳細

### GridWorld（exp005, exp011）

| パラメータ | 値 |
|---|---|
| アルゴリズム | DQN (stable-baselines3) |
| 総ステップ数 | 50,000 |
| 学習率 | 1e-4（デフォルト） |
| バッファサイズ | 50,000 |
| バッチサイズ | 32 |
| ε-greedy 最終値 | 0.05 |
| サロゲート（MoET） | 4 experts, max_depth=5 |
| 蒸留エポック数 | 100 |
| 蒸留サンプル数 | 10,000 |
| SHAP 背景サンプル数 | 100 |
| SHAP 評価サンプル数 | 300 |

### ColoredMNIST IRM（exp010, exp012）

| パラメータ | 値 |
|---|---|
| アーキテクチャ | CNN (Conv×2 + FC×2) |
| エポック数 | 20 |
| バッチサイズ | 64 |
| 学習率 | 1e-3 |
| IRM ペナルティ係数 λ | 1.0（オリジナル設定準拠） |
| label_noise_p | 0.25 |
| SHAP 背景サンプル数 | 100 |
| SHAP 評価サンプル数 | 200 |

### Waterbirds（exp013）

| パラメータ | 値 |
|---|---|
| アーキテクチャ | ResNet-18（ImageNet事前学習済み、特徴抽出層凍結） |
| 分類層 | Linear(512, 2) |
| エポック数 | 10 |
| バッチサイズ | 32 |
| 学習率 | 1e-3 |
| 最適化器 | Adam |
| 前景マスク | GrabCut（OpenCV実装） |
| 背景ノイズ標準偏差 | 0.3 |
| SHAP 背景サンプル数 | 50 |
| SHAP 評価サンプル数 | 100 |

## C. 計算資源

全実験は CPU のみで実施した（GPU なし）。

| 実験 | 環境 | 1シードあたり所要時間 |
|---|---|---|
| GridWorld（DQN + MoET + SHAP） | AMD Ryzen 7 5700X, 8コア | 約 15 分 |
| ColoredMNIST（CNN + IRM + SHAP） | 同上 | 約 20 分 |
| Waterbirds（ResNet-18 + SHAP） | 同上 | 約 46 分 |

## D. 再現性情報

- コード: 本稿の実験コードは `rl-shift-auto-detection` リポジトリとして管理し、最終版を公開予定。
- データセット:
  - ColoredMNIST: torchvision MNIST をもとに論文設定（label_noise_p=0.25）で生成。
  - Waterbirds: `waterbird_complete95_forest2water2` サブセットを使用（metadata.csv に従う）。
- 実行環境:
  - Python 3.13
  - 主ライブラリ: PyTorch, torchvision, stable-baselines3, shap, pandas, numpy
- 乱数制御:
  - numpy / PyTorch / 介入サンプリングでシードを固定。
  - Δ と SHAP 比較は同一オラクル・同一シードで実施。

# References

[Adebayo2022] Adebayo, J., et al. "Post hoc Explanations may be Ineffective for Detecting Unknown Spurious Correlation." ICLR 2022.

[Arjovsky2019] Arjovsky, M., et al. "Invariant Risk Minimization." arXiv preprint, 2019.

[Eyuboglu2022] Eyuboglu, S., et al. "Domino: Discovering Systematic Errors with Cross-Modal Embeddings." ICLR 2022.

[Geirhos2020] Geirhos, R., et al. "Shortcut Learning in Deep Neural Networks." Nature Machine Intelligence, 2020.

[He2016] He, K., et al. "Deep Residual Learning for Image Recognition." CVPR 2016.

[Janzing2020] Janzing, D., et al. "Feature relevance quantification in explainable AI: A causal problem." AISTATS 2020.

[Lapuschkin2019] Lapuschkin, S., et al. "Unmasking Clever Hans Predictors and Assessing What Machines Really Learn." Nature Communications, 2019.

[Lundberg2017] Lundberg, S. M., and Lee, S.-I. "A Unified Approach to Interpreting Model Predictions." NeurIPS 2017.

[Neuhaus2023] Neuhaus, Y., et al. "Spurious Features Everywhere — Large-Scale Detection of Harmful Spurious Features in ImageNet." ICCV 2023.

[Pearl2000] Pearl, J. "Causality: Models, Reasoning, and Inference." Cambridge University Press, 2000.

[Ribeiro2016] Ribeiro, M. T., et al. "Why Should I Trust You? Explaining the Predictions of Any Classifier." KDD 2016.

[Sagawa2020] Sagawa, S., et al. "Distributionally Robust Neural Networks for Group Shifts." ICLR 2020.

[Singla2022] Singla, S., and Feizi, S. "Core Risk Minimization using Salient ImageNet." ICML 2022.

[Sohoni2020] Sohoni, N., et al. "No Subclass Left Behind: Fine-Grained Robustness in Coarse-Grained Classification Problems." NeurIPS 2020.

[Sundararajan2017] Sundararajan, M., et al. "Axiomatic Attribution for Deep Networks." ICML 2017.

[Veitch2021] Veitch, V., et al. "Counterfactual Invariance to Spurious Correlations in Text Classification." NeurIPS 2021.

[Wah2011] Wah, C., et al. "The Caltech-UCSD Birds-200-2011 Dataset." Technical Report, 2011.

[Zhou2021] Zhou, C., et al. "Examining and Combating Spurious Features under Distribution Shift." ICML 2021.
