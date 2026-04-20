"""AgentPost スキルのテスト。"""

import pytest
import json
import os
import sys
from pathlib import Path

# skill モジュールをインポート
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestSkillImport:
    """スキルインポートのテスト。"""
    
    def test_skill_import(self):
        """スキルがインポートできるかテスト。"""
        from skill.agentpost import post, check, listen_loop
        
        assert callable(post)
        assert callable(check)
        assert callable(listen_loop)
    
    def test_skill_exports(self):
        """スキルが正しくエクスポートされているかテスト。"""
        from skill import agentpost
        
        assert hasattr(agentpost, "post")
        assert hasattr(agentpost, "check")
        assert hasattr(agentpost, "listen_loop")


class TestSkillPost:
    """スキル post 関数のテスト。"""
    
    def test_skill_post_with_env(self, temp_agentpost_dir, agent_dirs, monkeypatch):
        """環境変数からエージェント名を取得するテスト。"""
        from skill.agentpost import post
        import agentpost as core
        
        # 環境変数を設定
        monkeypatch.setenv("AGENTPOST_AGENT", "qwen")
        
        # 設定ファイルを保存
        config = {
            "version": 1,
            "auto_update": False,
            "agents": [{"name": "gemini", "session": "0", "window": 1, "pane": 1}],
            "defaults": {"priority": "normal", "ttl_seconds": 86400}
        }
        
        original_config = core.CONFIG_FILE
        core.CONFIG_FILE = temp_agentpost_dir / "config.json"
        
        with open(core.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        try:
            # 送信
            post(to="gemini", body="スキルから送信")
            
            # 送信されたことを確認
            inbox = core.BASE_DIR / "agents" / "gemini" / "inbox"
            files = list(inbox.glob("*.json"))
            assert len(files) >= 1
        finally:
            core.CONFIG_FILE = original_config
