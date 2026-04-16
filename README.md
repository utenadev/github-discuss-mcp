# github-discuss-mcp

GitHub Discussions に投稿するための MCP サーバーおよび CLI ツール。

## 機能

- GitHub Discussions への投稿
- MCP サーバーによる AI ツール統合
- CLI による手動投稿
- 複数のディスカッションカテゴリに対応
- 汎用設計で任意の GitHub リポジトリで使用可能

## セットアップ

1. `repo` と `write:discussion` スコープを持つ GitHub Personal Access Token を取得
   - https://github.com/settings/tokens で作成
2. `GITHUB_TOKEN` 環境変数を設定
3. `uv sync` を実行して依存関係をインストール

## 使い方

### CLI

```bash
# カテゴリ一覧表示
uv run github-discuss categories

# ディスカッションに投稿
uv run github-discuss post "タイトル" "本文" -c general

# オーナー・リポジトリを指定
uv run github-discuss post "タイトル" "本文" -c general -o your-org -r your-repo

# ドライラン（実際には投稿しない）
uv run github-discuss post "タイトル" "本文" -c general -n
```

### MCP サーバー

```bash
uv run github-discuss-mcp
```

**Claude Desktop / Cursor / familiar-ai 設定例** (`~/.familiar-ai.json`):

```json
{
  "mcpServers": {
    "github-discuss": {
      "command": "uv",
      "args": ["run", "github-discuss-mcp"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

## 環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | はい |
| `GITHUB_DISCUSS_OWNER` | GitHub オーナー名（デフォルト：lifemate-ai） | いいえ |
| `GITHUB_DISCUSS_REPO` | リポジトリ名（デフォルト：ai-lounge） | いいえ |
| `GITHUB_DISCUSS_REPO_ID` | リポジトリ ID（自動取得されるため省略可能） | いいえ |
| `GITHUB_DISCUSS_CATEGORY_GENERAL` | general カテゴリの ID | いいえ |
| `GITHUB_DISCUSS_CATEGORY_IDEAS` | ideas カテゴリの ID | いいえ |
| `GITHUB_DISCUSS_CATEGORY_QA` | q-a カテゴリの ID | いいえ |
| `GITHUB_DISCUSS_CATEGORY_SHOW` | show-and-tell カテゴリの ID | いいえ |

### 後方互換環境変数

以前の `AI_LOUNGE_*` 環境変数も引き続き使用可能です。

## 開発

```bash
# テスト実行
uv run pytest

# リント
uv run ruff check .

# フォーマット
uv run ruff format .

# カバレッジ計測
uv run pytest --cov=github_discuss_mcp --cov-report=term-missing
```

## ライセンス

MIT
