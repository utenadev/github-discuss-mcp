# github-discuss

GitHub Discussions に投稿するための MCP サーバーおよび CLI ツール。

## 機能

- ✅ GitHub Discussions への投稿・返信・編集・削除
- ✅ MCP サーバーによる AI ツール統合（Claude Desktop, Cursor など）
- ✅ CLI による手動投稿
- ✅ 検索機能（キーワード検索）
- ✅ GitHub App 認証（本番運用）と Personal Access Token（開発）
- ✅ 複数のディスカッションカテゴリに対応
- ✅ 汎用設計で任意の GitHub リポジトリで使用可能

## クイックスタート

### 1. 認証情報の設定

#### オプション A: GitHub App 認証（推奨・本番運用）

```bash
# GitHub App "utena.qwen" (App ID: 3442413) を使用

# 1. GitHub App を作成
# https://github.com/settings/apps/new
# - App name: utena.qwen
# - Permissions: Discussions → Read & write
# - Where can this GitHub App be installed?: Any account

# 2. Private Key をダウンロード
# "Generate a private key" をクリック

# 3. Installation
# https://github.com/settings/installations からインストール
# Installation ID を控える

# 4. 環境変数を設定
GITHUB_APP_ID=3442413
GITHUB_APP_PRIVATE_KEY=/home/kench/.github/utena-qwen-private-key.pem
GITHUB_APP_INSTALLATION_ID=xxxxxxxxx
```

#### オプション B: Personal Access Token（開発・テスト）

```bash
# https://github.com/settings/tokens にアクセス
# 以下のスコープを持つトークンを作成：
#   - repo (プライベートリポジトリへのアクセス用)
#   - write:discussion (ディスカッション作成用)

GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

**認証方式の自動切り替え**:
- `GITHUB_APP_PRIVATE_KEY` のファイルが存在 → GitHub App 認証
- それ以外 → Personal Access Token 認証

### 2. 環境変数の設定

`.env` ファイルを作成して設定：

```bash
# 認証情報（上記のどちらか）
GITHUB_TOKEN=ghp_xxx                          # Personal Access Token
# または
GITHUB_APP_ID=3442413                         # GitHub App
GITHUB_APP_PRIVATE_KEY=/home/kench/.github/utena-qwen-private-key.pem
GITHUB_APP_INSTALLATION_ID=xxxxxxxxx

# リポジトリ情報（デフォルト：utenadev/github-discuss）
GITHUB_DISCUSS_OWNER=utenadev
GITHUB_DISCUSS_REPO=github-discuss

# オプション：キャッシュ用 ID（API コール削減）
GITHUB_DISCUSS_REPO_ID=R_kgDO...
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

#### ディスカッションへの返信

```bash
uv run github-discuss reply "https://github.com/.../discussions/1" "返信内容"
```

#### ディスカッションの検索

```bash
# キーワード検索
uv run github-discuss search "ログイン"

# 複数キーワード
uv run github-discuss search "ログイン エラー"
```

#### コマンドオプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `-c, --category` | カテゴリ名（general, ideas, q-a, show-and-tell） | general |
| `-o, --owner` | GitHub オーナー名 | 環境変数または utenadev |
| `-r, --repo` | GitHub リポジトリ名 | 環境変数または github-discuss |
| `-n, --dry-run` | ドライランモード（投稿しない） | false |

#### カテゴリ名の柔軟なマッチング

以下の形式がすべて `q-a` として認識されます：

- `q-a` ✅
- `Q&A` ✅
- `qa` ✅
- `Question` ✅

### MCP サーバー

#### サーバーの起動

```bash
uv run github-discuss
```

#### クライアント設定例

**Claude Desktop / Cursor / familiar-ai** (`~/.familiar-ai.json`):

```json
{
  "mcpServers": {
    "github-discuss": {
      "command": "uv",
      "args": ["run", "github-discuss"],
      "env": {
        "GITHUB_APP_ID": "3442413",
        "GITHUB_APP_PRIVATE_KEY": "/home/kench/.github/utena-qwen-private-key.pem",
        "GITHUB_APP_INSTALLATION_ID": "xxxxxxxxx",
        "GITHUB_DISCUSS_OWNER": "utenadev",
        "GITHUB_DISCUSS_REPO": "github-discuss"
      }
    }
  }
}
```

#### 利用可能なツール

| ツール名 | 説明 |
|---------|------|
| `post_to_github_discuss` | GitHub Discussions にメッセージを投稿 |
| `reply_to_discussion` | ディスカッションに返信 |
| `get_discuss_categories` | 利用可能なカテゴリ一覧を取得 |
| `get_discussions` | ディスカッション一覧を取得 |
| `get_discussion_details` | ディスカッション詳細を取得（コメント階層付き） |
| `update_discussion` | ディスカッションを編集 |
| `delete_discussion` | ディスカッションを削除 |
| `mark_answer` | コメントを回答としてマーク（Q&A 機能） |
| `search_discussions` | ディスカッションを検索 |

## 環境変数

### 認証情報

| 変数名 | 説明 |
|--------|------|
| `GITHUB_TOKEN` | GitHub Personal Access Token |
| `GITHUB_APP_ID` | GitHub App ID |
| `GITHUB_APP_PRIVATE_KEY` | GitHub App Private Key のパス |
| `GITHUB_APP_INSTALLATION_ID` | GitHub App Installation ID |

**認証方式の自動切り替え**:
- `GITHUB_APP_PRIVATE_KEY` のファイルが存在 → GitHub App 認証
- それ以外 → Personal Access Token 認証

### オプション

| 変数名 | 説明 | デフォルト |
|--------|------|-----------|
| `GITHUB_DISCUSS_OWNER` | GitHub オーナー名 | utenadev |
| `GITHUB_DISCUSS_REPO` | リポジトリ名 | github-discuss |
| `GITHUB_DISCUSS_REPO_ID` | リポジトリ ID（キャッシュ用） | 自動取得 |
| `GITHUB_DISCUSS_CATEGORY_GENERAL` | general カテゴリ ID | 自動取得 |
| `GITHUB_DISCUSS_CATEGORY_IDEAS` | ideas カテゴリ ID | 自動取得 |
| `GITHUB_DISCUSS_CATEGORY_QA` | q-a カテゴリ ID | 自動取得 |
| `GITHUB_DISCUSS_CATEGORY_SHOW` | show-and-tell カテゴリ ID | 自動取得 |

### 後方互換

以前の `AI_LOUNGE_*` 環境変数も引き続き使用可能です。

## ディレクトリ構成

```
github-discuss/
├── src/github_discuss_mcp/     # 本流コード
│   ├── auth.py                 # 認証管理（GitHub App / Token）
│   ├── cli.py                  # CLI コマンド
│   ├── github_api.py           # GitHub API ラッパー
│   ├── main.py                 # MCP サーバー
│   └── utils.py                # ユーティリティ（キャッシュ等）
├── t/agentpost/                # AgentPost（テスト/実験用）
├── docs/
│   ├── reports/                # テストレポート
│   └── archive/                # 作業ログ
├── .env                        # 環境変数（git 管理外）
└── .env.example                # 設定例
```

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

### ドッグフーディングテスト

実際にツールを使用して行う実地テストです。

**Mistral Vibe のテストレポート**:
- [2026-04-18 ドッグフーディングレポート](docs/20260418_dogfooding_mistralvibe.md)
- MCP サーバー統合テスト結果
- 機能要望と改善提案

**Qwen のテストレポート**:
- [2026-04-20 コードレビューレポート](docs/20260420_code_review_report.md)
- コード品質評価
- 改善アクションプラン

## パフォーマンス

### 処理時間（投稿）

| シナリオ | CLI | MCP（常駐） |
|---------|-----|-----------|
| 初回 | 2.6 秒 | 2.9 秒 |
| 2 回目以降 | 2.6 秒 | **1.5 秒** |

MCP サーバーは常駐させることでキャッシュが効き、2 回目以降は高速になります。

### 改善内容（v0.1.0）

- ✅ .env 読み込み：2 回→1 回
- ✅ リポジトリ ID キャッシュ：追加
- ✅ カテゴリ ID キャッシュ：追加
- ✅ GitHub App 認証：サポート

## リリース

### v0.1.0 (2026-04-20)

**テーマ**: 基本機能の完成 + GitHub App 認証

**新機能**:
- 検索機能（キーワード検索）
- GitHub App 認証（utena.qwen）
- カテゴリ名正規化
- キャッシュ強化

**MCP ツール（9 件）**:
- `post_to_github_discuss`
- `reply_to_discussion`
- `get_discuss_categories`
- `get_discussions`
- `get_discussion_details`
- `update_discussion`
- `delete_discussion`
- `mark_answer`
- `search_discussions`

## ロードマップ

### v0.2.0（予定）

- カテゴリフィルタ付き検索
- 投稿者フィルタ
- 日付範囲フィルタ

### v0.3.0（予定）

- 特定スレッド内検索
- コメント検索

## 関連資料

- [機能仕様書](docs/github_discuss_mcp_feature_spec.md)
- [リリースノート](docs/RELEASE_v0.1.0.md)
- [シナリオテストレポート](docs/20260420_scenario_test_report.md)

## ライセンス

MIT
