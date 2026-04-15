"""GitHub Discussions GraphQL API wrapper."""

import os
from typing import Optional
import httpx
from pydantic import BaseModel, Field

GITHUB_API_URL = "https://api.github.com/graphql"


class DiscussionInput(BaseModel):
    """Discussion post parameters."""
    repository_id: str = Field(..., description="GitHub repository ID (not name)")
    category_id: str = Field(..., description="Discussion category ID")
    title: str = Field(..., description="Discussion title")
    body: str = Field(..., description="Discussion body content (Markdown)")
    client_mutation_id: Optional[str] = Field(None, description="Optional idempotency key")


class DiscussionResult(BaseModel):
    """Result of creating a discussion."""
    success: bool
    discussion_url: Optional[str] = None
    error: Optional[str] = None
    discussion_id: Optional[str] = None


class GitHubDiscussionsAPI:
    """GitHub Discussions API client using GraphQL."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token or not self.token.strip():
            raise ValueError("GITHUB_TOKEN環境変数が必要です")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "GraphQL-Features": "discussions_api",
        }
    
    async def create_discussion(self, input_data: DiscussionInput) -> DiscussionResult:
        """Create a new discussion post."""
        mutation = """
        mutation CreateDiscussion($input: CreateDiscussionInput!) {
            createDiscussion(input: $input) {
                discussion {
                    id
                    url
                    title
                }
            }
        }
        """
        
        variables = {
            "input": {
                "repositoryId": input_data.repository_id,
                "categoryId": input_data.category_id,
                "title": input_data.title,
                "body": input_data.body,
            }
        }
        if input_data.client_mutation_id:
            variables["input"]["clientMutationId"] = input_data.client_mutation_id
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    GITHUB_API_URL,
                    headers=self.headers,
                    json={"query": mutation, "variables": variables}
                )
                response.raise_for_status()
                data = response.json()
                
                if "errors" in data:
                    return DiscussionResult(
                        success=False,
                        error=str(data["errors"])
                    )
                
                discussion = data["data"]["createDiscussion"]["discussion"]
                return DiscussionResult(
                    success=True,
                    discussion_url=discussion["url"],
                    discussion_id=discussion["id"]
                )
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    error_msg = "認証エラー: GitHubトークンが無効または期限切れです"
                elif e.response.status_code == 403:
                    error_msg = "権限エラー: トークンに 'repo' と 'write:discussion' 権限が必要です"
                else:
                    error_msg = f"HTTPエラー (ステータスコード: {e.response.status_code}): {e.response.text}"
                return DiscussionResult(
                    success=False,
                    error=error_msg
                )
            except httpx.RequestError as e:
                return DiscussionResult(
                    success=False,
                    error=f"リクエストエラー: {str(e)}"
                )
            except httpx.HTTPError as e:
                return DiscussionResult(
                    success=False,
                    error=f"HTTPエラー: {str(e)}"
                )
    
    async def get_repository_id(self, owner: str, repo: str) -> Optional[str]:
        """Get repository ID from owner/name."""
        query = """
        query GetRepoId($owner: String!, $name: String!) {
            repository(owner: $owner, name: $name) {
                id
            }
        }
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    GITHUB_API_URL,
                    headers=self.headers,
                    json={"query": query, "variables": {"owner": owner, "name": repo}}
                )
                response.raise_for_status()
                data = response.json()
                if "data" in data and data["data"]["repository"]:
                    return data["data"]["repository"]["id"]
            except httpx.HTTPError:
                return None
        return None
    
    async def get_categories(self, owner: str, repo: str) -> list[dict]:
        """Get discussion categories for a repository."""
        query = """
        query GetCategories($owner: String!, $name: String!) {
            repository(owner: $owner, name: $name) {
                discussionCategories(first: 20) {
                    nodes {
                        id
                        name
                        emoji
                        description
                    }
                }
            }
        }
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    GITHUB_API_URL,
                    headers=self.headers,
                    json={"query": query, "variables": {"owner": owner, "name": repo}}
                )
                response.raise_for_status()
                data = response.json()
                if "data" in data and data["data"]["repository"]:
                    return data["data"]["repository"]["discussionCategories"]["nodes"] or []
            except httpx.HTTPError:
                return []
        return []
