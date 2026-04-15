"""Shared test fixtures for all test modules."""

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


@pytest.fixture
def mock_create_discussion_success():
    """Mock response for successful discussion creation."""
    return {
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


@pytest.fixture
def mock_create_discussion_api_error():
    """Mock response for API error during discussion creation."""
    return {
        "errors": [{"message": "Something went wrong"}]
    }


@pytest.fixture
def mock_get_repository_id():
    """Mock response for repository ID lookup."""
    return {
        "data": {
            "repository": {
                "id": "R_test_repo"
            }
        }
    }


@pytest.fixture
def mock_get_categories():
    """Mock response for discussion categories."""
    return {
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
                        {
                            "id": "DIC_ideas",
                            "name": "ideas",
                            "emoji": "💡",
                            "description": "Ideas and suggestions",
                        },
                        {
                            "id": "DIC_qa",
                            "name": "q-a",
                            "emoji": "❓",
                            "description": "Questions and answers",
                        },
                        {
                            "id": "DIC_show",
                            "name": "show-and-tell",
                            "emoji": "🎉",
                            "description": "Show off your projects",
                        },
                    ]
                }
            }
        }
    }


@pytest.fixture
def mock_all_api_success(respx_mock, mock_get_repository_id, mock_get_categories,
                          mock_create_discussion_success):
    """Mock all API endpoints to success."""
    respx_mock.post("https://api.github.com/graphql").mock(
        side_effect=[
            Response(200, json=mock_get_repository_id),
            Response(200, json=mock_get_categories),
            Response(200, json=mock_create_discussion_success),
        ]
    )
