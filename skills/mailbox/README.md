# Mailbox Skill

リアルタイム通知システム - inotifywait を使用したファイルベースのメールボックス

## 概要

Agent 間の通知をファイルベースで実現します。

- **送信**: `inbox_write.sh` - メールボックスに通知を書く
- **受信**: `inbox_watcher.sh` - inotifywait で監視して即座に通知

## クイックスタート

### 1. 通知を送る

```bash
bash skills/mailbox/inbox_write.sh vibe "br を確認せよ！"
```

### 2. 監視を開始

```bash
bash skills/mailbox/inbox_watcher.sh vibe
```

## 設計

- **ファイルベース**: `.beads/mailbox/{target}.json`
- **リアルタイム**: inotifywait でファイル変更を即座に検知
- **tmux 統合**: 通知を tmux pane に表示
- **シンプル**: Shell スクリプトのみ、依存関係最小限

## 使用例

### 通常通知

```bash
# 簡易通知
bash skills/mailbox/inbox_write.sh vibe "Phase 2 実装完了！"

# 緊急通知
bash skills/mailbox/inbox_write.sh vibe "緊急：ブランチが壊れました！"
```

### 監視の開始

```bash
# 現在の tmux pane で監視
bash skills/mailbox/inbox_watcher.sh vibe

# 別ウィンドウで常駐
tmux new-window -n mailbox-vibe \
  "bash skills/mailbox/inbox_watcher.sh vibe"
```

## ファイル構造

```
.beeds/
└── mailbox/
    ├── vibe.json      # MistralVibe 宛の通知
    ├── qwen.json      # Qwen 宛の通知
    └── gemini.json    # Gemini 宛の通知
```

## 技術詳細

### inbox_write.sh

- JSON 形式で通知を保存
- タイムスタンプ自動付与
- 排他ロック（flock）

### inbox_watcher.sh

- inotifywait でファイル変更を検知
- tmux send-keys で通知を表示
- 自動でメールボックスをクリア

## トラブルシューティング

### inotifywait が見つからない

```bash
sudo apt install inotify-tools
```

### tmux pane で表示されない

```bash
# 現在の pane を確認
tmux display-message -p '#I:#P'

# 手動でメールボックスを確認
cat .beads/mailbox/vibe.json
```
