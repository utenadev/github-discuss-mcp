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

    async def get_discussions(
        self, owner: str, repo: str, category_id: Optional[str] = None
    ) -> list[dict]:
        """リポジトリのディスカッション一覧を取得する。

        指定されたリポジトリの最新のディスカッションを取得します。
        カテゴリ ID を指定することでフィルタリングも可能です。

        Args:
            owner: GitHub オーナー名
            repo: リポジトリ名
            category_id: カテゴリ ID（オプション）

        Returns:
            ディスカッション情報のリスト。
        """
        query = """
        query GetDiscussions($owner: String!, $name: String!, $categoryId: ID) {
            repository(owner: $owner, name: $name) {
                discussions(first: 10, categoryId: $categoryId, orderBy: {field: CREATED_AT, direction: DESC}) {
                    nodes {
                        id
                        number
                        title
                        body
                        url
                        createdAt
                        author {
                            login
                        }
                        category {
                            name
                        }
                    }
                }
            }
        }
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                variables = {"owner": owner, "name": repo, "categoryId": category_id}
                response = await client.post(
                    GITHUB_API_URL,
                    headers=self.headers,
                    json={"query": query, "variables": variables},
                )
                response.raise_for_status()
                data = response.json()
                if "data" in data and data["data"]["repository"]:
                    discussions = data["data"]["repository"]["discussions"]["nodes"] or []
                    # number を追加（URL からの検索用）
                    for d in discussions:
                        d["number"] = d.get("number")
                    return discussions
            except httpx.HTTPError:
                return []
        return []

    async def get_discussion_details(
        self, owner: str, repo: str, number: int
    ) -> Optional[dict]:
        """ディスカッションの詳細（コメントの階層構造を含む）を取得する。

        ディスカッション本文と、すべてのコメント（ネストされた返信を含む）
        を取得します。

        Args:
            owner: GitHub オーナー名
            repo: リポジトリ名
            number: ディスカッション番号

        Returns:
            ディスカッション詳細情報。見つからない場合は None。
        """
        query = """
        query GetDiscussionDetails($owner: String!, $name: String!, $number: Int!) {
            repository(owner: $owner, name: $name) {
                discussion(number: $number) {
                    id
                    number
                    title
                    body
                    url
                    createdAt
                    updatedAt
                    author {
                        login
                    }
                    category {
                        name
                    }
                    comments(first: 100) {
                        nodes {
                            id
                            body
                            createdAt
                            updatedAt
                            author {
                                login
                            }
                            replies(first: 50) {
                                nodes {
                                    id
                                    body
                                    createdAt
                                    author {
                                        login
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                variables = {"owner": owner, "name": repo, "number": number}
                response = await client.post(
                    GITHUB_API_URL,
                    headers=self.headers,
                    json={"query": query, "variables": variables},
                )
                response.raise_for_status()
                data = response.json()
                if "data" in data and data["data"]["repository"]:
                    return data["data"]["repository"]["discussion"]
            except httpx.HTTPError:
                return None
        return None

    async def get_discussion_by_number(self, owner: str, repo: str, number: int) -> Optional[dict]:
        """ディスカッション番号からディスカッション情報を取得する。

        指定されたリポジトリのディスカッション番号から、
        ディスカッションの詳細情報を取得します。

        Args:
            owner: GitHub オーナー名
            repo: リポジトリ名
            number: ディスカッション番号

        Returns:
            ディスカッション情報の辞書。
            取得失敗時は None。
        """
        query = """
        query GetDiscussionByNumber($owner: String!, $name: String!, $number: Int!) {
            repository(owner: $owner, name: $name) {
                discussion(number: $number) {
                    id
                    title
                    body
                    url
                    createdAt
                    author {
                        login
                    }
                    category {
                        name
                    }
                    comments(first: 50) {
                        nodes {
                            id
                            body
                            createdAt
                            author {
                                login
                            }
                            replies(first: 50) {
                                nodes {
                                    id
                                    body
                                    createdAt
                                    author {
                                        login
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                variables = {"owner": owner, "name": repo, "number": number}
                response = await client.post(
                    GITHUB_API_URL,
                    headers=self.headers,
                    json={"query": query, "variables": variables},
                )
                response.raise_for_status()
                data = response.json()
                if "data" in data and data["data"]["repository"]:
                    return data["data"]["repository"]["discussion"]
            except httpx.HTTPError:
                return None
        return None

    async def add_comment(self, discussion_id: str, body: str, reply_to_id: Optional[str] = None) -> dict:
        """ディスカッションにコメント（返信）を追加する。

        既存のディスカッションにコメント、または既存のコメントに返信を追加します。

        Args:
            discussion_id: ディスカッション ID（node ID）
            body: コメント本文（Markdown 形式）
            reply_to_id: 返信先のコメント ID（オプション）

        Returns:
            結果を含む辞書。
        """
        # Discussion へのコメントには addDiscussionComment を使用
        mutation = """
        mutation AddDiscussionComment($input: AddDiscussionCommentInput!) {
            addDiscussionComment(input: $input) {
                comment {
                    id
                    body
                    createdAt
                }
            }
        }
        """

        variables = {
            "input": {
                "discussionId": discussion_id,
                "body": body,
            }
        }
        if reply_to_id:
            variables["input"]["replyToId"] = reply_to_id

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    GITHUB_API_URL,
                    headers=self.headers,
                    json={"query": mutation, "variables": variables},
                )
                response.raise_for_status()
                data = response.json()

                if "errors" in data:
                    return {"success": False, "error": str(data["errors"])}

                # commentEdge または comment のどちらかをサポート
                comment_data = data["data"]["addDiscussionComment"]
                if "commentEdge" in comment_data:
                    comment = comment_data["commentEdge"]["node"]
                else:
                    comment = comment_data["comment"]
                return {
                    "success": True,
                    "comment_id": comment["id"],
                    "body": comment["body"],
                    "created_at": comment["createdAt"],
                }

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    error_msg = "認証エラー：GitHub トークンが無効または期限切れです"
                elif e.response.status_code == 403:
                    error_msg = "権限エラー：トークンに 'repo' と 'write:discussion' 権限が必要です"
                else:
                    error_msg = f"HTTP エラー (ステータスコード：{e.response.status_code}): {e.response.text}"
                return {"success": False, "error": error_msg}
            except httpx.RequestError as e:
                return {"success": False, "error": f"リクエストエラー：{str(e)}"}
            except httpx.HTTPError as e:
                return {"success": False, "error": f"HTTP エラー：{str(e)}"}

    async def update_discussion(self, discussion_id: str, title: Optional[str] = None, body: Optional[str] = None) -> dict:
        """ディスカッションを更新（編集）する。

        既存のディスカッションのタイトルまたは本文を更新します。

        Args:
            discussion_id: ディスカッション ID（node ID）
            title: 新しいタイトル（オプション）
            body: 新しい本文（オプション）

        Returns:
            結果を含む辞書。成功時は 'success': True。
        """
        mutation = """
        mutation UpdateDiscussion($input: UpdateDiscussionInput!) {
            updateDiscussion(input: $input) {
                discussion {
                    id
                    title
                    body
                    updatedAt
                }
            }
        }
        """

        variables = {"input": {"id": discussion_id}}
        if title:
            variables["input"]["title"] = title
        if body:
            variables["input"]["body"] = body

        return await self._execute_mutation(mutation, variables, "updateDiscussion")

    async def delete_discussion(self, discussion_id: str) -> dict:
        """ディスカッションを削除する。

        Args:
            discussion_id: ディスカッション ID（node ID）

        Returns:
            結果を含む辞書。成功時は 'success': True。
        """
        mutation = """
        mutation DeleteDiscussion($input: DeleteDiscussionInput!) {
            deleteDiscussion(input: $input) {
                repository { id }
            }
        }
        """

        variables = {"input": {"id": discussion_id}}
        return await self._execute_mutation(mutation, variables, "deleteDiscussion")

    async def update_comment(self, comment_id: str, body: str) -> dict:
        """コメントを更新（編集）する。

        Args:
            comment_id: コメント ID（node ID）
            body: 新しい本文（Markdown 形式）

        Returns:
            結果を含む辞書。成功時は 'success': True。
        """
        mutation = """
        mutation UpdateDiscussionComment($input: UpdateDiscussionCommentInput!) {
            updateDiscussionComment(input: $input) {
                comment {
                    id
                    body
                    updatedAt
                }
            }
        }
        """

        variables = {"input": {"id": comment_id, "body": body}}
        return await self._execute_mutation(mutation, variables, "updateDiscussionComment")

    async def delete_comment(self, comment_id: str) -> dict:
        """コメントを削除する。

        Args:
            comment_id: コメント ID（node ID）

        Returns:
            結果を含む辞書。成功時は 'success': True。
        """
        mutation = """
        mutation DeleteDiscussionComment($input: DeleteDiscussionCommentInput!) {
            deleteDiscussionComment(input: $input) {
                comment { id }
            }
        }
        """

        variables = {"input": {"id": comment_id}}
        return await self._execute_mutation(mutation, variables, "deleteDiscussionComment")

    async def mark_answer(self, comment_id: str) -> dict:
        """コメントを回答としてマークする（Q&A 機能）。

        Args:
            comment_id: コメント ID（node ID）

        Returns:
            結果を含む辞書。成功時は 'success': True。
        """
        mutation = """
        mutation MarkDiscussionCommentAsAnswer($input: MarkDiscussionCommentAsAnswerInput!) {
            markDiscussionCommentAsAnswer(input: $input) {
                comment {
                    id
                    isAnswer
                }
            }
        }
        """

        variables = {"input": {"id": comment_id}}
        return await self._execute_mutation(mutation, variables, "markDiscussionCommentAsAnswer")

    async def _execute_mutation(self, mutation: str, variables: dict, result_key: str) -> dict:
        """GraphQL ミューテーションを実行する共通ヘルパー。

        Args:
            mutation: GraphQL ミューテーション文字列
            variables: 変数辞書
            result_key: レスポンスの結果キー

        Returns:
            結果を含む辞書。
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    GITHUB_API_URL,
                    headers=self.headers,
                    json={"query": mutation, "variables": variables},
                )
                response.raise_for_status()
                data = response.json()

                if "errors" in data:
                    return {"success": False, "error": str(data["errors"])}

                return {"success": True, "data": data["data"][result_key]}

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    return {"success": False, "error": "認証エラー：GitHub トークンが無効または期限切れです"}
                elif e.response.status_code == 403:
                    return {"success": False, "error": "権限エラー：トークンに 'repo' と 'write:discussion' 権限が必要です"}
                else:
                    return {"success": False, "error": f"HTTP エラー：{e.response.status_code}"}
            except httpx.RequestError as e:
                return {"success": False, "error": f"リクエストエラー：{str(e)}"}
            except httpx.HTTPError as e:
                return {"success": False, "error": f"HTTP エラー：{str(e)}"}
