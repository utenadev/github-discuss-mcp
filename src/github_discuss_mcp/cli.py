"""GitHub Discussions への投稿を行う CLI ツール。

MCP サーバーと同じ機能を提供します。
"""

import os
import asyncio
import typer
from dotenv import load_dotenv

from .github_api import GitHubDiscussionsAPI, DiscussionInput
from .utils import (
    resolve_category_id,
    get_repo_id_cached,
    DEFAULT_OWNER,
    DEFAULT_REPO,
)

# 環境変数の読み込み
load_dotenv()

# CLI アプリケーションの定義
app = typer.Typer(
    help="GitHub Discussions CLI - GitHub Discussions として投稿"
)


# ============================================================================
# CLI コマンド
# ============================================================================

@app.command("post")
def post(
    title: str = typer.Argument(..., help="Discussion タイトル"),
    body: str = typer.Argument(..., help="投稿内容（Markdown 形式）"),
    category: str = typer.Option(
        "general",
        "--category",
        "-c",
        help="カテゴリ：general, ideas, q-a, show-and-tell"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="送信せずにプレビュー表示"
    ),
    owner: str = typer.Option(
        None,
        "--owner",
        "-o",
        help=f"GitHub オーナー名（デフォルト：{DEFAULT_OWNER}）"
    ),
    repo: str = typer.Option(
        None,
        "--repo",
        "-r",
        help=f"GitHub リポジトリ名（デフォルト：{DEFAULT_REPO}）"
    ),
):
    """GitHub Discussions にメッセージを投稿します。"""
    # リポジトリ情報の決定（引数→環境変数→デフォルト）
    repo_owner = owner or os.getenv("GITHUB_DISCUSS_OWNER", DEFAULT_OWNER)
    repo_name = repo or os.getenv("GITHUB_DISCUSS_REPO", DEFAULT_REPO)

    # ドライランモード
    if dry_run:
        typer.echo("🔍 ドライラン - 以下の内容で投稿します:")
        typer.echo(f"   オーナー：{repo_owner}")
        typer.echo(f"   リポジトリ：{repo_name}")
        typer.echo(f"   タイトル：{title}")
        typer.echo(f"   カテゴリ：{category}")
        typer.echo(f"   本文:\n{body}")
        return

    # 非同期処理の実行
    async def _post():
        api = GitHubDiscussionsAPI()

        # カテゴリ ID の解決
        category_id = await resolve_category_id(
            api,
            category,
            repo_owner=repo_owner,
            repo_name=repo_name,
        )
        if not category_id:
            typer.echo(f"❌ カテゴリ '{category}' が見つかりません")
            raise typer.Exit(1)

        # リポジトリ ID の解決
        try:
            repo_id = await get_repo_id_cached(api, owner=repo_owner, repo=repo_name)
        except ValueError as e:
            typer.echo(f"❌ エラー：{e}")
            raise typer.Exit(1)

        # 投稿実行
        result = await api.create_discussion(DiscussionInput(
            repository_id=repo_id,
            category_id=category_id,
            title=title,
            body=body
        ))

        if result.success:
            typer.echo(f"✅ 投稿が完了しました！ {result.discussion_url}")
        else:
            typer.echo(f"❌ エラー：{result.error}")
            raise typer.Exit(1)

    asyncio.run(_post())


@app.command("categories")
def list_categories(
    owner: str = typer.Option(
        None,
        "--owner",
        "-o",
        help=f"GitHub オーナー名（デフォルト：{DEFAULT_OWNER}）"
    ),
    repo: str = typer.Option(
        None,
        "--repo",
        "-r",
        help=f"GitHub リポジトリ名（デフォルト：{DEFAULT_REPO}）"
    ),
):
    """利用可能なディスカッションカテゴリの一覧を表示します。"""
    # リポジトリ情報の決定
    repo_owner = owner or os.getenv("GITHUB_DISCUSS_OWNER", DEFAULT_OWNER)
    repo_name = repo or os.getenv("GITHUB_DISCUSS_REPO", DEFAULT_REPO)

    async def _list():
        api = GitHubDiscussionsAPI()
        categories = await api.get_categories(repo_owner, repo_name)
        for cat in categories:
            emoji = cat.get("emoji", "📁")
            typer.echo(f"{emoji} `{cat['name']}`: {cat.get('description', '')}")

    asyncio.run(_list())


@app.command("setup")
def setup_guide():
    """セットアップ手順を表示します。"""
    typer.echo("""
🔧 GitHub Discussions MCP/CLI セットアップガイド

1. GitHub Personal Access Token の取得:
   - https://github.com/settings/tokens にアクセス
   - 以下のスコープを持つトークンを作成：repo, write:discussion
   - GITHUB_TOKEN 環境変数として保存

2. リポジトリ/カテゴリ ID の取得:
   $ github-discuss categories

3. 環境変数の設定:
   $ export GITHUB_TOKEN=ghp_xxx
   $ export GITHUB_DISCUSS_OWNER=your-org  # オプション
   $ export GITHUB_DISCUSS_REPO=your-repo  # オプション
   $ export GITHUB_DISCUSS_REPO_ID=R_kgDO...  # オプション（キャッシュ用）

4. 投稿：
   $ github-discuss post "今日の気づき" "こんにちは、今日カメラで見たこと..." -c general

🤖 MCP クライアント設定例 (~/.familiar-ai.json):
{
  "mcpServers": {
    "github-discuss": {
      "command": "uvx",
      "args": ["github-discuss-mcp"],
      "env": {
        "GITHUB_TOKEN": "your-token-here"
      }
    }
  }
}
    """)


if __name__ == "__main__":
    app()
