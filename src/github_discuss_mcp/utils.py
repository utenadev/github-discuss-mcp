"""GitHub Discussions へのアクセスに関する共通ユーティリティモジュール。

CLI および MCP サーバーで共有される機能を提供します：
- カテゴリ ID の解決（環境変数優先、 fallback として API 取得）
- リポジトリ ID の取得（環境変数優先、fallback として API 取得）
- 環境変数の検証
"""

import os
import warnings
from typing import Optional

from .github_api import GitHubDiscussionsAPI

# ============================================================================
# デフォルト設定
# ============================================================================

# GitHub Discussions のデフォルトオーナー・リポジトリ名
# 環境変数で上書き可能
DEFAULT_OWNER = "lifemate-ai"
DEFAULT_REPO = "ai-lounge"

# カテゴリ名の環境変数マップ
# 汎用名を主に使用し、後方互換のために ai_lounge 名義も残す
CATEGORY_ENV_VARS = {
    "general": ("GITHUB_DISCUSS_CATEGORY_GENERAL", "AI_LOUNGE_CATEGORY_GENERAL"),
    "ideas": ("GITHUB_DISCUSS_CATEGORY_IDEAS", "AI_LOUNGE_CATEGORY_IDEAS"),
    "q-a": ("GITHUB_DISCUSS_CATEGORY_QA", "AI_LOUNGE_CATEGORY_QA"),
    "show-and-tell": ("GITHUB_DISCUSS_CATEGORY_SHOW", "AI_LOUNGE_CATEGORY_SHOW"),
}

# 必須環境変数
REQUIRED_ENV_VARS = ["GITHUB_TOKEN"]

# オプショナル環境変数（警告のみ）
OPTIONAL_ENV_VARS = ["GITHUB_DISCUSS_REPO_ID", "AI_LOUNGE_REPO_ID"]


def get_category_id_from_env(category: str) -> Optional[str]:
    """環境変数からカテゴリ ID を取得する。

    汎用名（GITHUB_DISCUSS_CATEGORY_*）を先に確認し、
    見つからない場合は後方互換名（AI_LOUNGE_CATEGORY_*）を確認する。

    Args:
        category: カテゴリ名（'general', 'ideas', 'q-a', 'show-and-tell'）

    Returns:
        環境変数に設定されたカテゴリ ID、見つからない場合は None
    """
    if category not in CATEGORY_ENV_VARS:
        return None

    primary_var, fallback_var = CATEGORY_ENV_VARS[category]

    # 汎用名を先に確認
    value = os.getenv(primary_var, "")
    if value:
        return value

    # 後方互換名を確認
    value = os.getenv(fallback_var, "")
    if value:
        return value

    return None


async def resolve_category_id(
    api: GitHubDiscussionsAPI,
    category_name: str,
    repo_owner: Optional[str] = None,
    repo_name: Optional[str] = None,
) -> Optional[str]:
    """カテゴリ名から ID を解決する。

    以下の優先順位で ID を解決します：
    1. 環境変数（汎用名優先、後方互換名 fallback）
    2. GitHub API による動的取得

    Args:
        api: GitHubDiscussionsAPI のインスタンス
        category_name: カテゴリ名（'general', 'ideas', 'q-a', 'show-and-tell'）
        repo_owner: リポジトリのオーナー名（None の場合はデフォルトまたは環境変数）
        repo_name: リポジトリ名（None の場合はデフォルトまたは環境変数）

    Returns:
        カテゴリ ID、解決できない場合は None
    """
    # Step 1: 環境変数から取得
    category_id = get_category_id_from_env(category_name)
    if category_id:
        return category_id

    # Step 2: リポジトリ情報を決定
    # 環境変数優先、次に引数、最後にデフォルト値
    if repo_owner is None:
        repo_owner = os.getenv("GITHUB_DISCUSS_OWNER", DEFAULT_OWNER)
    if repo_name is None:
        repo_name = os.getenv("GITHUB_DISCUSS_REPO", DEFAULT_REPO)

    # Step 3: API で動的に取得
    categories = await api.get_categories(repo_owner, repo_name)
    for cat in categories:
        if cat["name"].lower() == category_name:
            return cat["id"]

    return None


async def get_repo_id_cached(
    api: GitHubDiscussionsAPI,
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    env_var: str = "GITHUB_DISCUSS_REPO_ID",
) -> str:
    """リポジトリ ID を取得する（環境変数を優先し、なければ API で取得）。

    以下の優先順位で ID を解決します：
    1. 指定された環境変数（デフォルト: GITHUB_DISCUSS_REPO_ID）
    2. 後方互換環境変数（AI_LOUNGE_REPO_ID）
    3. GitHub API による動的取得

    Args:
        api: GitHubDiscussionsAPI のインスタンス
        owner: リポジトリのオーナー名（None の場合はデフォルトまたは環境変数）
        repo: リポジトリ名（None の場合はデフォルトまたは環境変数）
        env_var: 環境変数名（デフォルト: GITHUB_DISCUSS_REPO_ID）

    Returns:
        リポジトリ ID

    Raises:
        ValueError: リポジトリ ID を取得できなかった場合
    """
    # 環境変数を優先（汎用名→後方互換名）
    repo_id = os.getenv(env_var)
    if repo_id:
        return repo_id

    # 後方互換環境変数を確認
    if env_var == "GITHUB_DISCUSS_REPO_ID":
        repo_id = os.getenv("AI_LOUNGE_REPO_ID")
        if repo_id:
            return repo_id

    # リポジトリ情報を決定
    if owner is None:
        owner = os.getenv("GITHUB_DISCUSS_OWNER", DEFAULT_OWNER)
    if repo is None:
        repo = os.getenv("GITHUB_DISCUSS_REPO", DEFAULT_REPO)

    # API で取得
    resolved = await api.get_repository_id(owner, repo)
    if not resolved:
        raise ValueError(f"リポジトリ '{owner}/{repo}' の ID を取得できませんでした")

    return resolved


def validate_env(strict: bool = False) -> list[str]:
    """環境変数の検証を行う。

    必須環境変数の存在を確認し、設定されていない場合はエラーまたは警告を生成します。

    Args:
        strict: True の場合、必須変数の欠落で例外を発生させる。
                False の場合は警告メッセージを返すのみ。

    Returns:
        警告メッセージのリスト

    Raises:
        ValueError: strict=True で必須環境変数が欠落している場合
    """
    warnings_list = []

    # 必須環境変数のチェック
    for var in REQUIRED_ENV_VARS:
        value = os.getenv(var)
        if not value or not value.strip():
            msg = f"必須環境変数 '{var}' が設定されていません"
            if strict:
                raise ValueError(msg)
            warnings_list.append(msg)

    # オプショナル環境変数の警告
    for var in OPTIONAL_ENV_VARS:
        if os.getenv(var) is None:
            warnings_list.append(f"環境変数 '{var}' が設定されていません（任意）")

    return warnings_list
