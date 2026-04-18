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


@app.command("list")
def list_discussions(
    category: str = typer.Option(
        None,
        "--category",
        "-c",
        help="カテゴリ名でフィルタリング（例：general）"
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
    """最新のディスカッション一覧を表示します。"""
    repo_owner = owner or os.getenv("GITHUB_DISCUSS_OWNER", DEFAULT_OWNER)
    repo_name = repo or os.getenv("GITHUB_DISCUSS_REPO", DEFAULT_REPO)

    async def _list():
        api = GitHubDiscussionsAPI()

        # カテゴリ ID の解決（オプション）
        category_id = None
        if category:
            category_id = await resolve_category_id(
                api,
                category,
                repo_owner=repo_owner,
                repo_name=repo_name,
            )

        discussions = await api.get_discussions(
            repo_owner, repo_name, category_id=category_id
        )

        if not discussions:
            typer.echo("📭 ディスカッションが見つかりませんでした。")
            return

        typer.echo("📖 最新のディスカッション:\n")
        for d in discussions:
            author = d.get("author", {}).get("login", "不明")
            typer.echo(f"### {d['title']}")
            typer.echo(f"- **作者**: {author}")
            typer.echo(f"- **カテゴリ**: {d['category']['name']}")
            typer.echo(f"- **URL**: {d['url']}")
            typer.echo(f"- **作成日**: {d['createdAt']}")
            # 本文の冒頭を表示
            body = d.get("body", "")
            snippet = body[:200] + "..." if len(body) > 200 else body
            typer.echo(f"\n{snippet}\n")
            typer.echo("---\n")

    asyncio.run(_list())


@app.command("reply")
def reply(
    discussion_url: str = typer.Argument(..., help="返信するディスカッションの URL"),
    body: str = typer.Argument(..., help="コメント内容（Markdown 形式）"),
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
    """既存のディスカッションにコメント（返信）を追加します。"""
    repo_owner = owner or os.getenv("GITHUB_DISCUSS_OWNER", DEFAULT_OWNER)
    repo_name = repo or os.getenv("GITHUB_DISCUSS_REPO", DEFAULT_REPO)

    async def _reply():
        api = GitHubDiscussionsAPI()

        # URL からディスカッション番号を抽出
        # 例：https://github.com/utenadev/github-discuss-mcp/discussions/15 -> 15
        try:
            discussion_number = int(discussion_url.rstrip("/").split("/")[-1])
        except ValueError:
            typer.echo(f"❌ エラー：無効なディスカッション URL です：{discussion_url}")
            raise typer.Exit(1)

        # ディスカッションを取得して ID を取得
        discussion = await api.get_discussion_by_number(
            repo_owner, repo_name, discussion_number
        )

        if not discussion:
            typer.echo(f"❌ エラー：ディスカッション '#{discussion_number}' が見つかりませんでした。")
            raise typer.Exit(1)

        # ID を取得（そのまま使用）
        discussion_id = discussion["id"]

        # コメントを追加
        result = await api.add_comment(discussion_id, body)

        if result.get("success"):
            typer.echo(f"✅ コメントを追加しました！\n{discussion_url}")
        else:
            typer.echo(f"❌ コメントの追加に失敗しました：{result.get('error')}")
            raise typer.Exit(1)

    asyncio.run(_reply())


@app.command("show")
def show_discussion(
    discussion_url: str = typer.Argument(..., help="表示するディスカッションの URL"),
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
    """ディスカッションの詳細（コメントの階層構造を含む）を表示します。"""
    repo_owner = owner or os.getenv("GITHUB_DISCUSS_OWNER", DEFAULT_OWNER)
    repo_name = repo or os.getenv("GITHUB_DISCUSS_REPO", DEFAULT_REPO)

    async def _show():
        api = GitHubDiscussionsAPI()

        # URL からディスカッション番号を抽出
        try:
            discussion_number = int(discussion_url.rstrip("/").split("/")[-1])
        except ValueError:
            typer.echo(f"❌ エラー：無効なディスカッション URL です：{discussion_url}")
            raise typer.Exit(1)

        # ディスカッション詳細を取得
        discussion = await api.get_discussion_details(
            repo_owner, repo_name, discussion_number
        )

        if not discussion:
            typer.echo(f"❌ エラー：ディスカッション '#{discussion_number}' が見つかりませんでした。")
            raise typer.Exit(1)

        # ディスカッション情報を表示
        typer.echo(f"# {discussion['title']}")
        typer.echo(f"**URL**: {discussion['url']}")
        typer.echo(f"**カテゴリ**: {discussion['category']['name']}")
        typer.echo(f"**作者**: {discussion['author']['login']}")
        typer.echo(f"**作成日**: {discussion['createdAt']}")
        typer.echo(f"**更新日**: {discussion['updatedAt']}")
        typer.echo("")
        typer.echo("---")
        typer.echo("")
        typer.echo(f"{discussion['body']}")
        typer.echo("")
        typer.echo("---")
        typer.echo("")

        # コメントを表示
        comments = discussion.get("comments", {}).get("nodes", [])
        if comments:
            typer.echo(f"## コメント ({len(comments)}件)")
            typer.echo("")

            for comment in comments:
                typer.echo(f"### 💬 {comment['author']['login']} - {comment['createdAt']}")
                typer.echo("")
                typer.echo(f"{comment['body']}")
                typer.echo("")

                # 返信を表示
                replies = comment.get("replies", {}).get("nodes", [])
                if replies:
                    for reply in replies:
                        typer.echo(f"  ↳ **{reply['author']['login']}** ({reply['createdAt']}): {reply['body']}")
                    typer.echo("")
        else:
            typer.echo("コメントはまだありません。")

    asyncio.run(_show())


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
