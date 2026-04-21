"""E2E テスト：実際の GitHub Discussions API を使用したテスト。

注意：このテストを実行するには以下の設定が必要です：
1. GITHUB_TOKEN 環境変数に有効なトークンを設定
2. テスト用 Discussion が事前に作成されていること

実行方法：
    uv run pytest tests/test_e2e.py -v

注意：このテストは実際の API コールを行うため、レートリミットに注意してください。
"""

import os
import pytest
import asyncio
from dotenv import load_dotenv

# .env ファイルから環境変数を読み込む
load_dotenv()

from github_discuss.github_api import GitHubDiscussionsAPI, DiscussionInput
from github_discuss.utils import (
    resolve_category_id,
    get_repo_id_cached,
    DEFAULT_OWNER,
    DEFAULT_REPO,
)


# ============================================================================
# テスト設定
# ============================================================================

# E2E テスト用のリポジトリ情報
# 環境変数で上書き可能
E2E_OWNER = os.getenv("GITHUB_DISCUSS_OWNER", "utenadev")
E2E_REPO = os.getenv("GITHUB_DISCUSS_REPO", "github-discuss-mcp")

# テスト用 Discussion タイトル（存在確認用）
E2E_DISCUSSION_TITLES = {
    "general": "[E2E テスト用] 一般投稿スレッド",
    "ideas": "[E2E テスト用] アイデア提案スレッド",
    "q-a": "[E2E テスト用] 質問スレッド",
    "show-and-tell": "[E2E テスト用] 自己紹介スレッド",
}


# ============================================================================
# フィクスチャ
# ============================================================================

@pytest.fixture(scope="module")
def api():
    """E2E テスト用の API インスタンス。"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        pytest.skip("GITHUB_TOKEN が設定されていません")
    return GitHubDiscussionsAPI(token=token)


@pytest.fixture(scope="module")
def event_loop():
    """非同期テスト用のイベントループ。"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# E2E テスト
# ============================================================================

class TestE2ECategories:
    """カテゴリ関連の E2E テスト。"""

    @pytest.mark.asyncio
    async def test_get_all_categories(self, api):
        """すべてのカテゴリが取得できることを確認する。"""
        categories = await api.get_categories(E2E_OWNER, E2E_REPO)

        # 4 つ以上のカテゴリが存在することを期待
        assert len(categories) >= 4, f"カテゴリが 4 つ未満です：{len(categories)}"

        # カテゴリ名のチェック（大文字小文字を無視）
        category_names_lower = [cat["name"].lower() for cat in categories]
        expected_categories = ["general", "ideas", "q&a", "show and tell"]

        for expected in expected_categories:
            assert expected in category_names_lower, \
                f"カテゴリ '{expected}' が見つかりません。取得できたカテゴリ：{category_names_lower}"

    @pytest.mark.asyncio
    async def test_resolve_category_ids(self, api):
        """各カテゴリの ID が解決できることを確認する。"""
        # 実際のカテゴリ名はリポジトリによって異なる可能性がある
        # ここでは汎用的なテストを行う
        categories = await api.get_categories(E2E_OWNER, E2E_REPO)
        
        # 少なくとも 1 つ以上のカテゴリが取得でき、ID が解決できることを確認
        assert len(categories) > 0, "カテゴリが取得できませんでした"
        
        # 最初のカテゴリ ID が解決できることを確認
        first_category_name = categories[0]["name"]
        category_id = await resolve_category_id(
            api,
            first_category_name.lower(),
            repo_owner=E2E_OWNER,
            repo_name=E2E_REPO,
        )
        assert category_id is not None, \
            f"カテゴリ '{first_category_name}' の ID が解決できませんでした"


class TestE2ERepository:
    """リポジトリ関連の E2E テスト。"""

    @pytest.mark.asyncio
    async def test_get_repository_id(self, api):
        """リポジトリ ID が取得できることを確認する。"""
        repo_id = await api.get_repository_id(E2E_OWNER, E2E_REPO)

        assert repo_id is not None, "リポジトリ ID が取得できませんでした"
        assert repo_id.startswith("R_"), \
            f"リポジトリ ID の形式が不正です：{repo_id}"

    @pytest.mark.asyncio
    async def test_get_repo_id_cached(self, api):
        """get_repo_id_cached が正常に動作することを確認する。"""
        repo_id = await get_repo_id_cached(api, owner=E2E_OWNER, repo=E2E_REPO)

        assert repo_id is not None, "リポジトリ ID が取得できませんでした"
        assert repo_id.startswith("R_"), \
            f"リポジトリ ID の形式が不正です：{repo_id}"


class TestE2EDiscussionCreation:
    """ディスカッション作成の E2E テスト。

    注意：このテストは実際に投稿を作成します。
    実行後は手動で削除してください。
    """

    @pytest.mark.asyncio
    async def test_create_discussion(self, api):
        """ディスカッションの作成が正常にできることを確認する。"""
        # カテゴリ ID の取得
        category_id = await resolve_category_id(
            api,
            "general",
            repo_owner=E2E_OWNER,
            repo_name=E2E_REPO,
        )
        assert category_id is not None, "カテゴリ ID が取得できませんでした"

        # リポジトリ ID の取得
        repo_id = await get_repo_id_cached(api, owner=E2E_OWNER, repo=E2E_REPO)
        assert repo_id is not None, "リポジトリ ID が取得できませんでした"

        # テスト用ディスカッションの作成
        # 実際の投稿はせず、ドライラン的な確認のみ行う場合はコメントアウトを解除
        # return

        discussion_input = DiscussionInput(
            repository_id=repo_id,
            category_id=category_id,
            title="[E2E テスト] 自動投稿テスト",
            body="この投稿は E2E テストによって自動的に作成されました。\n"
                 "テスト終了後に手動で削除してください。",
        )

        result = await api.create_discussion(discussion_input)

        # 結果の検証
        assert result.success is True, f"投稿に失敗しました：{result.error}"
        assert result.discussion_url is not None, "ディスカッション URL が返されていません"
        assert result.discussion_id is not None, "ディスカッション ID が返されていません"
        assert result.discussion_url.startswith(
            f"https://github.com/{E2E_OWNER}/{E2E_REPO}/discussions/"
        ), f"URL の形式が不正です：{result.discussion_url}"

        print(f"\n✅ テスト投稿が作成されました：{result.discussion_url}")
        print("   テスト終了後に手動で削除してください")


class TestE2EIntegration:
    """統合テスト：CLI および MCP サーバーとの連携。"""

    @pytest.mark.asyncio
    async def test_full_workflow(self, api):
        """カテゴリ取得→リポジトリ ID 取得→投稿のフルワークフローをテストする。"""
        # 1. カテゴリ一覧の取得
        categories = await api.get_categories(E2E_OWNER, E2E_REPO)
        assert len(categories) >= 4

        # 2. リポジトリ ID の取得
        repo_id = await get_repo_id_cached(api, owner=E2E_OWNER, repo=E2E_REPO)
        assert repo_id.startswith("R_")

        # 3. 各カテゴリの ID 解決
        for category_name in ["general", "ideas"]:
            category_id = await resolve_category_id(
                api,
                category_name,
                repo_owner=E2E_OWNER,
                repo_name=E2E_REPO,
            )
            assert category_id is not None

        # 4. 投稿（オプション）
        # 実際の投稿を行わない場合はこのブロックをスキップ
        if os.getenv("E2E_SKIP_POSTING", "false").lower() == "true":
            pytest.skip("E2E_SKIP_POSTING が設定されているため投稿をスキップ")

        general_category_id = await resolve_category_id(
            api,
            "general",
            repo_owner=E2E_OWNER,
            repo_name=E2E_REPO,
        )

        discussion_input = DiscussionInput(
            repository_id=repo_id,
            category_id=general_category_id,
            title="[E2E 統合テスト] ワークフロー検証",
            body="E2E 統合テストによる投稿です。\n"
                 "カテゴリ取得、リポジトリ ID 取得、投稿の全フローが正常に動作しました。",
        )

        result = await api.create_discussion(discussion_input)
        assert result.success is True
        assert result.discussion_url is not None

        print(f"\n✅ 統合テスト成功：{result.discussion_url}")
