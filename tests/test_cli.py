"""CLI ツールのテスト。"""

import pytest
import respx
from httpx import Response
from typer.testing import CliRunner

from github_discuss_mcp.cli import app

runner = CliRunner()


class TestPostCommand:
    """post コマンドのテスト。"""

    @respx.mock
    def test_post_dry_run(self, monkeypatch):
        """ドライランモードのテスト。"""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")

        result = runner.invoke(app, [
            "post", "Test Title", "Test body",
            "--dry-run",
        ])

        assert result.exit_code == 0
        assert "🔍 ドライラン" in result.output
        assert "Test Title" in result.output

    @respx.mock
    def test_post_success(self, mock_token, monkeypatch):
        """投稿成功のテスト。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.setenv("GITHUB_DISCUSS_REPO_ID", "R_test_repo")
        monkeypatch.setenv("GITHUB_DISCUSS_CATEGORY_GENERAL", "DIC_general")

        mock_response = {
            "data": {
                "createDiscussion": {
                    "discussion": {
                        "id": "D_test",
                        "url": "https://github.com/lifemate-ai/ai-lounge/discussions/1",
                        "title": "Test",
                    }
                }
            }
        }
        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_response)
        )

        result = runner.invoke(app, [
            "post", "Test Title", "Test body",
            "-c", "general",
        ])

        assert result.exit_code == 0
        assert "✅ 投稿が完了しました" in result.output

    @respx.mock
    def test_post_category_not_found(self, mock_token, monkeypatch):
        """無効なカテゴリでの投稿テスト。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.setenv("GITHUB_DISCUSS_REPO_ID", "R_test_repo")
        monkeypatch.delenv("GITHUB_DISCUSS_CATEGORY_GENERAL", raising=False)
        monkeypatch.delenv("GITHUB_DISCUSS_CATEGORY_IDEAS", raising=False)
        monkeypatch.delenv("GITHUB_DISCUSS_CATEGORY_QA", raising=False)
        monkeypatch.delenv("GITHUB_DISCUSS_CATEGORY_SHOW", raising=False)

        mock_categories = {
            "data": {
                "repository": {
                    "discussionCategories": {"nodes": []}
                }
            }
        }
        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_categories)
        )

        result = runner.invoke(app, [
            "post", "Test Title", "Test body",
            "-c", "nonexistent",
        ])

        assert result.exit_code == 1
        assert "❌ カテゴリ 'nonexistent' が見つかりません" in result.output

    @respx.mock
    def test_post_api_failure(self, mock_token, monkeypatch):
        """API エラー発生時の投稿テスト。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.setenv("GITHUB_DISCUSS_REPO_ID", "R_test_repo")
        monkeypatch.setenv("GITHUB_DISCUSS_CATEGORY_GENERAL", "DIC_general")

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(500, json={"message": "Internal Server Error"})
        )

        result = runner.invoke(app, [
            "post", "Test Title", "Test body",
            "-c", "general",
        ])

        assert result.exit_code == 1
        assert "❌ エラー" in result.output


class TestCategoriesCommand:
    """categories コマンドのテスト。"""

    @respx.mock
    def test_categories_success(self, mock_token, monkeypatch):
        """categories コマンド成功のテスト。"""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)

        mock_categories = {
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
                        ]
                    }
                }
            }
        }
        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(200, json=mock_categories)
        )

        result = runner.invoke(app, ["categories"])

        assert result.exit_code == 0
        assert "general" in result.output
        assert "💬" in result.output


class TestSetupCommand:
    """setup コマンドのテスト。"""

    def test_setup_shows_instructions(self, monkeypatch):
        """setup コマンドが手順を表示するテスト。"""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")

        result = runner.invoke(app, ["setup"])

        assert result.exit_code == 0
        assert "セットアップガイド" in result.output
        assert "GITHUB_TOKEN" in result.output
