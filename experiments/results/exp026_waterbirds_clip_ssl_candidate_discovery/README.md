# exp026: Waterbirds 候補発見（CLIP / SSL）予定メモ

## 目的
Waterbirds 上で、表現ベースの候補発見法を前段に置き、PerformanceCheck への接続可能性を追加検証する。

## 予定している比較
- CLIP ベースの候補発見
- 自己教師あり表現ベースの候補発見
- 既存の簡易候補発見法との比較

## 見たいこと
- `background` を候補としてどれだけ安定して上位に回収できるか
- 候補発見の順位と PerformanceCheck の確認結果がどれだけ整合するか
- 候補の存在を示す指標と、性能上の必要性を示す指標がどのように役割分担するか

## メモ
- `exp025` の Waterbirds 候補発見 sweep を踏まえて設計する
- discovery 単体の優劣ではなく、`candidate discovery -> confirmation` の接続を主眼に置く
- 実装・config・結果が揃ったら `EXPERIMENT_MAP.md` に planned / 実行中として反映する
