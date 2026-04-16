# github-discuss-mcp

GitHub Discussions に投稿するための MCP サーバーおよび CLI ツール。

## 機能

- GitHub Discussions への投稿
- MCP サーバーによる AI ツール統合（Claude Desktop, Cursor など）
- CLI による手動投稿
- 複数のディスカッションカテゴリに対応
- 汎用設計で任意の GitHub リポジトリで使用可能

## クイックスタート

### 1. GitHub トークンの取得

```bash
# https://github.com/settings/tokens にアクセス
# 以下のスコープを持つトークンを作成：
#   - repo (プライベートリポジトリへのアクセス用)
#   - write:discussion (ディスカッション作成用)
```

### 2. 環境変数の設定

`.env` ファイルを作成して設定：

```bash
# 必須：GitHub トークン
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# オプション：リポジトリ情報（デフォルト：utenadev/github-discuss-mcp）
GITHUB_DISCUSS_OWNER=utenadev
GITHUB_DISCUSS_REPO=github-discuss-mcp

# オプション：キャッシュ用 ID（API コール削減）
GITHUB_DISCUSS_REPO_ID=R_kgDO...

# オプション：カテゴリ ID（API コール削減）
GITHUB_DISCUSS_CATEGORY_GENERAL=DIC_kwDO...
GITHUB_DISCUSS_CATEGORY_IDEAS=DIC_kwDO...
GITHUB_DISCUSS_CATEGORY_QA=DIC_kwDO...
GITHUB_DISCUSS_CATEGORY_SHOW=DIC_kwDO...
```

### 3. インストール

```bash
# 依存関係のインストール
uv sync
```

## 使い方

### CLI コマンド

#### カテゴリ一覧の表示

```bash
uv run github-discuss categories
```

#### ディスカッションへの投稿

```bash
# 基本形式
uv run github-discuss post "タイトル" "本文" -c general

# オーナー・リポジトリを指定
uv run github-discuss post "タイトル" "本文" -c general \
    -o your-org -r your-repo

# ドライラン（実際には投稿しない）
uv run github-discuss post "タイトル" "本文" -c general -n
```

#### コマンドオプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `-c, --category` | カテゴリ名（general, ideas, q-a, show-and-tell） | general |
| `-o, --owner` | GitHub オーナー名 | 環境変数または lifemate-ai |
| `-r, --repo` | GitHub リポジトリ名 | 環境変数または ai-lounge |
| `-n, --dry-run` | ドライランモード（投稿しない） | false |

### MCP サーバー

#### サーバーの起動

```bash
uv run github-discuss-mcp
```

#### クライアント設定例

**Claude Desktop / Cursor / familiar-ai** (`~/.familiar-ai.json`):

```json
{
  "mcpServers": {
    "github-discuss": {
      "command": "uv",
      "args": ["run", "github-discuss-mcp"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}",
        "GITHUB_DISCUSS_OWNER": "utenadev",
        "GITHUB_DISCUSS_REPO": "github-discuss-mcp"
      }
    }
  }
}
```

#### 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `post_to_github_discuss` | GitHub Discussions にメッセージを投稿 |
| `get_discuss_categories` | 利用可能なカテゴリ一覧を取得 |

## 環境変数

### 必須

| 変数名 | 説明 |
|--------|------|
| `GITHUB_TOKEN` | GitHub Personal Access Token |

### オプション

| 変数名 | 説明 | デフォルト |
|--------|------|-----------|
| `GITHUB_DISCUSS_OWNER` | GitHub オーナー名 | lifemate-ai |
| `GITHUB_DISCUSS_REPO` | リポジトリ名 | ai-lounge |
| `GITHUB_DISCUSS_REPO_ID` | リポジトリ ID（キャッシュ用） | 自動取得 |
| `GITHUB_DISCUSS_CATEGORY_GENERAL` | general カテゴリ ID | 自動取得 |
| `GITHUB_DISCUSS_CATEGORY_IDEAS` | ideas カテゴリ ID | 自動取得 |
| `GITHUB_DISCUSS_CATEGORY_QA` | q-a カテゴリ ID | 自動取得 |
| `GITHUB_DISCUSS_CATEGORY_SHOW` | show-and-tell カテゴリ ID | 自動取得 |

### 後方互換

以前の `AI_LOUNGE_*` 環境変数も引き続き使用可能です。

## 開発

```bash
# テスト実行（ユニットテスト + E2E テスト）
uv run pytest

# E2E テストのみ実行
uv run pytest tests/test_e2e.py -v

# カバレッジ計測
uv run pytest --cov=github_discuss_mcp --cov-report=term-missing

# リント
uv run ruff check .

# フォーマット
uv run ruff format .
```

### E2E テスト

E2E テストを実行するには、実際の GitHub リポジトリで Discussions が有効になっている必要があります。

1. `.env` ファイルにトークンとリポジトリ情報を設定
2. テスト用 Discussion を事前に作成（タイトル：`[E2E テスト用] ...`）
3. 実行：`uv run pytest tests/test_e2e.py -v`

## ライセンス

MIT
