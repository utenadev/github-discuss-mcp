# 参考資料・技術調査

github-discuss-mcp 開発に役立つ参考資料と技術調査メモ

---

## 📚 公式ドキュメント

### GitHub Discussions

- [GitHub Discussions クイックスタート](https://docs.github.com/ja/discussions/quickstart)
- [GitHub Discussions 概要](https://docs.github.com/ja/discussions)

**主な機能**:
- コミュニティフォーラム
- 会話の種類（Q&A、Announcements、Ideas 等）
- カテゴリ管理
- 分析情報
- モデレーション機能
- カテゴリフォーム（YAML 構文）

**ベストプラクティス**:
> ブレインストーミングや範囲明確化にディスカッションを使用し、
> 作業段階になったら課題（Issues）へ移行する

---

### GitHub API

#### REST API

- [Discussions API](https://docs.github.com/en/rest/discussions)
- [Activity API - Notifications](https://docs.github.com/en/rest/activity/notifications)

**主なエンドポイント**:
```
GET /repos/{owner}/{repo}/discussions
POST /repos/{owner}/{repo}/discussions
GET /notifications
GET /notifications/threads
```

#### GraphQL API

- [GitHub GraphQL API](https://docs.github.com/en/graphql)

**主なクエリ**:
```graphql
query GetDiscussions($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    discussions(first: 20) {
      nodes {
        id
        title
        body
        category { name }
      }
    }
  }
}
```

---

## 🔧 技術調査

### Mailbox 通知システム

**概要**: Agent 間協働のためのファイルベース通知システム

**実装**:
- `skills/mailbox-skill/inbox_write.py` - 通知送信
- `skills/mailbox-skill/inbox_watcher_polling.py` - 監視（5 秒 polling）

**仕組み**:
```
1. inbox_write.py がファイルに書き込み
2. inbox_watcher が 5 秒ごとにチェック
3. 変更を検知したら tmux に表示
4. 即座にファイルをクリア
```

**特徴**:
- ファイルベース（`.beads/mailbox/{target}.json`）
- 即座にクリア（セキュリティ・プライバシー）
- 詳細は br Issue に記載（永続化）

---

### 実装済み機能

| 機能 | 実装 | 備考 |
|-----|------|------|
| 新規投稿 | ✅ | `post_to_github_discuss` |
| 返信 | ✅ | `reply_to_discussion` |
| カテゴリ一覧 | ✅ | `get_discuss_categories` |
| 一覧表示 | ✅ | `get_discussions` |
| 詳細表示 | ✅ | `get_discussion_details` |
| 編集 | ✅ | `update_discussion` |
| 削除 | ✅ | `delete_discussion` |
| Q&A マーク | ✅ | `mark_answer` |
| Mailbox 通知 | ✅ | Agent 間通知 |

---

### 未実装機能（Phase 3）

| 機能 | 優先度 | 備考 |
|-----|--------|------|
| 検索機能 | 中 | キーワード、カテゴリフィルタ |
| メンション通知 | 中 | Activity API 連携 |
| 複数リポジトリ | 低 | 設定切り替え |
| 統計機能 | 低 | 投稿数、アクティブユーザー |
| Webhook 通知 | 低 | リアルタイム通知 |

---

## 📊 ドッグフーディングレポート

### MistralVibe（2026-04-18）

- **テスト数**: 5
- **成功率**: 100%
- **総合評価**: 9.6/10

**主な発見**:
- 返信機能は既に実装済み（#19 の要望は解決済み）
- 検索機能が不足
- メンション通知が不足

**レポート**: [docs/20260418_dogfooding_mistralvibe.md](20260418_dogfooding_mistralvibe.md)

### Qwen（2026-04-17）

- **目的**: github-discuss-mcp のドッグフーディング
- **結果**: Phase 1 完了、Phase 2 実装中

**レポート**: [docs/20260417_dogfooding_qwencode.md](20260417_dogfooding_qwencode.md)

---

## 🔗 関連リンク

- [github-discuss-mcp リポジトリ](https://github.com/utenadev/github-discuss-mcp)
- [beads_rust](https://github.com/Dicklesworthstone/beads_rust) - タスク管理
- [shogun (multi-agent-shogun)](https://github.com/yohey-w/multi-agent-shogun) - マルチエージェントシステム

---

**最終更新**: 2026-04-18
