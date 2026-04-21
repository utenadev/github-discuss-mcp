"""GitHub Discussions API ラッパーのテスト。"""

import pytest
import respx
from httpx import Response

from github_discuss.github_api import (
    GitHubDiscussionsAPI,
    DiscussionInput,
    DiscussionResult,
)


class TestGitHubDiscussionsAPI:
    """GitHubDiscussionsAPI クラスのテスト。"""

    def test_init_with_token(self, mock_token):
        """明示的なトークンでの初期化テスト。"""
        api = GitHubDiscussionsAPI(token=mock_token)
        assert api.token == mock_token
        assert api.headers["Authorization"] == f"Bearer {mock_token}"

    def test_init_without_token_raises_error(self, monkeypatch):
        """トークンなしで初期化した場合エラーになるテスト。"""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with pytest.raises(ValueError, match="GITHUB_TOKEN 環境変数が必要です"):
            GitHubDiscussionsAPI()

    def test_init_with_env_variable(self, mock_token, monkeypatch):
        """環境変数での初期化テスト。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        api = GitHubDiscussionsAPI()
        assert api.token == mock_token

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_discussion_success(self, api, discussion_input):
        """ディスカッション作成成功のテスト。"""
        mock_response = {
            "data": {
                "createDiscussion": {
                    "discussion": {
                        "id": "D_test_discussion",
                        "url": "https://github.com/test/repo/discussions/1",
                        "title": "Test Discussion",
                    }
                }
            }
        }

        route = respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_response)
        )

        result = await api.create_discussion(discussion_input)

        assert result.success is True
        assert result.discussion_url == "https://github.com/test/repo/discussions/1"
        assert result.discussion_id == "D_test_discussion"
        assert result.error is None
        assert route.called

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_discussion_with_client_mutation_id(self, api):
        """client_mutation_id 付きディスカッション作成テスト。"""
        discussion_input = DiscussionInput(
            repository_id="R_test_repo",
            category_id="DIC_test_category",
            title="Test Discussion",
            body="Test body",
            client_mutation_id="mutation_123",
        )

        mock_response = {
            "data": {
                "createDiscussion": {
                    "discussion": {
                        "id": "D_test_discussion",
                        "url": "https://github.com/test/repo/discussions/1",
                        "title": "Test Discussion",
                    }
                }
            }
        }

        route = respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_response)
        )

        result = await api.create_discussion(discussion_input)

        assert result.success is True
        assert route.called

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_discussion_api_error(self, api, discussion_input):
        """API エラー処理のテスト。"""
        mock_response = {
            "errors": [{"message": "Something went wrong"}]
        }

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_response)
        )

        result = await api.create_discussion(discussion_input)

        assert result.success is False
        assert "Something went wrong" in result.error

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_discussion_http_error(self, api, discussion_input):
        """HTTP エラー処理のテスト。"""
        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(500, json={"message": "Internal Server Error"})
        )

        result = await api.create_discussion(discussion_input)

        assert result.success is False
        assert "HTTP エラー" in result.error

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_repository_id_success(self, api):
        """リポジトリ ID 取得成功のテスト。"""
        mock_response = {
            "data": {
                "repository": {
                    "id": "R_test_repo"
                }
            }
        }

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_response)
        )

        repo_id = await api.get_repository_id("test-owner", "test-repo")

        assert repo_id == "R_test_repo"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_repository_id_not_found(self, api):
        """リポジトリ ID が存在しない場合のテスト。"""
        mock_response = {
            "data": {
                "repository": None
            }
        }

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_response)
        )

        repo_id = await api.get_repository_id("test-owner", "test-repo")

        assert repo_id is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_repository_id_http_error(self, api):
        """HTTP エラー発生時のリポジトリ ID 取得テスト。"""
        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(500)
        )

        repo_id = await api.get_repository_id("test-owner", "test-repo")

        assert repo_id is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_categories_success(self, api):
        """カテゴリ取得成功のテスト。"""
        mock_response = {
            "data": {
                "repository": {
                    "discussionCategories": {
                        "nodes": [
                            {
                                "id": "DIC_cat1",
                                "name": "general",
                                "emoji": "💬",
                                "description": "General discussion",
                            },
                            {
                                "id": "DIC_cat2",
                                "name": "ideas",
                                "emoji": "💡",
                                "description": "Ideas and suggestions",
                            },
                        ]
                    }
                }
            }
        }

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_response)
        )

        categories = await api.get_categories("test-owner", "test-repo")

        assert len(categories) == 2
        assert categories[0]["name"] == "general"
        assert categories[1]["name"] == "ideas"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_categories_empty(self, api):
        """カテゴリ空リスト取得のテスト。"""
        mock_response = {
            "data": {
                "repository": {
                    "discussionCategories": {
                        "nodes": []
                    }
                }
            }
        }

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_response)
        )

        categories = await api.get_categories("test-owner", "test-repo")

        assert categories == []

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_categories_http_error(self, api):
        """HTTP エラー発生時のカテゴリ取得テスト。"""
        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(500)
        )

        categories = await api.get_categories("test-owner", "test-repo")

        assert categories == []

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_categories_null_nodes(self, api):
        """nodes が null の場合のカテゴリ取得テスト。"""
        mock_response = {
            "data": {
                "repository": {
                    "discussionCategories": {
                        "nodes": None
                    }
                }
            }
        }

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_response)
        )

        categories = await api.get_categories("test-owner", "test-repo")

        assert categories == []


class TestDiscussionInput:
    """DiscussionInput モデルのテスト。"""

    def test_create_discussion_input(self):
        """DiscussionInput 生成テスト。"""
        input_data = DiscussionInput(
            repository_id="R_test",
            category_id="DIC_test",
            title="Test Title",
            body="Test Body",
        )
        assert input_data.repository_id == "R_test"
        assert input_data.category_id == "DIC_test"
        assert input_data.title == "Test Title"
        assert input_data.body == "Test Body"
        assert input_data.client_mutation_id is None

    def test_create_discussion_input_with_mutation_id(self):
        """client_mutation_id 付き DiscussionInput 生成テスト。"""
        input_data = DiscussionInput(
            repository_id="R_test",
            category_id="DIC_test",
            title="Test Title",
            body="Test Body",
            client_mutation_id="mutation_123",
        )
        assert input_data.client_mutation_id == "mutation_123"


class TestDiscussionResult:
    """DiscussionResult モデルのテスト。"""

    def test_create_success_result(self):
        """成功 DiscussionResult 生成テスト。"""
        result = DiscussionResult(
            success=True,
            discussion_url="https://github.com/test/repo/discussions/1",
            discussion_id="D_test",
        )
        assert result.success is True
        assert result.discussion_url == "https://github.com/test/repo/discussions/1"
        assert result.discussion_id == "D_test"
        assert result.error is None

    def test_create_error_result(self):
        """エラー DiscussionResult 生成テスト。"""
        result = DiscussionResult(
            success=False,
            error="Test error message",
        )
        assert result.success is False
        assert result.error == "Test error message"
        assert result.discussion_url is None
        assert result.discussion_id is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_discussions_success(self, api):
        """ディスカッション一覧取得成功のテスト。"""
        mock_response = {
            "data": {
                "repository": {
                    "discussions": {
                        "nodes": [
                            {
                                "id": "D_test_1",
                                "title": "Test Discussion 1",
                                "body": "Test body 1",
                                "url": "https://github.com/test/repo/discussions/1",
                                "createdAt": "2024-01-01T00:00:00Z",
                                "author": {"login": "user1"},
                                "category": {"name": "general"},
                            },
                            {
                                "id": "D_test_2",
                                "title": "Test Discussion 2",
                                "body": "Test body 2",
                                "url": "https://github.com/test/repo/discussions/2",
                                "createdAt": "2024-01-02T00:00:00Z",
                                "author": {"login": "user2"},
                                "category": {"name": "ideas"},
                            },
                        ]
                    }
                }
            }
        }

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_response)
        )

        discussions = await api.get_discussions("test-owner", "test-repo")

        assert len(discussions) == 2
        assert discussions[0]["title"] == "Test Discussion 1"
        assert discussions[1]["title"] == "Test Discussion 2"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_discussions_empty(self, api):
        """ディスカッション一覧取得で結果が空のテスト。"""
        mock_response = {
            "data": {
                "repository": {
                    "discussions": {
                        "nodes": []
                    }
                }
            }
        }

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_response)
        )

        discussions = await api.get_discussions("test-owner", "test-repo")

        assert discussions == []

    @pytest.mark.asyncio
    @respx.mock
    async def test_add_comment_success(self, api):
        """コメント追加成功のテスト。"""
        mock_response = {
            "data": {
                "addDiscussionComment": {
                    "comment": {
                        "id": "C_test_comment",
                        "body": "Test comment body",
                        "createdAt": "2024-01-01T00:00:00Z",
                    }
                }
            }
        }

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_response)
        )

        result = await api.add_comment("D_test_discussion", "Test comment body")

        assert result["success"] is True
        assert result["comment_id"] == "C_test_comment"
        assert result["body"] == "Test comment body"

    @pytest.mark.asyncio
    @respx.mock
    async def test_add_comment_api_error(self, api):
        """コメント追加で API エラーのテスト。"""
        mock_response = {
            "errors": [{"message": "Something went wrong"}]
        }

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_response)
        )

        result = await api.add_comment("D_test_discussion", "Test comment")

        assert result["success"] is False
        assert "Something went wrong" in result["error"]

    @pytest.mark.asyncio
    @respx.mock
    async def test_add_comment_http_error(self, api):
        """コメント追加で HTTP エラーのテスト。"""
        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(500, json={"message": "Internal Server Error"})
        )

        result = await api.add_comment("D_test_discussion", "Test comment")

        assert result["success"] is False
        assert "HTTP エラー" in result["error"]
