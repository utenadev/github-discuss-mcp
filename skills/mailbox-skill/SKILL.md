# Mailbox Skill

エージェント間のリアルタイム通知システム

## 概要

このスキルは、複数の AI エージェント間でリアルタイムに通知をやり取りするための仕組みを提供します。

- **tmux 統合**: 通知を tmux 入力欄に自動表示
- **5 秒 polling**: ファイル変更を定期的にチェック
- **自動クリア**: 読んだ通知を自動削除

## ファイル構成

```
mailbox-skill/
├── SKILL.md                      # このファイル
├── README.md                     # 詳しい使い方
├── inbox_write.py                # 通知送信スクリプト
├── inbox_watcher_polling.py      # 監視スクリプト（polling 版）
├── inbox_watcher.py              # 監視スクリプト（inotifywait 版）
├── inbox_watcher.sh              # 監視スクリプト（Bash 版）
└── inbox_write.sh                # 通知送信スクリプト（Bash 版）
```

## コマンド

### 通知を送る

```bash
./skills/mailbox-skill/inbox_write.py <target> "<メッセージ>"
```

**例**:
```bash
./skills/mailbox-skill/inbox_write.py gemini "br を確認してください！"
./skills/mailbox-skill/inbox_write.py vibe "タスクを追加しました"
```

### 監視を開始する

```bash
./skills/mailbox-skill/inbox_watcher_polling.py <target> <window.pane>
```

**例**:
```bash
./skills/mailbox-skill/inbox_watcher_polling.py gemini 2.1
./skills/mailbox-skill/inbox_watcher_polling.py vibe 3.1
```

## 対応エージェント

| エージェント | ウィンドウ | コマンド |
|-------------|-----------|---------|
| Qwen | 1.1 | `./skills/mailbox-skill/inbox_watcher_polling.py qwen 1.1` |
| Gemini | 2.1 | `./skills/mailbox-skill/inbox_watcher_polling.py gemini 2.1` |
| MistralVibe | 3.1 | `./skills/mailbox-skill/inbox_watcher_polling.py vibe 3.1` |

## 注意点

1. **bash を使わない**: `./script.py` で直接実行
2. **cd で移動**: プロジェクトルートに移動してから実行
3. **`.` から始める**: `./` で現在のディレクトリから実行

## 関連ドキュメント

- `docs/ONBOARDING.md` - 新規エージェント用ガイド
- `skills/mailbox-skill/README.md` - 詳しい使い方
