"""MCP サーバーのテスト。"""

import os
import pytest
import respx
from httpx import Response
from unittest.mock import AsyncMock, patch, MagicMock
from contextvars import ContextVar

from github_discuss_mcp.main import server, list_tools, call_tool
from github_discuss_mcp.github_api import GitHubDiscussionsAPI


class TestListTools:
    """list_tools 関数のテスト。"""

    @pytest.mark.asyncio
    async def test_list_tools_returns_two_tools(self):
        """list_tools が正確に 2 つのツールを返すテスト。"""
        tools = await list_tools()
        assert len(tools) == 2

    @pytest.mark.asyncio
    async def test_post_to_github_discuss_tool_exists(self):
        """post_to_github_discuss ツールが定義されているテスト。"""
        tools = await list_tools()
        tool_names = [t.name for t in tools]
        assert "post_to_github_discuss" in tool_names

    @pytest.mark.asyncio
    async def test_get_discuss_categories_tool_exists(self):
        """get_discuss_categories ツールが定義されているテスト。"""
        tools = await list_tools()
        tool_names = [t.name for t in tools]
        assert "get_discuss_categories" in tool_names

    @pytest.mark.asyncio
    async def test_post_tool_schema(self):
        """post_to_github_discuss ツールのスキーマテスト。"""
        tools = await list_tools()
        post_tool = next(t for t in tools if t.name == "post_to_github_discuss")
        schema = post_tool.inputSchema

        assert "title" in schema["properties"]
        assert "body" in schema["properties"]
        assert "category" in schema["properties"]
        assert "title" in schema["required"]
        assert "body" in schema["required"]
        assert "category" in schema["required"]
        assert schema["properties"]["category"]["enum"] == [
            "general", "ideas", "q-a", "show-and-tell"
        ]

    @pytest.mark.asyncio
    async def test_get_discuss_categories_tool_schema(self):
        """get_discuss_categories ツールのスキーマテスト。"""
        tools = await list_tools()
        cat_tool = next(t for t in tools if t.name == "get_discuss_categories")
        # owner と repo プロパティを持つ
        assert "owner" in cat_tool.inputSchema["properties"]
        assert "repo" in cat_tool.inputSchema["properties"]


class TestCallTool:
    """call_tool 関数のテスト。"""

    def _setup_request_context(self, api):
        """指定された API でモックリクエストコンテキストをセットアップする。"""
        from mcp.server.lowlevel.server import request_ctx
        from unittest.mock import MagicMock

        mock_request_ctx = MagicMock()
        mock_request_ctx.lifespan_context = {"api": api}
        token = request_ctx.set(mock_request_ctx)
        return token

    def _cleanup_request_context(self, token):
        """リクエストコンテキストをクリーンアップする。"""
        from mcp.server.lowlevel.server import request_ctx
        request_ctx.reset(token)

    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(self, mock_token):
        """不明なツールが ValueError を発生させるテスト。"""
        api = GitHubDiscussionsAPI(token=mock_token)
        token = self._setup_request_context(api)
        try:
            with pytest.raises(ValueError, match="不明なツール"):
                await call_tool("unknown_tool", {})
        finally:
            self._cleanup_request_context(token)

    @pytest.mark.asyncio
    @respx.mock
    async def test_call_tool_post_success(self, mock_token, monkeypatch):
        """call_tool 経由での投稿成功テスト。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.setenv("GITHUB_DISCUSS_REPO_ID", "R_test_repo")
        monkeypatch.setenv("GITHUB_DISCUSS_CATEGORY_GENERAL", "DIC_general")

        mock_response = {
            "data": {
                "createDiscussion": {
                    "discussion": {
                        "id": "D_test",
                        "url": "https://github.com/lifemate-ai/ai-lounge/discussions/1",
                        "title": "Test",
                    }
                }
            }
        }
        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_response)
        )

        api = GitHubDiscussionsAPI(token=mock_token)
        token = self._setup_request_context(api)
        try:
            result = await call_tool("post_to_github_discuss", {
                "title": "Test Title",
                "body": "I am an AI assistant.",
                "category": "general",
            })
        finally:
            self._cleanup_request_context(token)

        assert len(result) == 1
        assert "✅ 投稿が完了しました" in result[0].text

    @pytest.mark.asyncio
    @respx.mock
    async def test_call_tool_post_category_not_found(self, mock_token, monkeypatch):
        """無効なカテゴリでの投稿失敗テスト。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.setenv("GITHUB_DISCUSS_REPO_ID", "R_test_repo")
        monkeypatch.delenv("GITHUB_DISCUSS_CATEGORY_GENERAL", raising=False)
        monkeypatch.delenv("GITHUB_DISCUSS_CATEGORY_IDEAS", raising=False)
        monkeypatch.delenv("GITHUB_DISCUSS_CATEGORY_QA", raising=False)
        monkeypatch.delenv("GITHUB_DISCUSS_CATEGORY_SHOW", raising=False)

        mock_categories = {
            "data": {
                "repository": {
                    "discussionCategories": {"nodes": []}
                }
            }
        }
        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_categories)
        )

        api = GitHubDiscussionsAPI(token=mock_token)
        token = self._setup_request_context(api)
        try:
            result = await call_tool("post_to_github_discuss", {
                "title": "Test Title",
                "body": "I am an AI.",
                "category": "nonexistent",
            })
        finally:
            self._cleanup_request_context(token)

        assert len(result) == 1
        assert "❌ エラー：カテゴリ 'nonexistent' が見つかりません" in result[0].text

    @pytest.mark.asyncio
    @respx.mock
    async def test_call_tool_post_api_failure(self, mock_token, monkeypatch):
        """API エラーによる投稿失敗テスト。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.setenv("GITHUB_DISCUSS_REPO_ID", "R_test_repo")
        monkeypatch.setenv("GITHUB_DISCUSS_CATEGORY_GENERAL", "DIC_general")

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(500, json={"message": "Internal Server Error"})
        )

        api = GitHubDiscussionsAPI(token=mock_token)
        token = self._setup_request_context(api)
        try:
            result = await call_tool("post_to_github_discuss", {
                "title": "Test Title",
                "body": "I am an AI assistant.",
                "category": "general",
            })
        finally:
            self._cleanup_request_context(token)

        assert len(result) == 1
        assert "❌ 投稿に失敗しました" in result[0].text

    @pytest.mark.asyncio
    @respx.mock
    async def test_call_tool_get_categories_success(self, mock_token, monkeypatch):
        """get_discuss_categories がカテゴリを返すテスト。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)

        mock_categories = {
            "data": {
                "repository": {
                    "discussionCategories": {
                        "nodes": [
                            {
                                "id": "DIC_general",
                                "name": "general",
                                "emoji": "💬",
                                "description": "General discussion",
                            },
                        ]
                    }
                }
            }
        }
        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_categories)
        )

        api = GitHubDiscussionsAPI(token=mock_token)
        token = self._setup_request_context(api)
        try:
            result = await call_tool("get_discuss_categories", {})
        finally:
            self._cleanup_request_context(token)

        assert len(result) == 1
        assert "📋 利用可能なカテゴリ一覧" in result[0].text
        assert "general" in result[0].text

    @pytest.mark.asyncio
    @respx.mock
    async def test_call_tool_post_missing_repo_id_fallback_api(self, mock_token, monkeypatch):
        """GITHUB_DISCUSS_REPO_ID が設定されていない場合 API fallback のテスト。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.delenv("GITHUB_DISCUSS_REPO_ID", raising=False)
        monkeypatch.delenv("AI_LOUNGE_REPO_ID", raising=False)
        monkeypatch.setenv("GITHUB_DISCUSS_CATEGORY_GENERAL", "DIC_general")

        call_count = 0

        def mock_route(request):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # リポジトリ ID 取得
                return Response(200, json={
                    "data": {"repository": {"id": "R_test_repo"}}
                })
            else:
                # ディスカッション作成
                return Response(200, json={
                    "data": {
                        "createDiscussion": {
                            "discussion": {
                                "id": "D_test",
                                "url": "https://github.com/lifemate-ai/ai-lounge/discussions/1",
                                "title": "Test",
                            }
                        }
                    }
                })

        respx.post("https://api.github.com/graphql").mock(side_effect=mock_route)

        api = GitHubDiscussionsAPI(token=mock_token)
        token = self._setup_request_context(api)
        try:
            result = await call_tool("post_to_github_discuss", {
                "title": "Test Title",
                "body": "I am an AI.",
                "category": "general",
            })
        finally:
            self._cleanup_request_context(token)

        assert len(result) == 1
        assert "✅ 投稿が完了しました" in result[0].text
