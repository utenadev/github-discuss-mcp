"""AgentPost コア機能のテスト。"""

import pytest
import json
import os
from pathlib import Path
from datetime import datetime, timezone

# agentpost モジュールをインポート
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestPostMessage:
    """メッセージ送信のテスト。"""
    
    def test_post_message(self, temp_agentpost_dir, agent_dirs):
        """メッセージ送信の基本テスト。"""
        from agentpost import post, save_config, BASE_DIR
        
        # 設定ファイルを保存
        config = {
            "version": 1,
            "auto_update": False,
            "agents": [{"name": "gemini", "session": "0", "window": 1, "pane": 1}],
            "defaults": {"priority": "normal", "ttl_seconds": 86400}
        }
        save_config(config)
        
        # メッセージを送信
        msg_id = post(to="gemini", body="テストメッセージ", from_agent="qwen")
        
        # 送信されたことを確認
        inbox = BASE_DIR / "agents" / "gemini" / "inbox"
        files = list(inbox.glob("*.json"))
        assert len(files) >= 1
        
        # 最新のメッセージ内容を確認
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        with open(files[0], "r", encoding="utf-8") as f:
            msg = json.load(f)
        
        assert msg["from"] == "qwen"
        assert msg["to"] == "gemini"
        assert msg["body"] == "テストメッセージ"
    
    def test_post_with_ref(self, temp_agentpost_dir, agent_dirs):
        """ref 付きメッセージ送信テスト。"""
        from agentpost import post, save_config, BASE_DIR
        
        config = {
            "version": 1,
            "auto_update": False,
            "agents": [{"name": "gemini", "session": "0", "window": 1, "pane": 1}],
            "defaults": {"priority": "normal", "ttl_seconds": 86400}
        }
        save_config(config)
        
        post(to="gemini", body="ブランチをマージしてください", from_agent="qwen", ref="br:bd-123")
        
        inbox = BASE_DIR / "agents" / "gemini" / "inbox"
        files = list(inbox.glob("*.json"))
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        with open(files[0], "r", encoding="utf-8") as f:
            msg = json.load(f)
        
        assert msg["ref"]["system"] == "br"
        assert msg["ref"]["issue_id"] == "bd-123"


class TestCheckMessages:
    """メッセージ受信のテスト。"""
    
    def test_check_empty_inbox(self, temp_agentpost_dir, agent_dirs):
        """空の受信トレイのテスト。"""
        from agentpost import check, save_config
        
        config = {
            "version": 1,
            "auto_update": False,
            "agents": [{"name": "gemini", "session": "0", "window": 1, "pane": 1}],
            "defaults": {"priority": "normal", "ttl_seconds": 86400}
        }
        save_config(config)
        
        messages = check(agent="gemini")
        assert len(messages) == 0


class TestConfigManagement:
    """設定ファイル管理のテスト。"""
    
    def test_save_config_creates_directory(self, temp_agentpost_dir):
        """設定保存時にディレクトリを作成するテスト。"""
        from agentpost import save_config, CONFIG_FILE
        
        config = {
            "version": 1,
            "auto_update": False,
            "agents": [],
            "defaults": {"priority": "normal", "ttl_seconds": 86400}
        }
        save_config(config)
        
        assert CONFIG_FILE.exists()
    
    def test_save_config_permissions(self, temp_agentpost_dir):
        """設定ファイルのパーミッションテスト。"""
        from agentpost import save_config, CONFIG_FILE
        import stat
        
        config = {
            "version": 1,
            "auto_update": False,
            "agents": [],
            "defaults": {"priority": "normal", "ttl_seconds": 86400}
        }
        save_config(config)
        
        mode = CONFIG_FILE.stat().st_mode
        assert mode & 0o777 == 0o600


class TestAgentDetection:
    """エージェント検出のテスト。"""
    
    def test_detect_agents_with_pipe_format(self, monkeypatch):
        """パイプ区切り形式でのエージェント検出テスト。"""
        import agentpost
        
        def mock_tmux(args):
            return "0|1|1|qwen|node|Qwen-Agent\n0|2|1|gemini|node|Gemini-Agent"
        
        monkeypatch.setattr(agentpost, "tmux_cmd", mock_tmux)
        
        agents = agentpost.detect_agents()
        
        assert len(agents) == 2
        assert agents[0]["name"] == "qwen"
        assert agents[0]["window"] == 1
        assert agents[0]["pane"] == 1
        
        assert agents[1]["name"] == "gemini"
        assert agents[1]["window"] == 2
        assert agents[1]["pane"] == 1
