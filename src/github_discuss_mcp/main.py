"""GitHub Discussions への投稿を行う MCP サーバー。

GitHub Discussions に投稿する機能を提供します。
"""

import os
from contextlib import asynccontextmanager
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .github_api import GitHubDiscussionsAPI, DiscussionInput
from .utils import (
    resolve_category_id,
    get_repo_id_cached,
    DEFAULT_OWNER,
    DEFAULT_REPO,
)


# ============================================================================
# サーバーライフサイクル管理
# ============================================================================

@asynccontextmanager
async def server_lifespan(server: Server):
    """サーバーのライフサイクルを管理するコンテキストマネージャ。

    サーバー起動時に GitHubDiscussionsAPI を初期化し、
    各リクエストで再利用できるようにします。

    Args:
        server: MCP サーバーインスタンス

    Yields:
        API インスタンスを含むコンテキスト辞書
    """
    # 起動時に API を初期化
    api = GitHubDiscussionsAPI(token=os.getenv("GITHUB_TOKEN"))
    yield {"api": api}


# ============================================================================
# MCP サーバーインスタンスの作成
# ============================================================================

# サーバー名を汎用化
server = Server("github-discuss-mcp", lifespan=server_lifespan)


# ============================================================================
# ツール定義
# ============================================================================

@server.list_tools()
async def list_tools():
    """利用可能な MCP ツールの一覧を返す。

    以下のツールを提供します：
    - post_to_github_discuss: GitHub Discussions への投稿
    - get_discuss_categories: カテゴリ一覧の取得

    Returns:
        Tool オブジェクトのリスト
    """
    return [
        Tool(
            name="post_to_github_discuss",
            description="GitHub Discussions にメッセージを投稿します。",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "ディスカッションのタイトル（例：'今日の気づき'）"
                    },
                    "body": {
                        "type": "string",
                        "description": "投稿内容（Markdown 形式）"
                    },
                    "category": {
                        "type": "string",
                        "description": "カテゴリ名：'general', 'ideas', 'q-a', 'show-and-tell'",
                        "enum": ["general", "ideas", "q-a", "show-and-tell"]
                    },
                    "owner": {
                        "type": "string",
                        "description": f"GitHub オーナー名（デフォルト：{DEFAULT_OWNER}）"
                    },
                    "repo": {
                        "type": "string",
                        "description": f"GitHub リポジトリ名（デフォルト：{DEFAULT_REPO}）"
                    }
                },
                "required": ["title", "body", "category"]
            }
        ),
        Tool(
            name="get_discuss_categories",
            description="GitHub Discussions の利用可能なカテゴリ一覧を取得します。",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": f"GitHub オーナー名（デフォルト：{DEFAULT_OWNER}）"
                    },
                    "repo": {
                        "type": "string",
                        "description": f"GitHub リポジトリ名（デフォルト：{DEFAULT_REPO}）"
                    }
                },
                "required": []
            }
        )
    ]


# ============================================================================
# ツール実行ハンドラ
# ============================================================================

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """MCP クライアントからのツール呼び出しを処理する。

    Args:
        name: ツール名
        arguments: ツールへの引数

    Returns:
        TextContent オブジェクトのリスト

    Raises:
        ValueError: 不明なツール名の場合
    """
    # ライフサイクルコンテキストから API インスタンスを取得
    ctx = server.request_context.lifespan_context
    api: GitHubDiscussionsAPI = ctx["api"]

    # リポジトリ情報の取得（引数→環境変数→デフォルト）
    repo_owner = arguments.get("owner") or os.getenv("GITHUB_DISCUSS_OWNER", DEFAULT_OWNER)
    repo_name = arguments.get("repo") or os.getenv("GITHUB_DISCUSS_REPO", DEFAULT_REPO)

    if name == "post_to_github_discuss":
        # カテゴリ ID の解決
        category_name = arguments.get("category", "general")
        category_id = await resolve_category_id(
            api,
            category_name,
            repo_owner=repo_owner,
            repo_name=repo_name,
        )

        if not category_id:
            return [TextContent(
                type="text",
                text=f"❌ エラー：カテゴリ '{category_name}' が見つかりません。\n"
                     f"使用可能なカテゴリ：general, ideas, q-a, show-and-tell"
            )]

        # リポジトリ ID の解決
        try:
            repo_id = await get_repo_id_cached(
                api,
                owner=repo_owner,
                repo=repo_name,
            )
        except ValueError as e:
            return [TextContent(
                type="text",
                text=f"❌ エラー：{str(e)}"
            )]

        # ディスカッションの作成
        result = await api.create_discussion(DiscussionInput(
            repository_id=repo_id,
            category_id=category_id,
            title=arguments["title"],
            body=arguments["body"]
        ))

        if result.success:
            return [TextContent(
                type="text",
                text=f"✅ 投稿が完了しました！\n🔗 {result.discussion_url}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"❌ 投稿に失敗しました：{result.error}"
            )]

    elif name == "get_discuss_categories":
        # カテゴリ一覧の取得
        categories = await api.get_categories(repo_owner, repo_name)
        category_list = "\n".join(
            f"- `{cat['name']}` {cat.get('emoji', '')}: {cat.get('description', '')}"
            for cat in categories
        )
        return [TextContent(
            type="text",
            text=f"📋 利用可能なカテゴリ一覧:\n{category_list}"
        )]

    else:
        raise ValueError(f"不明なツール：{name}")


# ============================================================================
# サーバー実行エントリーポイント
# ============================================================================

def run():
    """MCP サーバーを stdio で実行する。

    標準入力・標準出力を使用して MCP プロトコルで通信します。
    """
    import asyncio

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream)

    asyncio.run(main())


if __name__ == "__main__":
    run()
