# GitHub Discussions MCP/CLI 機能仕様書

**日付**: 2026-04-20  
**バージョン**: v0.1.0  
**プロジェクト**: github-discuss-mcp

---

## 🎯 プロジェクト概要

**github-discuss-mcp** は、GitHub Discussions に投稿する MCP サーバー/CLI ツールです。

**リポジトリ**: https://github.com/utenadev/github-discuss-mcp

---

## 📋 機能一覧

### Phase 1: 議論の質の向上 ✅

| 機能 | CLI | MCP | 状態 |
|-----|-----|-----|------|
| 返信機能 | `reply` | `reply_to_discussion` | ✅ |
| 階層構造詳細取得 | `show` | `get_discussion_details` | ✅ |

### Phase 2: コンテンツ管理と Q&A ✅

| 機能 | CLI | MCP | 状態 |
|-----|-----|-----|------|
| 新規投稿 | `post` | `post_to_github_discuss` | ✅ |
| 編集 | `update` | `update_discussion` | ✅ |
| 削除 | `delete` | `delete_discussion` | ✅ |
| Q&A 回答マーク | `mark-answer` | `mark_answer` | ✅ |

### Phase 2.5: 基本機能 ✅

| 機能 | CLI | MCP | 状態 |
|-----|-----|-----|------|
| カテゴリ一覧 | `categories` | `get_discuss_categories` | ✅ |
| 一覧表示 | `list` | `get_discussions` | ✅ |

### Phase 3: 探索と通知（一部）🔄

| 機能 | CLI | MCP | 状態 |
|-----|-----|-----|------|
| 検索機能 | `search` | (未実装) | ✅ v0.1.0 |
| メンション通知 | (未実装) | (未実装) | ⏳ 次回 |

---

## 📖 各機能の仕様

### 1. 新規投稿 (`post`)

**概要**: GitHub Discussions に新規投稿を作成

**コマンド**:
```bash
github-discuss post "タイトル" "本文" -c <category>
```

**オプション**:
| オプション | 必須 | 説明 |
|-----------|------|------|
| `タイトル` | ✅ | ディスカッションのタイトル |
| `本文` | ✅ | 投稿内容（Markdown 形式） |
| `--category`, `-c` | ❌ | カテゴリ（general, ideas, q-a, show-and-tell）デフォルト：general |
| `--dry-run`, `-n` | ❌ | ドライラン（送信せずにプレビュー） |
| `--owner`, `-o` | ❌ | GitHub オーナー名 |
| `--repo`, `-r` | ❌ | リポジトリ名 |

**MCP ツール**: `post_to_github_discuss`

**使用例**:
```bash
# 基本
github-discuss post "質問があります" "どうやって使いますか？" -c q-a

# ドライラン
github-discuss post "テスト" "本文" -n

# カテゴリ指定
github-discuss post "改善案" "こういう機能は？" -c ideas
```

---

### 2. 返信 (`reply`)

**概要**: 既存のディスカッションにコメント（返信）を追加

**コマンド**:
```bash
github-discuss reply <discussion_url> "コメント内容"
```

**MCP ツール**: `reply_to_discussion`

**使用例**:
```bash
github-discuss reply https://github.com/utenadev/github-discuss-mcp/discussions/15 "参考になりました！"
```

---

### 3. カテゴリ一覧 (`categories`)

**概要**: 利用可能なディスカッションカテゴリを一覧表示

**コマンド**:
```bash
github-discuss categories
```

**MCP ツール**: `get_discuss_categories`

**出力例**:
```
📋 カテゴリ一覧：

### General (DIC_xxx)
   説明：一般的なトピック

### Ideas (DIC_xxx)
   説明：機能提案

### Q&A (DIC_xxx)
   説明：質問と回答

### Show and tell (DIC_xxx)
   説明：成果物の共有
```

---

### 4. 一覧表示 (`list`)

**概要**: ディスカッションの一覧を表示

**コマンド**:
```bash
github-discuss list
```

**MCP ツール**: `get_discussions`

**出力例**:
```
📋 ディスカッション一覧：

### ログイン機能の実装について (#15)
   カテゴリ：General
   投稿者：user123
   日時：2026-04-19T12:00:00Z
   URL: https://github.com/.../discussions/15

### 認証周りのバグ報告 (#12)
   カテゴリ：Q&A
   投稿者：dev456
   日時：2026-04-18T10:30:00Z
   URL: https://github.com/.../discussions/12
```

---

### 5. 詳細表示 (`show`)

**概要**: ディスカッションの詳細（コメントの階層構造を含む）を表示

**コマンド**:
```bash
github-discuss show <discussion_url>
```

**MCP ツール**: `get_discussion_details`

**出力例**:
```
### ログイン機能の実装について (#15)
   URL: https://github.com/.../discussions/15
   カテゴリ：General
   投稿者：user123
   日時：2026-04-19T12:00:00Z

---

本文：
ログイン機能の実装について質問です。
OAuth2.0 を使用すべきでしょうか？

---

コメント (3 件):

┌ user456 • 2026-04-19T13:00:00Z
│ OAuth2.0 がおすすめです。
│ セキュリティの観点から安全です。
│
└─ user123 • 2026-04-19T14:00:00Z
   ありがとうございます！
   OAuth2.0 で実装してみます。

┌ dev789 • 2026-04-19T15:00:00Z
│ 参考資料：https://docs.github.com/...
```

---

### 6. 編集 (`update`)

**概要**: ディスカッションのタイトルまたは本文を編集

**コマンド**:
```bash
github-discuss update <discussion_url> --title "新しいタイトル" --body "新しい本文"
```

**MCP ツール**: `update_discussion`

**オプション**:
| オプション | 必須 | 説明 |
|-----------|------|------|
| `discussion_url` | ✅ | 編集するディスカッションの URL |
| `--title` | ❌ | 新しいタイトル |
| `--body` | ❌ | 新しい本文 |

**使用例**:
```bash
# タイトルのみ編集
github-discuss update https://.../discussions/15 --title "修正後のタイトル"

# 本文のみ編集
github-discuss update https://.../discussions/15 --body "修正後の本文"

# 両方編集
github-discuss update https://.../discussions/15 --title "タイトル" --body "本文"
```

---

### 7. 削除 (`delete`)

**概要**: ディスカッションを削除

**コマンド**:
```bash
github-discuss delete <discussion_url>
```

**MCP ツール**: `delete_discussion`

**使用例**:
```bash
github-discuss delete https://github.com/.../discussions/15
```

---

### 8. Q&A 回答マーク (`mark-answer`)

**概要**: コメントを回答としてマーク（Q&A 機能）

**コマンド**:
```bash
github-discuss mark-answer <comment_url>
```

**MCP ツール**: `mark_answer`

**使用例**:
```bash
github-discuss mark-answer https://github.com/.../discussions/15#discussioncomment-123
```

---

### 9. 検索機能 (`search`) - v0.1.0 新規

**概要**: ディスカッションをキーワードで検索

**コマンド**:
```bash
github-discuss search <キーワード>
```

**オプション**:
| オプション | 必須 | 説明 |
|-----------|------|------|
| `キーワード` | ✅ | 検索ワード（スペース区切りで複数可） |
| `--category`, `-c` | ⏳ | カテゴリ指定（v0.2.0 予定） |
| `--owner`, `-o` | ❌ | GitHub オーナー名 |
| `--repo`, `-r` | ❌ | リポジトリ名 |

**MCP ツール**: (未実装)

**出力例**:
```
📋 検索結果：5 件

### ログイン機能の実装について
   URL: https://github.com/.../discussions/15
   カテゴリ：General
   投稿者：user123
   日時：2026-04-19T12:00:00Z

### 認証周りのバグ報告
   URL: https://github.com/.../discussions/12
   カテゴリ：Q&A
   投稿者：dev456
   日時：2026-04-18T10:30:00Z
```

**制限事項**:
- 最大 30 件取得（GitHub API の制限）
- 検索対象：タイトル・本文（コメントは対象外）
- カテゴリフィルタ：v0.2.0 予定

---

## 🔧 MCP ツール一覧

| ツール名 | 説明 | 対応バージョン |
|---------|------|---------------|
| `post_to_github_discuss` | 新規投稿 | v0.1.0 |
| `reply_to_discussion` | 返信 | v0.1.0 |
| `get_discuss_categories` | カテゴリ一覧取得 | v0.1.0 |
| `get_discussions` | ディスカッション一覧取得 | v0.1.0 |
| `get_discussion_details` | ディスカッション詳細取得 | v0.1.0 |
| `update_discussion` | ディスカッション編集 | v0.1.0 |
| `delete_discussion` | ディスカッション削除 | v0.1.0 |
| `mark_answer` | 回答マーク | v0.1.0 |

---

## 🎯 使用例

### 基本的な使い方

```bash
# 1. カテゴリを確認
github-discuss categories

# 2. 新規投稿
github-discuss post "質問があります" "どうやって使いますか？" -c q-a

# 3. 一覧を確認
github-discuss list

# 4. 詳細を確認
github-discuss show https://github.com/.../discussions/1

# 5. 返信
github-discuss reply https://github.com/.../discussions/1 "参考になりました！"

# 6. 検索
github-discuss search "ログイン"
```

### Q&A フロー

```bash
# 1. 質問を投稿
github-discuss post "OAuth2.0 の実装方法は？" "教えてください" -c q-a

# 2. 返信がつく
# （他のユーザーが reply）

# 3. 回答をマーク
github-discuss mark-answer https://...#discussioncomment-123
```

---

## ⚠️ 制限事項

| 項目 | 制限 | 備考 |
|-----|------|------|
| **最大取得数** | 30 件 | 検索機能、GitHub API の制限 |
| **検索対象** | タイトル・本文 | コメントは対象外 |
| **カテゴリフィルタ** | 未実装 | v0.2.0 予定 |
| **ページネーション** | 未実装 | 31 件目以降は取得不可 |
| **ソート** | 関連度順 | 日付順は未実装 |

---

## 🗺️ 将来のリリース予定

### v0.1.0（今回リリース）✅

**テーマ**: 基本機能の完成

**実装機能**:
- 新規投稿、返信、編集、削除
- カテゴリ一覧、一覧表示、詳細表示
- Q&A 回答マーク
- **検索機能（キーワード検索のみ）**

---

### v0.2.0（次回予定）⏳

**テーマ**: 検索機能の強化

**実装予定機能**:
- **カテゴリフィルタ** - 特定カテゴリから検索
  ```bash
  github-discuss search "ログイン" --category q-a
  ```

**検索範囲**: 特定カテゴリに絞り込み

---

### v0.3.0（将来予定）🔮

**テーマ**: 検索範囲の拡張

**実装予定機能**:
- **特定スレッド内検索** - 特定ディスカッション内のコメントを検索
  ```bash
  github-discuss search "ログイン" --discussion 15
  ```
- **コメント検索** - コメントも検索対象に含める

**検索範囲**: 特定スレッド内のコメント

---

### v0.4.0（将来予定）🔮

**テーマ**: 高度なフィルタリング

**実装予定機能**:
- **投稿者フィルタ** - 特定ユーザーの投稿のみ検索
  ```bash
  github-discuss search "提案" --author user123
  ```
- **日付範囲フィルタ** - 特定期間の投稿のみ検索
  ```bash
  github-discuss search "報告" --since 2026-04-01 --until 2026-04-30
  ```
- **ソート機能** - 作成日順、更新日順など
  ```bash
  github-discuss search "バグ" --sort created --order desc
  ```

**検索範囲**: 複数条件で精密に絞り込み

---

## 📊 検索機能ロードマップ

| バージョン | 検索範囲 | フィルタ | 検索対象 |
|-----------|---------|---------|---------|
| **v0.1.0** | リポジトリ全体 | なし | タイトル・本文 |
| **v0.2.0** | 特定カテゴリ | カテゴリ | タイトル・本文 |
| **v0.3.0** | 特定スレッド内 | ディスカッション ID | コメント含む |
| **v0.4.0** | 複数条件 | カテゴリ + 投稿者 + 日付 + ソート | コメント含む |

---

## 📚 参考資料

- [GitHub Discussions API](https://docs.github.com/en/graphql/guides/using-the-graphql-api-for-discussions)
- [GitHub Search Documentation](https://docs.github.com/en/search-github/searching-on-github/searching-discussions)
- [MCP Specification](https://modelcontextprotocol.io/)

