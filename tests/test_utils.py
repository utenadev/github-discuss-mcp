"""Tests for utility functions."""

import os
import pytest
import respx
from httpx import Response

from ai_lounge_mcp.utils import (
    get_category_id_from_env,
    resolve_category_id,
    get_repo_id_cached,
    validate_env,
    CATEGORY_ENV_VARS,
)
from ai_lounge_mcp.github_api import GitHubDiscussionsAPI


class TestGetCategoryIdFromEnv:
    """Test get_category_id_from_env function."""

    def test_returns_env_value(self, monkeypatch):
        """Returns category ID from environment variable."""
        monkeypatch.setenv("AI_LOUNGE_CATEGORY_GENERAL", "DIC_general")
        assert get_category_id_from_env("general") == "DIC_general"

    def test_returns_empty_string_if_not_set(self, monkeypatch):
        """Returns empty string if env var not set."""
        monkeypatch.delenv("AI_LOUNGE_CATEGORY_GENERAL", raising=False)
        assert get_category_id_from_env("general") == ""

    def test_returns_none_for_unknown_category(self):
        """Returns None for unknown category."""
        assert get_category_id_from_env("unknown") == ""


class TestResolveCategoryId:
    """Test resolve_category_id function."""

    @pytest.mark.asyncio
    async def test_returns_env_value_if_set(self, mock_token, monkeypatch):
        """Returns category ID from env without calling API."""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.setenv("AI_LOUNGE_CATEGORY_GENERAL", "DIC_general")

        api = GitHubDiscussionsAPI(token=mock_token)
        result = await resolve_category_id(api, "general")
        assert result == "DIC_general"

    @pytest.mark.asyncio
    @respx.mock
    async def test_falls_back_to_api_if_env_empty(self, mock_token, monkeypatch):
        """Falls back to API if env var is empty."""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.delenv("AI_LOUNGE_CATEGORY_GENERAL", raising=False)

        mock_categories = {
            "data": {
                "repository": {
                    "discussionCategories": {
                        "nodes": [
                            {"id": "DIC_general", "name": "general", "emoji": "💬", "description": ""}
                        ]
                    }
                }
            }
        }
        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_categories)
        )

        api = GitHubDiscussionsAPI(token=mock_token)
        result = await resolve_category_id(api, "general")
        assert result == "DIC_general"

    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_none_if_not_found(self, mock_token, monkeypatch):
        """Returns None if category not found in env or API."""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        for var in CATEGORY_ENV_VARS.values():
            monkeypatch.delenv(var, raising=False)

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json={
                "data": {"repository": {"discussionCategories": {"nodes": []}}}
            })
        )

        api = GitHubDiscussionsAPI(token=mock_token)
        result = await resolve_category_id(api, "general")
        assert result is None


class TestGetRepoIdCached:
    """Test get_repo_id_cached function."""

    @pytest.mark.asyncio
    async def test_returns_env_value_if_set(self, mock_token, monkeypatch):
        """Returns repo ID from env without calling API."""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.setenv("AI_LOUNGE_REPO_ID", "R_test_repo")

        api = GitHubDiscussionsAPI(token=mock_token)
        result = await get_repo_id_cached(api)
        assert result == "R_test_repo"

    @pytest.mark.asyncio
    @respx.mock
    async def test_falls_back_to_api_if_env_empty(self, mock_token, monkeypatch):
        """Falls back to API if env var not set."""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.delenv("AI_LOUNGE_REPO_ID", raising=False)

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json={
                "data": {"repository": {"id": "R_test_repo"}}
            })
        )

        api = GitHubDiscussionsAPI(token=mock_token)
        result = await get_repo_id_cached(api)
        assert result == "R_test_repo"

    @pytest.mark.asyncio
    @respx.mock
    async def test_raises_if_api_fails(self, mock_token, monkeypatch):
        """Raises ValueError if API fails to return repo ID."""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.delenv("AI_LOUNGE_REPO_ID", raising=False)

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json={
                "data": {"repository": None}
            })
        )

        api = GitHubDiscussionsAPI(token=mock_token)
        with pytest.raises(ValueError, match="リポジトリ"):
            await get_repo_id_cached(api)


class TestValidateEnv:
    """Test validate_env function."""

    def test_returns_warning_if_token_missing(self, monkeypatch):
        """Returns warning when GITHUB_TOKEN is missing."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        warnings = validate_env()
        assert any("GITHUB_TOKEN" in w for w in warnings)

    def test_no_warning_if_token_set(self, monkeypatch):
        """No warning for GITHUB_TOKEN when it's set."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        warnings = validate_env()
        assert not any("GITHUB_TOKEN" in w and "必須" in w for w in warnings)

    def test_strict_mode_raises_if_token_missing(self, monkeypatch):
        """Strict mode raises ValueError when GITHUB_TOKEN is missing."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with pytest.raises(ValueError, match="GITHUB_TOKEN"):
            validate_env(strict=True)

    def test_warns_for_optional_vars(self, monkeypatch):
        """Warns for optional env vars that are not set."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        monkeypatch.delenv("AI_LOUNGE_REPO_ID", raising=False)
        warnings = validate_env()
        assert any("AI_LOUNGE_REPO_ID" in w for w in warnings)
