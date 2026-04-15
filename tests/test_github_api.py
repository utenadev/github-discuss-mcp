"""Tests for GitHub Discussions API wrapper."""

import pytest
import respx
from httpx import Response

from ai_lounge_mcp.github_api import (
    GitHubDiscussionsAPI,
    DiscussionInput,
    DiscussionResult,
)


@pytest.fixture
def mock_token():
    """Mock GitHub token for testing."""
    return "ghp_test_token_12345"


@pytest.fixture
def api(mock_token):
    """Create API instance with mock token."""
    return GitHubDiscussionsAPI(token=mock_token)


@pytest.fixture
def discussion_input():
    """Create sample discussion input."""
    return DiscussionInput(
        repository_id="R_test_repo",
        category_id="DIC_test_category",
        title="Test Discussion",
        body="This is a test discussion body.",
    )


class TestGitHubDiscussionsAPI:
    """Test GitHubDiscussionsAPI class."""

    def test_init_with_token(self, mock_token):
        """Test initialization with explicit token."""
        api = GitHubDiscussionsAPI(token=mock_token)
        assert api.token == mock_token
        assert api.headers["Authorization"] == f"Bearer {mock_token}"

    def test_init_without_token_raises_error(self, monkeypatch):
        """Test initialization fails without token."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with pytest.raises(ValueError, match="GITHUB_TOKEN環境変数が必要です"):
            GitHubDiscussionsAPI()

    def test_init_with_env_variable(self, mock_token, monkeypatch):
        """Test initialization with environment variable."""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        api = GitHubDiscussionsAPI()
        assert api.token == mock_token

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_discussion_success(self, api, discussion_input):
        """Test successful discussion creation."""
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
        """Test discussion creation with client mutation ID."""
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
        """Test handling of API errors."""
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
        """Test handling of HTTP errors."""
        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(500, json={"message": "Internal Server Error"})
        )

        result = await api.create_discussion(discussion_input)

        assert result.success is False
        assert "HTTPエラー" in result.error

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_repository_id_success(self, api):
        """Test successful repository ID retrieval."""
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
        """Test repository ID retrieval when not found."""
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
        """Test repository ID retrieval on HTTP error."""
        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(500)
        )

        repo_id = await api.get_repository_id("test-owner", "test-repo")

        assert repo_id is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_categories_success(self, api):
        """Test successful category retrieval."""
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
        """Test category retrieval with no categories."""
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
        """Test category retrieval on HTTP error."""
        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(500)
        )

        categories = await api.get_categories("test-owner", "test-repo")

        assert categories == []

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_categories_null_nodes(self, api):
        """Test category retrieval when nodes is null."""
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
    """Test DiscussionInput model."""

    def test_create_discussion_input(self):
        """Test creating DiscussionInput."""
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
        """Test creating DiscussionInput with client mutation ID."""
        input_data = DiscussionInput(
            repository_id="R_test",
            category_id="DIC_test",
            title="Test Title",
            body="Test Body",
            client_mutation_id="mutation_123",
        )
        assert input_data.client_mutation_id == "mutation_123"


class TestDiscussionResult:
    """Test DiscussionResult model."""

    def test_create_success_result(self):
        """Test creating successful DiscussionResult."""
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
        """Test creating error DiscussionResult."""
        result = DiscussionResult(
            success=False,
            error="Test error message",
        )
        assert result.success is False
        assert result.error == "Test error message"
        assert result.discussion_url is None
        assert result.discussion_id is None
