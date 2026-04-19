# Mailbox システム仕様書

**バージョン**: 2.0  
**作成日**: 2026-04-19  
**最終更新**: 2026-04-19

---

## 📋 概要

github-discuss-mcp プロジェクトにおける、エージェント間の非同期通信システムです。

tmux 上で動作する各エージェント（Qwen, Gemini, MistralVibe）が、メールボックスを介してメッセージを送受信します。

---

## 🏗️ アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                    tmux セッション                       │
│                                                         │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐ │
│  │    Qwen       │  │    Gemini     │  │    Vibe     │ │
│  │   (Pane 1.1)  │  │   (Pane 2.1)  │  │  (Pane 3.1) │ │
│  │               │  │               │  │             │ │
│  │ inbox_write   │  │mailbox_receiver│mailbox_receiver││
│  │   (送信)      │  │   (受信)      │  │   (受信)    │ │
│  └───────────────┘  └───────────────┘  └─────────────┘ │
│                                                         │
│  ┌─────────────────────────────────────────────────────┐│
│  │              設定ファイル                            ││
│  │         ~/.config/mailbox/config.json               ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

---

## 📁 ファイル構成

```
~/.config/mailbox/
└── config.json              # 設定ファイル

~/.beads/mailbox/
├── qwen.json                # Qwen 宛メールボックス
├── gemini.json              # Gemini 宛メールボックス
└── vibe.json                # MistralVibe 宛メールボックス

skills/mailbox-skill/
├── inbox_write.py           # 送信スクリプト
├── mailbox_receiver.py      # 受信プロセス
└── README.md                # 使い方
```

---

## ⚙️ 設定ファイル

### 場所

```
~/.config/mailbox/config.json
```

### 形式

```json
{
  "agents": [
    {"name": "qwen", "pane": "1.1"},
    {"name": "gemini", "pane": "2.1"},
    {"name": "vibe", "pane": "3.1"}
  ],
  "auto_update": true,
  "polling_interval": 5,
  "created_at": "2026-04-19T10:00:00",
  "updated_at": "2026-04-19T10:00:00"
}
```

### フィールド説明

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `agents` | array | エージェント一覧 |
| `agents[].name` | string | エージェント名（qwen, gemini, vibe） |
| `agents[].pane` | string | tmux pane ID（例：`1.1`） |
| `auto_update` | boolean | 自動更新の有効/無効 |
| `polling_interval` | number | ポーリング間隔（秒） |
| `created_at` | string | 作成日時（ISO 8601） |
| `updated_at` | string | 更新日時（ISO 8601） |

---

## 📤 送信機能

### 使い方

```bash
python inbox_write.py --from <sender> --to <receiver> "<message>"
```

### 例

```bash
# Qwen から Gemini へ
python inbox_write.py --from qwen --to gemini "bd-1yb に報告をお願いします"

# Gemini から Qwen へ
python inbox_write.py --from gemini --to qwen "受信処理完了"
```

### メールボックスファイル形式

```json
{
  "messages": [
    {
      "id": "msg_20260419_100000_12345",
      "from": "qwen",
      "to": "gemini",
      "timestamp": "2026-04-19T10:00:00",
      "message": "bd-1yb に報告をお願いします",
      "type": "normal",
      "read": false
    }
  ]
}
```

### メッセージタイプ

| タイプ | 説明 | 返信要否 |
|-------|------|---------|
| `normal` | 通常メッセージ | 要 |
| `receipt_confirmation` | 受信処理完了 | 不要 |

---

## 📥 受信機能

### 起動方法

```bash
# 初回設定
python mailbox_receiver.py --setup

# 受信プロセス起動
python mailbox_receiver.py --agent <agent_name>
```

### 例

```bash
# 初回設定（自動でエージェント検出）
python mailbox_receiver.py --setup

# Gemini の受信プロセスを起動
python mailbox_receiver.py --agent gemini
```

### 標準出力

```
📬 qwen からのメッセージ (2026-04-19T10:00:00):
   bd-1yb に最終報告をお願いします

✅ gemini が受信処理を完了しました
```

---

## 🔄 通信フロー

### 基本フロー

```
1. 送信者が inbox_write.py を実行
   ↓
2. メールボックスファイルに保存
   ↓
3. 受信者の mailbox_receiver が polling（5 秒ごと）
   ↓
4. 新着メッセージを検知
   ↓
5. 標準出力に表示
   ↓
6. 受信者が確認・返信
   ↓
7. 返信を inbox_write.py で送信
   ↓
8. 【完了】
```

### 受信処理完了のフロー

```
1. 受信者がメッセージを読む
   ↓
2. 受信処理完了メッセージを送信
   python inbox_write.py --from gemini --to qwen "受信処理完了"
   ↓
3. 送信者の mailbox_receiver が表示
   ✅ gemini が受信処理を完了しました
   ↓
4. 【完了】（返信しない）
```

---

## 🛠️ コマンドリファレンス

### inbox_write.py

```
Usage: python inbox_write.py --from <sender> --to <receiver> "<message>"

Options:
  --from    送信者名（必須）
  --to      受信者名（必須）
  --help    ヘルプを表示
```

### mailbox_receiver.py

```
Usage: python mailbox_receiver.py [OPTIONS]

Options:
  --setup         初回設定
  --agent <name>  エージェント名
  --list-agents   検出されたエージェントを表示
  --help          ヘルプを表示
```

---

## 🔧 設定管理

### 初回設定（--setup）

1. 設定ディレクトリを作成（`~/.config/mailbox/`）
2. tmux pane を自動検出
3. エージェント名をマッピング
4. 設定ファイルを作成

### 自動更新

`auto_update: true` の場合：
- 起動時に tmux pane を再検出
- 変更があれば設定を更新

### 手動追加

存在しないエージェントを指定した場合：
1. 利用可能な pane を一覧表示
2. ユーザーが選択
3. 設定ファイルに追加

---

## 📊 エージェント検出

### tmux コマンド

```bash
tmux list-panes -F "#I:#P #{pane_current_command}"
```

### 出力例

```
1.1 python3 (Qwen)
2.1 python3 (Gemini)
3.1 python3 (Vibe)
```

### キーワードマッピング

| エージェント | 検出キーワード |
|-------------|---------------|
| qwen | qwen, Qwen |
| gemini | gemini, Gemini |
| vibe | vibe, Vibe, mistral |

---

## 🔒 セキュリティ

### ファイルロック

メールボックスファイルの読み書きは、排他ロックを使用：

```python
with open(lockfile, 'w') as lock:
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
    # 読み書き処理
    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
```

### パーミッション

- 設定ファイル：`600`（所有者のみ読み書き可能）
- メールボックスファイル：`600`

---

## 🐛 トラブルシューティング

### 設定ファイルが見つからない

```
❌ 設定ファイルが見つかりません：~/.config/mailbox/config.json
```

**解決**: 先に `--setup` を実行してください

```bash
python mailbox_receiver.py --setup
```

### エージェントが検出されない

```
⚠️ エージェントが検出されませんでした
```

**解決**: tmux でエージェントを起動後、再度 `--setup` を実行

### メールボックスファイルが空

```
📬 未読メッセージはありません
```

**正常**: 未読メッセージがない状態です

---

## 📝 使用例

### シナリオ 1: Qwen から Gemini へ指示

```bash
# Qwen のターミナル
python inbox_write.py --from qwen --to gemini "bd-1yb に最終報告をお願いします"

# Gemini のターミナル（mailbox_receiver が表示）
📬 qwen からのメッセージ (2026-04-19T10:00:00):
   bd-1yb に最終報告をお願いします

# Gemini が報告後
python inbox_write.py --from gemini --to qwen "受信処理完了"

# Qwen のターミナル
✅ gemini が受信処理を完了しました
```

### シナリオ 2: 複数エージェントへの通知

```bash
# Qwen から全員へ
python inbox_write.py --from qwen --to gemini "明日 10 時に会議"
python inbox_write.py --from qwen --to vibe "明日 10 時に会議"
```

---

## 📚 関連ドキュメント

- [ONBOARDING.md](ONBOARDING.md) - 新規エージェント用ガイド
- [references.md](references.md) - 参考資料・技術調査

---

**おわり**
