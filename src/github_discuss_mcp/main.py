"""GitHub Discussions への投稿を行う MCP サーバー。

GitHub Discussions に投稿する機能を提供します。
"""

import os
import sys
import re
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from mcp.server import Server, NotificationOptions
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
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
    - get_discussions: ディスカッション一覧の取得

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
        ),
        Tool(
            name="get_discussions",
            description="GitHub Discussions の最新の投稿一覧を取得します。",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "カテゴリ名でフィルタリング（例：'general'）"
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
                "required": []
            }
        ),
        Tool(
            name="reply_to_discussion",
            description="既存の GitHub Discussions にコメント（返信）を追加します。",
            inputSchema={
                "type": "object",
                "properties": {
                    "discussion_url": {
                        "type": "string",
                        "description": "返信するディスカッションの URL"
                    },
                    "body": {
                        "type": "string",
                        "description": "コメント内容（Markdown 形式）"
                    }
                },
                "required": ["discussion_url", "body"]
            }
        ),
        Tool(
            name="get_discussion_details",
            description="ディスカッションの詳細（コメントの階層構造を含む）を取得します。",
            inputSchema={
                "type": "object",
                "properties": {
                    "discussion_url": {
                        "type": "string",
                        "description": "詳細を取得するディスカッションの URL"
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
                "required": ["discussion_url"]
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

    elif name == "get_discussions":
        # カテゴリ ID の解決（オプション）
        category_name = arguments.get("category")
        category_id = None
        if category_name:
            category_id = await resolve_category_id(
                api,
                category_name,
                repo_owner=repo_owner,
                repo_name=repo_name,
            )

        # ディスカッション一覧の取得
        discussions = await api.get_discussions(
            repo_owner, repo_name, category_id=category_id
        )

        if not discussions:
            return [TextContent(
                type="text",
                text="📭 ディスカッションが見つかりませんでした。"
            )]

        result_text = "📖 最新のディスカッション:\n\n"
        for d in discussions:
            author = d.get("author", {}).get("login", "不明")
            result_text += f"### {d['title']}\n"
            result_text += f"- **作者**: {author}\n"
            result_text += f"- **カテゴリ**: {d['category']['name']}\n"
            result_text += f"- **URL**: {d['url']}\n"
            result_text += f"- **作成日**: {d['createdAt']}\n\n"
            # 本文の冒頭を表示
            body = d.get("body", "")
            snippet = body[:200] + "..." if len(body) > 200 else body
            result_text += f"{snippet}\n\n---\n\n"

        return [TextContent(
            type="text",
            text=result_text
        )]

    elif name == "reply_to_discussion":
        # URL からディスカッション ID を取得する必要がある
        discussion_url = arguments.get("discussion_url")
        body = arguments.get("body")

        if not discussion_url or not body:
            return [TextContent(
                type="text",
                text="❌ エラー：discussion_url と body が必要です。"
            )]

        # URL からディスカッション番号を抽出 (例: .../discussions/13)
        match = re.search(r"discussions/(\d+)", discussion_url)
        discussion_id = None
        
        if match:
            number = int(match.group(1))
            # 番号から直接ディスカッション情報を取得
            discussion = await api.get_discussion_by_number(repo_owner, repo_name, number)
            if discussion:
                discussion_id = discussion["id"]
        else:
            # 正規表現でマッチしない場合は、従来の一覧検索をフォールバックとして試行
            discussions = await api.get_discussions(repo_owner, repo_name)
            for d in discussions:
                if d["url"] == discussion_url:
                    discussion_id = d["id"]
                    break

        if not discussion_id:
            return [TextContent(
                type="text",
                text=f"❌ エラー：ディスカッション '{discussion_url}' の ID を特定できませんでした。"
            )]

        # コメントを追加
        result = await api.add_comment(discussion_id, body)

        if result.get("success"):
            return [TextContent(
                type="text",
                text=f"✅ コメントを追加しました！\n{discussion_url}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"❌ コメントの追加に失敗しました：{result.get('error')}"
            )]

    elif name == "get_discussion_details":
        # URL からディスカッション番号を抽出
        discussion_url = arguments.get("discussion_url")
        if not discussion_url:
            return [TextContent(
                type="text",
                text="❌ エラー：discussion_url が必要です。"
            )]

        # URL から番号を抽出
        match = re.search(r'/discussions/(\d+)', discussion_url)
        if match:
            number = int(match.group(1))
            # 番号から直接ディスカッション情報を取得
            discussion = await api.get_discussion_details(repo_owner, repo_name, number)
        else:
            return [TextContent(
                type="text",
                text=f"❌ エラー：無効なディスカッション URL です：{discussion_url}"
            )]

        if not discussion:
            return [TextContent(
                type="text",
                text=f"❌ エラー：ディスカッション '{discussion_url}' が見つかりませんでした。"
            )]

        # 詳細情報をフォーマット
        result_text = f"# {discussion['title']}\n\n"
        result_text += f"**URL**: {discussion['url']}\n"
        result_text += f"**カテゴリ**: {discussion['category']['name']}\n"
        result_text += f"**作者**: {discussion['author']['login']}\n"
        result_text += f"**作成日**: {discussion['createdAt']}\n\n"
        result_text += "---\n\n"
        result_text += f"{discussion['body']}\n\n"
        result_text += "---\n\n"

        # コメントを追加
        comments = discussion.get("comments", {}).get("nodes", [])
        if comments:
            result_text += f"## コメント ({len(comments)}件)\n\n"
            for comment in comments:
                result_text += f"### 💬 {comment['author']['login']} - {comment['createdAt']}\n\n"
                result_text += f"{comment['body']}\n\n"

                # 返信を追加
                replies = comment.get("replies", {}).get("nodes", [])
                if replies:
                    for reply in replies:
                        result_text += f"  ↳ **{reply['author']['login']}** ({reply['createdAt']}): {reply['body']}\n"
                    result_text += "\n"
        else:
            result_text += "コメントはまだありません。\n"

        return [TextContent(
            type="text",
            text=result_text
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
    from pathlib import Path

    # スクリプトの場所からプロジェクトルートにある .env を探す
    base_path = Path(__file__).parent.parent.parent
    env_path = base_path / ".env"
    
    # .env ファイルを読み込む
    load_dotenv(dotenv_path=env_path)

    # トークンの確認（デバッグ用に stderr に出力）
    if not os.getenv("GITHUB_TOKEN"):
        print("❌ エラー：GITHUB_TOKEN が環境変数に設定されていません。", file=sys.stderr)
        # 終了せずに続行すると、ツール実行時にエラーになる

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="github-discuss-mcp",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    asyncio.run(main())


if __name__ == "__main__":
    run()
