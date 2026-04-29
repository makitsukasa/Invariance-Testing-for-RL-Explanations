# rl-shift-auto-detection

このリポジトリは、実験運用・査読対応・原稿更新を分離して管理します。  
特に `review.md`（最新レビュー本文）と `review_log.md`（履歴本体）を分ける運用を前提とします。

---

## PEER_REVIEW の実施手順

1. `tmp_peer_review_prompt.txt` を実行する  
2. 出力結果で `review.md` を上書きする（追記しない）

`review.md` は常に「最新1回分のみ」を保持します。

---

## ドキュメントの役割

- `vision.md`  
  最初に書いた大枠・目指すところ（更新しない）

- `review.md`  
  毎回の最新レビュー本文だけ（履歴を持たない）

- `review_log.md`  
  指摘 ID ごとに `方針 / 対応 / 証拠ファイル` を更新（履歴の本体）

- `EXPERIMENT_MAP.md`  
  実験の事実管理（ID, 状態, 実行時間, 論文章対応）

- `draft.md`  
  本文のみ更新（TODOは書かない）

---

## 更新タイミング（運用ルール）

### 1) 実験が必要と判明したとき
- `review_log.md` の既存項目に追記（必要なら新規IDを追加）
- `EXPERIMENT_MAP.md` に planned ID を追加

### 2) 実験を開始したとき
- `EXPERIMENT_MAP.md` の対象実験を `実行中` に更新

### 3) 実験が完了したとき
- `EXPERIMENT_MAP.md` の数値・状態・実行時間を更新
- `review_log.md` を `対応済` または `要追加実験` に更新
- `draft.md` の本文を更新

### 4) PEER_REVIEW 実施時
- `review.md` を差し替え
- `review_log.md` にレビュー内容を ID 分解して反映

### 5) draft 更新後
- `review_log.md` の該当指摘IDを `draft.md反映済`（または完了）に更新

---

## 運用上の注意

- 実験の事実（何を走らせ、何が出たか）は `EXPERIMENT_MAP.md` に集約する  
- レビュー指摘の履歴と意思決定は `review_log.md` に集約する  
- `draft.md` は論文本文専用とし、タスク管理情報を書かない  
- `review.md` は「最新レビューの置き場」であり、履歴用途に使わない

