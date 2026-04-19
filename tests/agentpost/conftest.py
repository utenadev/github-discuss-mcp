"""AgentPost テスト用の共通フィクスチャ。"""

import pytest
import json
import tempfile
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone


@pytest.fixture
def temp_agentpost_dir():
    """テスト用の一時ディレクトリ。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        
        # 環境変数を保存
        old_env = os.environ.get("AGENTPOST_BASE")
        
        # 環境変数を設定
        os.environ["AGENTPOST_BASE"] = str(base_dir)
        
        # ディレクトリ構造を作成
        (base_dir / "agents").mkdir()
        (base_dir / "logs").mkdir()
        
        # BASE_DIR のキャッシュをクリア
        import agentpost
        old_base_dir = getattr(agentpost, 'BASE_DIR', None)
        old_config_file = getattr(agentpost, 'CONFIG_FILE', None)
        
        # agentpost モジュールの BASE_DIR を更新
        agentpost.BASE_DIR = base_dir
        agentpost.CONFIG_FILE = base_dir / "config.json"
        
        yield base_dir
        
        # 環境変数を元に戻す
        if old_env:
            os.environ["AGENTPOST_BASE"] = old_env
        elif "AGENTPOST_BASE" in os.environ:
            del os.environ["AGENTPOST_BASE"]
        
        # agentpost モジュールの BASE_DIR を元に戻す
        if old_base_dir is not None:
            agentpost.BASE_DIR = old_base_dir
        if old_config_file is not None:
            agentpost.CONFIG_FILE = old_config_file


@pytest.fixture
def mock_config():
    """モック設定ファイル。"""
    return {
        "version": 1,
        "auto_update": False,
        "agents": [
            {
                "name": "qwen",
                "session": "0",
                "window": 1,
                "pane": 1
            },
            {
                "name": "gemini",
                "session": "0",
                "window": 2,
                "pane": 1
            },
            {
                "name": "vibe",
                "session": "0",
                "window": 3,
                "pane": 1
            }
        ],
        "defaults": {
            "priority": "normal",
            "ttl_seconds": 86400
        }
    }


@pytest.fixture
def sample_message():
    """サンプルメッセージ。"""
    return {
        "version": 1,
        "id": "msg_test_123",
        "from": "qwen",
        "to": "gemini",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "type": "task",
        "priority": "normal",
        "body": "テストメッセージ",
        "ref": None,
        "reply_to": None,
        "ttl_seconds": 86400
    }


@pytest.fixture
def agent_dirs(temp_agentpost_dir):
    """エージェントディレクトリを作成。"""
    agents_dir = temp_agentpost_dir / "agents"
    
    for agent in ["qwen", "gemini", "vibe"]:
        for subdir in ["inbox", "processing", "archive"]:
            (agents_dir / agent / subdir).mkdir(parents=True, exist_ok=True)
    
    return agents_dir


@pytest.fixture(autouse=True)
def reset_agentpost_state():
    """各テスト前に agentpost モジュールの状態をリセット。"""
    import agentpost
    
    # 環境変数をクリア
    if "AGENTPOST_AGENT" in os.environ:
        del os.environ["AGENTPOST_AGENT"]
    
    yield
    
    # テスト後に環境変数をクリア
    if "AGENTPOST_AGENT" in os.environ:
        del os.environ["AGENTPOST_AGENT"]
