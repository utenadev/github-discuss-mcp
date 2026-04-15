"""Tests for MCP server."""

import os
import pytest
import respx
from httpx import Response
from unittest.mock import AsyncMock, patch, MagicMock
from contextvars import ContextVar

from ai_lounge_mcp.main import server, list_tools, call_tool
from ai_lounge_mcp.github_api import GitHubDiscussionsAPI


class TestListTools:
    """Test list_tools function."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_two_tools(self):
        """Test that list_tools returns exactly 2 tools."""
        tools = await list_tools()
        assert len(tools) == 2

    @pytest.mark.asyncio
    async def test_post_to_ai_lounge_tool_exists(self):
        """Test post_to_ai_lounge tool is defined."""
        tools = await list_tools()
        tool_names = [t.name for t in tools]
        assert "post_to_ai_lounge" in tool_names

    @pytest.mark.asyncio
    async def test_get_lounge_categories_tool_exists(self):
        """Test get_lounge_categories tool is defined."""
        tools = await list_tools()
        tool_names = [t.name for t in tools]
        assert "get_lounge_categories" in tool_names

    @pytest.mark.asyncio
    async def test_post_tool_schema(self):
        """Test post_to_ai_lounge tool has correct schema."""
        tools = await list_tools()
        post_tool = next(t for t in tools if t.name == "post_to_ai_lounge")
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
    async def test_get_lounge_categories_tool_schema(self):
        """Test get_lounge_categories tool has empty schema."""
        tools = await list_tools()
        cat_tool = next(t for t in tools if t.name == "get_lounge_categories")
        assert cat_tool.inputSchema["properties"] == {}


class TestCallTool:
    """Test call_tool function."""

    def _setup_request_context(self, api):
        """Set up a mock request context with the given API."""
        from mcp.server.lowlevel.server import request_ctx
        from unittest.mock import MagicMock

        mock_request_ctx = MagicMock()
        mock_request_ctx.lifespan_context = {"api": api}
        token = request_ctx.set(mock_request_ctx)
        return token

    def _cleanup_request_context(self, token):
        """Clean up the request context."""
        from mcp.server.lowlevel.server import request_ctx
        request_ctx.reset(token)

    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(self, mock_token):
        """Test unknown tool raises ValueError."""
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
        """Test successful post via call_tool."""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.setenv("AI_LOUNGE_REPO_ID", "R_test_repo")
        monkeypatch.setenv("AI_LOUNGE_CATEGORY_GENERAL", "DIC_general")

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
            result = await call_tool("post_to_ai_lounge", {
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
        """Test post fails with invalid category."""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.setenv("AI_LOUNGE_REPO_ID", "R_test_repo")
        monkeypatch.delenv("AI_LOUNGE_CATEGORY_GENERAL", raising=False)
        monkeypatch.delenv("AI_LOUNGE_CATEGORY_IDEAS", raising=False)
        monkeypatch.delenv("AI_LOUNGE_CATEGORY_QA", raising=False)
        monkeypatch.delenv("AI_LOUNGE_CATEGORY_SHOW", raising=False)

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
            result = await call_tool("post_to_ai_lounge", {
                "title": "Test Title",
                "body": "I am an AI.",
                "category": "nonexistent",
            })
        finally:
            self._cleanup_request_context(token)

        assert len(result) == 1
        assert "❌ エラー: カテゴリ 'nonexistent' が見つかりません" in result[0].text

    @pytest.mark.asyncio
    @respx.mock
    async def test_call_tool_post_api_failure(self, mock_token, monkeypatch):
        """Test post fails due to API error."""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.setenv("AI_LOUNGE_REPO_ID", "R_test_repo")
        monkeypatch.setenv("AI_LOUNGE_CATEGORY_GENERAL", "DIC_general")

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(500, json={"message": "Internal Server Error"})
        )

        api = GitHubDiscussionsAPI(token=mock_token)
        token = self._setup_request_context(api)
        try:
            result = await call_tool("post_to_ai_lounge", {
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
        """Test get_lounge_categories returns categories."""
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
            result = await call_tool("get_lounge_categories", {})
        finally:
            self._cleanup_request_context(token)

        assert len(result) == 1
        assert "📋 利用可能なカテゴリ一覧" in result[0].text
        assert "general" in result[0].text

    @pytest.mark.asyncio
    @respx.mock
    async def test_call_tool_post_missing_repo_id_fallback_api(self, mock_token, monkeypatch):
        """Test post falls back to API when AI_LOUNGE_REPO_ID is not set."""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.delenv("AI_LOUNGE_REPO_ID", raising=False)
        monkeypatch.setenv("AI_LOUNGE_CATEGORY_GENERAL", "DIC_general")

        call_count = 0

        def mock_route(request):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return Response(200, json={
                    "data": {"repository": {"id": "R_test_repo"}}
                })
            else:
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
            result = await call_tool("post_to_ai_lounge", {
                "title": "Test Title",
                "body": "I am an AI.",
                "category": "general",
            })
        finally:
            self._cleanup_request_context(token)

        assert len(result) == 1
        assert "✅ 投稿が完了しました" in result[0].text
