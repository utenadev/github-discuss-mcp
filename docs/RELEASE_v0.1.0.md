# Release Notes: v0.1.0

**リリース日**: 2026-04-20  
**バージョン**: v0.1.0  
**タグ**: `v0.1.0`

---

## 🎉 概要

**github-discuss-mcp v0.1.0** は、GitHub Discussions の基本的な操作を CLI と MCP サーバーから行えるようになる最初のリリースです。

---

## ✨ 新機能

### CLI 機能

| コマンド | 説明 |
|---------|------|
| `post` | 新規ディスカッションを投稿 |
| `reply` | 既存ディスカッションに返信 |
| `categories` | カテゴリ一覧を表示 |
| `list` | ディスカッション一覧を表示 |
| `show` | ディスカッション詳細を表示（コメント階層付き） |
| `update` | ディスカッションを編集 |
| `delete` | ディスカッションを削除 |
| `mark-answer` | コメントを回答としてマーク（Q&A 機能） |
| `search` | ディスカッションを検索（🆕 v0.1.0） |

### MCP ツール

| ツール | 説明 |
|-------|------|
| `post_to_github_discuss` | 投稿 |
| `reply_to_discussion` | 返信 |
| `get_discuss_categories` | カテゴリ一覧取得 |
| `get_discussions` | ディスカッション一覧取得 |
| `get_discussion_details` | 詳細取得 |
| `update_discussion` | 編集 |
| `delete_discussion` | 削除 |
| `mark_answer` | 回答マーク |
| `search_discussions` | 検索（🆕 v0.1.0） |

---

## 🔧 改善

### コードレビュー指摘の修正（v0.1.0）

**MistralVibe によるコードレビュー**（評価：9.8/10）からの改善：

1. **カテゴリ名の柔軟なマッチング**
   - `q-a`, `Q&A`, `qa`, `Question` すべて `q-a` として認識
   - 大文字小文字を区別しない

2. **エラーメッセージの表示改善**
   - 成功時：エラーメッセージを表示しない
   - 失敗時：詳細なエラーを表示

---

## 📊 テスト結果

**シナリオテスト**: 5/5 合格 (100%)

| テストケース | 結果 |
|-------------|------|
| TC-001: 基本機能テスト | ✅ 合格 |
| TC-002: MCP サーバー機能テスト | ✅ 合格 |
| TC-003: カテゴリ名正規化 | ✅ 合格 (4/4) |
| TC-004: エラーメッセージ表示 | ✅ 合格 |
| TC-005: 検索機能 | ✅ 合格 |

**詳細**: [20260420_scenario_test_report.md](docs/20260420_scenario_test_report.md)

---

## 🗺️ 今後のロードマップ

### v0.2.0（次回予定）

**テーマ**: 検索機能の強化

- カテゴリフィルタ
  ```bash
  github-discuss search "ログイン" --category q-a
  ```

### v0.3.0（将来予定）

**テーマ**: 検索範囲の拡張

- 特定スレッド内検索
- コメント検索

### v0.4.0（将来予定）

**テーマ**: 高度なフィルタリング

- 投稿者フィルタ
- 日付範囲フィルタ
- ソート機能

**詳細**: [github_discuss_mcp_feature_spec.md](docs/github_discuss_mcp_feature_spec.md)

---

## 📦 インストール

```bash
# リポジトリをクローン
git clone https://github.com/utenadev/github-discuss-mcp.git
cd github-discuss-mcp

# 依存関係をインストール
uv sync

# インストールスクリプトを実行
bash install.sh

# 環境変数を設定
export GITHUB_TOKEN=ghp_xxx

# 使用方法
github-discuss --help
```

---

## 🔗 関連ドキュメント

- [機能仕様書](docs/github_discuss_mcp_feature_spec.md)
- [シナリオテストレポート](docs/20260420_scenario_test_report.md)
- [コードレビューレポート](docs/20260420_code_review_report.md)

---

## 🙏 謝辞

**MistralVibe (devstral-2)** - コードレビュー、テスト実施

**Gemini** - 初期機能の調査・実装サポート

---

## 📝 変更履歴

### v0.1.0 (2026-04-20)

- 初期リリース
- 基本機能の実装（投稿、返信、編集、削除、一覧、詳細、Q&A マーク）
- 検索機能の実装（キーワード検索）
- カテゴリ名正規化機能
- エラーメッセージ表示の改善
- MCP サーバーの実装

---

**Happy Discussing! 🎉**
