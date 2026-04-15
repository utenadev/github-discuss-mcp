"""Common utilities for MCP server and CLI."""

import os
import warnings
from typing import Optional

from .github_api import GitHubDiscussionsAPI

# AI Lounge のデフォルト設定
AI_LOUNGE_OWNER = "lifemate-ai"
AI_LOUNGE_REPO = "ai-lounge"

# カテゴリ名の環境変数マップ
CATEGORY_ENV_VARS = {
    "general": "AI_LOUNGE_CATEGORY_GENERAL",
    "ideas": "AI_LOUNGE_CATEGORY_IDEAS",
    "q-a": "AI_LOUNGE_CATEGORY_QA",
    "show-and-tell": "AI_LOUNGE_CATEGORY_SHOW",
}

# 必須環境変数
REQUIRED_ENV_VARS = ["GITHUB_TOKEN"]

# オプショナル環境変数（警告のみ）
OPTIONAL_ENV_VARS = ["AI_LOUNGE_REPO_ID"] + list(CATEGORY_ENV_VARS.values())


def get_category_id_from_env(category: str) -> Optional[str]:
    """環境変数からカテゴリIDを取得する。"""
    env_var = CATEGORY_ENV_VARS.get(category)
    if env_var:
        return os.getenv(env_var, "")
    return ""


async def resolve_category_id(
    api: GitHubDiscussionsAPI,
    category_name: str,
    repo_owner: str = AI_LOUNGE_OWNER,
    repo_name: str = AI_LOUNGE_REPO,
) -> Optional[str]:
    """カテゴリ名からIDを解決する。

    1. 環境変数をまず確認
    2. 環境変数が空の場合、GitHub APIで動的に取得
    """
    # Step 1: 環境変数から取得
    category_id = get_category_id_from_env(category_name)
    if category_id:
        return category_id

    # Step 2: APIで動的に取得
    categories = await api.get_categories(repo_owner, repo_name)
    for cat in categories:
        if cat["name"].lower() == category_name:
            return cat["id"]

    return None


async def get_repo_id_cached(
    api: GitHubDiscussionsAPI,
    owner: str = AI_LOUNGE_OWNER,
    repo: str = AI_LOUNGE_REPO,
    env_var: str = "AI_LOUNGE_REPO_ID",
) -> str:
    """リポジトリIDを取得する（環境変数を優先し、なければAPIで取得）。"""
    repo_id = os.getenv(env_var)
    if repo_id:
        return repo_id

    resolved = await api.get_repository_id(owner, repo)
    if not resolved:
        raise ValueError(f"リポジトリ '{owner}/{repo}' のIDを取得できませんでした")

    return resolved


def validate_env(strict: bool = False) -> list[str]:
    """環境変数の検証を行う。

    Args:
        strict: True の場合、必須変数の欠落は例外発生、False の場合は警告のみ

    Returns:
        警告メッセージのリスト
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
