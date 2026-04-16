"""GitHub Discussions GraphQL API ラッパー。

GitHub の GraphQL API を使用して、ディスカッションの作成・取得を行います。
"""

import os
from typing import Optional
import httpx
from pydantic import BaseModel, Field

# GitHub GraphQL API エンドポイント
GITHUB_API_URL = "https://api.github.com/graphql"


# ============================================================================
# データモデル
# ============================================================================

class DiscussionInput(BaseModel):
    """ディスカッション投稿のパラメータ。

    Attributes:
        repository_id: GitHub リポジトリ ID（名前ではなく ID）
        category_id: ディスカッションカテゴリ ID
        title: ディスカッションタイトル
        body: 投稿内容（Markdown 形式）
        client_mutation_id: オプションの冪等性キー
    """
    repository_id: str = Field(..., description="GitHub リポジトリ ID（名前ではなく ID）")
    category_id: str = Field(..., description="ディスカッションカテゴリ ID")
    title: str = Field(..., description="ディスカッションタイトル")
    body: str = Field(..., description="投稿内容（Markdown 形式）")
    client_mutation_id: Optional[str] = Field(None, description="オプションの冪等性キー")


class DiscussionResult(BaseModel):
    """ディスカッション作成の結果。

    Attributes:
        success: 成功した場合 True
        discussion_url: 作成されたディスカッションの URL（成功時）
        error: エラーメッセージ（失敗時）
        discussion_id: 作成されたディスカッションの ID（成功時）
    """
    success: bool
    discussion_url: Optional[str] = None
    error: Optional[str] = None
    discussion_id: Optional[str] = None


# ============================================================================
# API クライアント
# ============================================================================

class GitHubDiscussionsAPI:
    """GitHub Discussions API クライアント（GraphQL 使用）。

    GitHub の Personal Access Token を使用して、
    Discussions API にアクセスします。

    必要なスコープ：
    - repo: プライベートリポジトリへのアクセス（必要な場合）
    - write:discussion: ディスカッションの作成・編集
    """

    def __init__(self, token: Optional[str] = None):
        """API クライアントを初期化する。

        Args:
            token: GitHub Personal Access Token。
                   None の場合は GITHUB_TOKEN 環境変数から読み込み。

        Raises:
            ValueError: トークンが提供されていない場合
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token or not self.token.strip():
            raise ValueError("GITHUB_TOKEN 環境変数が必要です")

        # API リクエストヘッダー
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "GraphQL-Features": "discussions_api",
        }

    async def create_discussion(self, input_data: DiscussionInput) -> DiscussionResult:
        """新しいディスカッションを作成する。

        GraphQL ミューテーションを使用して、指定されたリポジトリに
        ディスカッションを作成します。

        Args:
            input_data: 投稿パラメータを含む DiscussionInput オブジェクト

        Returns:
            作成結果を含む DiscussionResult オブジェクト
        """
        # GraphQL ミューテーション
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

        # 変数設定
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

        # API リクエスト送信
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    GITHUB_API_URL,
                    headers=self.headers,
                    json={"query": mutation, "variables": variables}
                )
                response.raise_for_status()
                data = response.json()

                # GraphQL エラーのチェック
                if "errors" in data:
                    return DiscussionResult(
                        success=False,
                        error=str(data["errors"])
                    )

                # 成功レスポンスの処理
                discussion = data["data"]["createDiscussion"]["discussion"]
                return DiscussionResult(
                    success=True,
                    discussion_url=discussion["url"],
                    discussion_id=discussion["id"]
                )

            except httpx.HTTPStatusError as e:
                # ステータスコードに基づくエラーメッセージ
                if e.response.status_code == 401:
                    error_msg = "認証エラー：GitHub トークンが無効または期限切れです"
                elif e.response.status_code == 403:
                    error_msg = "権限エラー：トークンに 'repo' と 'write:discussion' 権限が必要です"
                else:
                    error_msg = f"HTTP エラー (ステータスコード：{e.response.status_code}): {e.response.text}"
                return DiscussionResult(
                    success=False,
                    error=error_msg
                )
            except httpx.RequestError as e:
                return DiscussionResult(
                    success=False,
                    error=f"リクエストエラー：{str(e)}"
                )
            except httpx.HTTPError as e:
                return DiscussionResult(
                    success=False,
                    error=f"HTTP エラー：{str(e)}"
                )

    async def get_repository_id(self, owner: str, repo: str) -> Optional[str]:
        """オーナー/リポジトリ名からリポジトリ ID を取得する。

        GraphQL クエリを使用して、指定されたリポジトリの ID を取得します。
        リポジトリ ID は GraphQL API でノードを特定するために必要です。

        Args:
            owner: GitHub オーナー名（ユーザー名または組織名）
            repo: リポジトリ名

        Returns:
            リポジトリ ID（例：R_kgDO...）。
            取得失敗時は None。
        """
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
        """リポジトリのディスカッションカテゴリを取得する。

        指定されたリポジトリで利用可能なディスカッションカテゴリ
        （General, Ideas, Q&A, Show and tell 等）を一覧取得します。

        Args:
            owner: GitHub オーナー名（ユーザー名または組織名）
            repo: リポジトリ名

        Returns:
            カテゴリ情報の辞書リスト。
            各辞書は 'id', 'name', 'emoji', 'description' キーを含む。
            取得失敗時は空リスト。
        """
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
