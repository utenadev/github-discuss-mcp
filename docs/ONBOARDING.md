# GitHub Discussions MCP - Onboarding Guide

## 📚 新規エージェント用ガイド

このプロジェクトでの **br** と **Mailbox** の使い方を説明します。

---

## 🎯 概要

**github-discuss-mcp**: GitHub Discussions に投稿する MCP サーバー/CLI ツール

**リポジトリ**: https://github.com/utenadev/github-discuss-mcp

---

## 📬 1. Mailbox 通知システム

### 概要

エージェント間の**リアルタイム通知システム**です。

- **tmux 統合**: 通知を tmux 入力欄に自動表示
- **5 秒 polling**: ファイル変更を定期的にチェック
- **自動クリア**: 読んだ通知を自動削除

---

### 使い方

#### 通知を送る

```bash
./skills/mailbox-skill/inbox_write.py <target> "<メッセージ>"
```

**例**:
```bash
# Qwen から Gemini へ
./skills/mailbox-skill/inbox_write.py gemini "br を確認してください！"

# Qwen から MistralVibe へ
./skills/mailbox-skill/inbox_write.py vibe "タスクを追加しました"
```

---

#### 監視を開始する

```bash
./skills/mailbox-skill/inbox_watcher_polling.py <target> <window.pane>
```

**例**:
```bash
# Gemini (Window 2, Pane 1)
./skills/mailbox-skill/inbox_watcher_polling.py gemini 2.1

# MistralVibe (Window 3, Pane 1)
./skills/mailbox-skill/inbox_watcher_polling.py vibe 3.1

# Qwen (Window 1, Pane 1)
./skills/mailbox-skill/inbox_watcher_polling.py qwen 1.1
```

---

#### tmux 構成

| エージェント | ウィンドウ | コマンド |
|-------------|-----------|---------|
| **Qwen** | 1.1 | `./skills/mailbox-skill/inbox_watcher_polling.py qwen 1.1` |
| **Gemini** | 2.1 | `./skills/mailbox-skill/inbox_watcher_polling.py gemini 2.1` |
| **MistralVibe** | 3.1 | `./skills/mailbox-skill/inbox_watcher_polling.py vibe 3.1` |

---

### 通知の流れ

```
1. inbox_write.py がファイルに書き込み
   ↓
2. inbox_watcher_polling.py が 5 秒ごとにチェック
   ↓
3. 変更を検知したら tmux に入力
   ↓
4. Agent が通知を見て反応
   ↓
5. **Agent は br Issue を確認**（詳細は br に記載）
```

**⚠️ 重要**: Mailbox 通知は即座にクリアされます（5 秒以内）。詳細は必ず br Issue で確認してください。

---

### 画面表示

通知が届くと、tmux 画面に以下と表示されます：

```
# 📬 メールボックスに通知があります (gemini)
# 📬 cat /home/kench/workspace/github-discuss-mcp/.beads/mailbox/gemini.json
```

---

### 注意点

**⚠️ 重要：Mailbox 監視スクリプトの起動はユーザーの役割です！**

Coding Agent はスクリプトを起動できません。ユーザーが tmux で事前に起動しておく必要があります。

**起動コマンド**（ユーザーが実行）:
```bash
# 各ウィンドウで実行
./skills/mailbox-skill/inbox_watcher_polling.py qwen 1.1
./skills/mailbox-skill/inbox_watcher_polling.py gemini 2.1
./skills/mailbox-skill/inbox_watcher_polling.py vibe 3.1
```

**起動確認**（Agent が実行）:
```bash
ps aux | grep inbox_watcher_polling
```

**技術的な注意点**:
1. **bash を使わない**:
   - ❌ `bash skills/mailbox-skill/inbox_watcher_polling.py gemini`
   - ✅ `./skills/mailbox-skill/inbox_watcher_polling.py gemini`

2. **cd で移動**:
   - プロジェクトルートに移動してから実行

3. **`.` から始める**:
   - `./` で現在のディレクトリから実行

---

## 📋 2. br (beads_rust)

### 概要

**タスク管理システム**です。

- **Issue ベース**: 各タスクを Issue で管理
- **優先度**: P1（高）〜 P3（低）
- **担当者**: [qwen], [gemini], [vibe] で区別

---

### 主要コマンド

#### タスク一覧を確認

```bash
br ready
```

**出力例**:
```
📋 Ready work (12 issues with no blockers):

1. [● P1] [task] bd-2gn: [全員] 日報・連絡：チームコミュニケーション用
2. [● P2] [task] bd-1px: [gemini] Mailbox スキル説明
3. [● P2] [task] bd-3og: [vibe] Mailbox スキル説明
...
```

---

#### Issue を確認

```bash
br show <issue-id>
```

**例**:
```bash
br show bd-2gn  # 通信用 Issue
br show bd-1px  # Gemini 用タスク
br show bd-3og  # MistralVibe 用タスク
```

---

#### コメントを追加

```bash
br comments add <issue-id> "<コメント>"
```

**例**:
```bash
br comments add bd-2gn "✅ 起動完了"
br comments add bd-1px "📋 確認しました"
```

---

### Issue 一覧

| Issue ID | 用途 | 担当者 |
|----------|------|--------|
| **bd-2gn** | 通信用（日報・連絡） | 全員 |
| **bd-1px** | Mailbox スキル説明 | Gemini |
| **bd-3og** | Mailbox スキル説明 | MistralVibe |

---

## 🔄 3. br と Mailbox の連携

### 基本的なフロー

```
1. br Issue で詳細を説明
   ↓
2. Mailbox で「br を見て！」と通知
   ↓
3. 相手が Mailbox 通知を確認
   ↓
4. br Issue を読んで返信
```

---

### 使用例

#### 例 1: タスクを振る

```bash
# 1. br Issue に詳細を記載
br comments add bd-1px "## タスク：コードレビュー..."

# 2. Mailbox で通知
./skills/mailbox-skill/inbox_write.py gemini "bd-1px にタスクを追加しました"
```

#### 例 2: 進捗を報告

```bash
# 1. br Issue に報告
br comments add bd-2gn "## 進捗報告..."

# 2. Mailbox で通知（必要に応じて）
./skills/mailbox-skill/inbox_write.py vibe "bd-2gn に進捗を報告しました"
```

---

## 📊 4. プロジェクト構造

```
github-discuss-mcp/
├── src/github_discuss_mcp/    # 主要ソースコード
│   ├── cli.py                 # CLI コマンド
│   ├── github_api.py          # GitHub API
│   └── main.py                # MCP サーバー
├── skills/mailbox-skill/            # Mailbox システム
│   ├── inbox_write.py         # 通知送信
│   ├── inbox_watcher_polling.py # 監視
│   └── README.md              # ドキュメント
├── tests/                     # テストコード
├── docs/                      # ドキュメント
├── .beads/                    # br データ
│   └── mailbox/               # Mailbox データ
└── .vibe/                     # 設定（git 対象外）
```

---

## 🎯 5. 最初のステップ

### 新規エージェント用チェックリスト

1. [ ] **br のチュートリアルを完了**
   ```bash
   br --help
   ```

2. [ ] **Mailbox 監視スクリプトの起動状況を確認**
   ```bash
   ps aux | grep inbox_watcher_polling
   ```
   
   **注意**: 起動していない場合は、ユーザーに依頼してください。Coding Agent はスクリプトを起動できません。

3. [ ] **bd-2gn を確認**（通信用 Issue）
   ```bash
   br show bd-2gn
   ```

4. [ ] **各自的な Issue を確認**
   - Gemini: `br show bd-1px`
   - MistralVibe: `br show bd-3og`

5. [ ] **Mailbox テスト**
   ```bash
   # 自分宛にテスト通知
   ./skills/mailbox-skill/inbox_write.py <target> "🧪 テスト"
   ```

---

## 🔗 6. 参考資料

### ドキュメント

- `docs/20260417_dogfooding_qwencode.md` - Qwen のドッグフーディングレポート
- `docs/20260418_gemini_discussions_research_report_ja.md` - Gemini 調査レポート

### コミット履歴

```bash
git log --oneline main | head -20
```

### 主要コミット

- `7555bb8` feat: Mailbox 通知システムの実装
- `ee70f70` feat: Phase 2 完了 - CLI・MCP ツール実装
- `a0c0e3d` feat: Phase 2 実装 - コンテンツ管理と Q&A 機能

---

## ❓ 7. よくある質問

### Q: Mailbox 通知が届かない

**A**: 監視スクリプトが起動しているか確認：
```bash
ps aux | grep inbox_watcher_polling
```

### Q: br でエラーが出る

**A**: br のインストールを確認：
```bash
which br
```

### Q: tmux の pane が分からない

**A**: 現在の pane を確認：
```bash
tmux display-message -p '#I:#P'
```

---

## 📞 8. サポート

何か問題があれば、**bd-2gn**（通信用 Issue）にコメントしてください。

```bash
br comments add bd-2gn "❌ 質問：..."
```

---

**ようこそ！github-discuss-mcp プロジェクトへ！** 🚀
