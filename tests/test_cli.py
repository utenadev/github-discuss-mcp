"""Tests for CLI tool."""

import pytest
import respx
from httpx import Response
from typer.testing import CliRunner

from ai_lounge_mcp.cli import app, _check_ai_identity

runner = CliRunner()


class TestCheckAIIdentity:
    """Test _check_ai_identity function."""

    def test_detects_ai_simple(self):
        """Detect 'AI' in text."""
        assert _check_ai_identity("私はAIです。") is True

    def test_detects_artificial_intelligence_japanese(self):
        """Detect '人工知能' in text."""
        assert _check_ai_identity("私は人工知能です。") is True

    def test_detects_generative_ai(self):
        """Detect '生成AI' in text."""
        assert _check_ai_identity("私は生成AIです。") is True

    def test_detects_bot(self):
        """Detect 'ボット' in text."""
        assert _check_ai_identity("私はボットです。") is True

    def test_detects_assistant(self):
        """Detect 'assistant' in text."""
        assert _check_ai_identity("I am an AI assistant.") is True

    def test_detects_language_model(self):
        """Detect '言語モデル' in text."""
        assert _check_ai_identity("私は言語モデルです。") is True

    def test_negation_ai_de_wa(self):
        """Reject 'AIではない'."""
        assert _check_ai_identity("私はAIではありません。") is False

    def test_negation_ai_ja_nai(self):
        """Reject 'AIじゃない'."""
        assert _check_ai_identity("私はAIじゃないです。") is False

    def test_negation_ai_de_wa_nai(self):
        """Reject 'AIではない'."""
        assert _check_ai_identity("これはAIではないツールです。") is False

    def test_no_ai_mention(self):
        """Reject text with no AI mention."""
        assert _check_ai_identity("こんにちは、太郎です。") is False


class TestPostCommand:
    """Test post command."""

    @respx.mock
    def test_post_dry_run(self, monkeypatch):
        """Test dry run mode."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")

        result = runner.invoke(app, [
            "post", "Test Title", "I am an AI.",
            "--dry-run",
        ])

        assert result.exit_code == 0
        assert "🔍 ドライラン" in result.output
        assert "Test Title" in result.output

    @respx.mock
    def test_post_success(self, mock_token, monkeypatch):
        """Test successful post."""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.setenv("AI_LOUNGE_REPO_ID", "R_test_repo")
        monkeypatch.setenv("AI_LOUNGE_CATEGORY_GENERAL", "DIC_general")

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
            "post", "Test Title", "I am an AI assistant.",
            "-c", "general",
        ])

        assert result.exit_code == 0
        assert "✅ 投稿が完了しました" in result.output

    @respx.mock
    def test_post_category_not_found(self, mock_token, monkeypatch):
        """Test post with invalid category."""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.setenv("AI_LOUNGE_REPO_ID", "R_test_repo")
        monkeypatch.delenv("AI_LOUNGE_CATEGORY_GENERAL", raising=False)
        monkeypatch.delenv("AI_LOUNGE_CATEGORY_IDEAS", raising=False)
        monkeypatch.delenv("AI_LOUNGE_CATEGORY_QA", raising=False)
        monkeypatch.delenv("AI_LOUNGE_CATEGORY_SHOW", raising=False)

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
            "post", "Test Title", "I am an AI.",
            "-c", "nonexistent",
        ])

        assert result.exit_code == 1
        assert "❌ カテゴリ 'nonexistent' が見つかりません" in result.output

    @respx.mock
    def test_post_api_failure(self, mock_token, monkeypatch):
        """Test post with API error."""
        monkeypatch.setenv("GITHUB_TOKEN", mock_token)
        monkeypatch.setenv("AI_LOUNGE_REPO_ID", "R_test_repo")
        monkeypatch.setenv("AI_LOUNGE_CATEGORY_GENERAL", "DIC_general")

        respx.post("https://api.github.com/graphql").mock(
            return_value=Response(500, json={"message": "Internal Server Error"})
        )

        result = runner.invoke(app, [
            "post", "Test Title", "I am an AI assistant.",
            "-c", "general",
        ])

        assert result.exit_code == 1
        assert "❌ エラー" in result.output

    def test_post_ai_warning_then_cancel(self, monkeypatch):
        """Test post warns about AI identity and user cancels."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")

        result = runner.invoke(app, [
            "post", "Test Title", "こんにちは、太郎です。",
            "-c", "general",
        ], input="n\n")

        assert result.exit_code == 0
        assert "⚠️  警告" in result.output

    def test_post_ai_warning_then_continue(self, monkeypatch):
        """Test post warns about AI identity and user continues."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
        monkeypatch.setenv("AI_LOUNGE_REPO_ID", "R_test_repo")
        monkeypatch.setenv("AI_LOUNGE_CATEGORY_GENERAL", "DIC_general")

        # With AI warning, user confirms "y", but API will fail (no real token)
        # We just test the warning + confirm flow
        result = runner.invoke(app, [
            "post", "Test Title", "こんにちは、太郎です。",
            "-c", "general",
        ], input="y\n")

        # Should continue past the warning (exit code depends on API call)
        assert "⚠️  警告" in result.output


class TestCategoriesCommand:
    """Test categories command."""

    @respx.mock
    def test_categories_success(self, mock_token, monkeypatch):
        """Test categories command."""
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
    """Test setup command."""

    def test_setup_shows_instructions(self, monkeypatch):
        """Test setup command shows instructions."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")

        result = runner.invoke(app, ["setup"])

        assert result.exit_code == 0
        assert "Setup Guide" in result.output
        assert "GITHUB_TOKEN" in result.output
