"""ユーティリティ関数のテスト。"""

import os
import pytest
import respx
from httpx import Response

from github_discuss_mcp.utils import (
    get_category_id_from_env,
    resolve_category_id,
    get_repo_id_cached,
    validate_env,
    CATEGORY_ENV_VARS,
    DEFAULT_OWNER,
    DEFAULT_REPO,
)
from github_discuss_mcp.github_api import GitHubDiscussionsAPI


class TestGetCategoryIdFromEnv:
    """get_category_id_from_env 関数のテスト。"""

    def test_returns_env_value_primary(self, monkeypatch):
        """汎用名環境変数からカテゴリ ID を返す。"""
        monkeypatch.setenv("GITHUB_DISCUSS_CATEGORY_GENERAL", "DIC_general")
        assert get_category_id_from_env("general") == "DIC_general"

    def test_returns_env_value_fallback(self, monkeypatch):
        """後方互換名環境変数からカテゴリ ID を返す。"""
        monkeypatch.delenv("GITHUB_DISCUSS_CATEGORY_GENERAL", raising=False)
        monkeypatch.setenv("AI_LOUNGE_CATEGORY_GENERAL", "DIC_general")
        assert get_category_id_from_env("general") == "DIC_general"

    def test_primary_takes_precedence(self, monkeypatch):
        """汎用名が後方互換名より優先される。"""
        monkeypatch.setenv("GITHUB_DISCUSS_CATEGORY_GENERAL", "DIC_primary")
        monkeypatch.setenv("AI_LOUNGE_CATEGORY_GENERAL", "DIC_fallback")
        assert get_category_id_from_env("general") == "DIC_primary"

    def test_returns_none_if_not_set(self, monkeypatch):
        """環境変数が設定されていない場合は None を返す。"""
        monkeypatch.delenv("GITHUB_DISCUSS_CATEGORY_GENERAL", raising=False)
        monkeypatch.delenv("AI_LOUNGE_CATEGORY_GENERAL", raising=False)
        assert get_category_id_from_env("general") is None

    def test_returns_none_for_unknown_category(self):
        """未知のカテゴリの場合は None を返す。"""
        assert get_category_id_from_env("unknown") is None


class TestResolveCategoryId:
    """resolve_category_id 関数のテスト。"""

    @pytest.mark.asyncio
    async def test_returns_env_value_if_set(self, mock_token, monkeypatch):
        """環境変数が設定されていれば API を呼ばずに返す。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.setenv("GITHUB_DISCUSS_CATEGORY_GENERAL", "DIC_general")

        api = GitHubDiscussionsAPI(token=mock_token)
        result = await resolve_category_id(api, "general")
        assert result == "DIC_general"

    @pytest.mark.asyncio
    @respx.mock
    async def test_falls_back_to_api_if_env_empty(self, mock_token, monkeypatch):
        """環境変数が空の場合 API にフォールバックする。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.delenv("GITHUB_DISCUSS_CATEGORY_GENERAL", raising=False)
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
    async def test_uses_custom_owner_repo(self, mock_token, monkeypatch):
        """カスタムオーナー・リポジトリ名を使用する。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.delenv("GITHUB_DISCUSS_CATEGORY_GENERAL", raising=False)
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

        route = respx.post("https://api.github.com/graphql")
        route.mock(return_value=Response(200, json=mock_categories))

        api = GitHubDiscussionsAPI(token=mock_token)
        result = await resolve_category_id(
            api,
            "general",
            repo_owner="custom-owner",
            repo_name="custom-repo",
        )
        assert result == "DIC_general"

        # カスタムオーナー・リポジトリで API が呼ばれたことを確認
        assert route.called

    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_none_if_not_found(self, mock_token, monkeypatch):
        """環境変数にも API にも見つからない場合は None を返す。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        for primary, fallback in CATEGORY_ENV_VARS.values():
            monkeypatch.delenv(primary, raising=False)
            monkeypatch.delenv(fallback, raising=False)

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json={
                "data": {"repository": {"discussionCategories": {"nodes": []}}}
            })
        )

        api = GitHubDiscussionsAPI(token=mock_token)
        result = await resolve_category_id(api, "general")
        assert result is None


class TestGetRepoIdCached:
    """get_repo_id_cached 関数のテスト。"""

    @pytest.mark.asyncio
    async def test_returns_env_value_if_set(self, mock_token, monkeypatch):
        """環境変数が設定されていれば API を呼ばずに返す。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.setenv("GITHUB_DISCUSS_REPO_ID", "R_test_repo")

        api = GitHubDiscussionsAPI(token=mock_token)
        result = await get_repo_id_cached(api)
        assert result == "R_test_repo"

    @pytest.mark.asyncio
    async def test_returns_fallback_env_value(self, mock_token, monkeypatch):
        """後方互換環境変数から値を返す。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.delenv("GITHUB_DISCUSS_REPO_ID", raising=False)
        monkeypatch.setenv("AI_LOUNGE_REPO_ID", "R_test_repo")

        api = GitHubDiscussionsAPI(token=mock_token)
        result = await get_repo_id_cached(api)
        assert result == "R_test_repo"

    @pytest.mark.asyncio
    @respx.mock
    async def test_falls_back_to_api_if_env_empty(self, mock_token, monkeypatch):
        """環境変数が設定されていない場合 API にフォールバックする。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.delenv("GITHUB_DISCUSS_REPO_ID", raising=False)
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
    async def test_uses_custom_owner_repo(self, mock_token, monkeypatch):
        """カスタムオーナー・リポジトリ名を使用する。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.delenv("GITHUB_DISCUSS_REPO_ID", raising=False)
        monkeypatch.delenv("AI_LOUNGE_REPO_ID", raising=False)

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json={
                "data": {"repository": {"id": "R_test_repo"}}
            })
        )

        api = GitHubDiscussionsAPI(token=mock_token)
        result = await get_repo_id_cached(
            api,
            owner="custom-owner",
            repo="custom-repo",
        )
        assert result == "R_test_repo"

    @pytest.mark.asyncio
    @respx.mock
    async def test_raises_if_api_fails(self, mock_token, monkeypatch):
        """API がリポジトリ ID を返せない場合 ValueError を発生する。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.delenv("GITHUB_DISCUSS_REPO_ID", raising=False)
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
    """validate_env 関数のテスト。"""

    def test_returns_warning_if_token_missing(self, monkeypatch):
        """GITHUB_TOKEN が缺失している場合警告を返す。"""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        warnings = validate_env()
        assert any("GITHUB_TOKEN" in w for w in warnings)

    def test_no_warning_if_token_set(self, monkeypatch):
        """GITHUB_TOKEN が設定されていれば警告を返さない。"""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        warnings = validate_env()
        assert not any("GITHUB_TOKEN" in w and "必須" in w for w in warnings)

    def test_strict_mode_raises_if_token_missing(self, monkeypatch):
        """strict モードで GITHUB_TOKEN が缺失している場合 ValueError を発生する。"""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with pytest.raises(ValueError, match="GITHUB_TOKEN"):
            validate_env(strict=True)

    def test_warns_for_optional_vars(self, monkeypatch):
        """設定されていない任意環境変数に対して警告を出す。"""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
        monkeypatch.delenv("GITHUB_DISCUSS_REPO_ID", raising=False)
        monkeypatch.delenv("AI_LOUNGE_REPO_ID", raising=False)
        warnings = validate_env()
        # どちらかの環境変数に関する警告が含まれることを確認
        assert any("REPO_ID" in w for w in warnings)
