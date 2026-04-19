#!/usr/bin/env python3
"""
AgentPost Skill for AI Coding Agents.
Thin wrapper that dynamically imports the core engine from the parent directory.
Usage inside Agent Code:
    from skill.agentpost import post, check, listen_loop
"""
import sys
from pathlib import Path

# リポジトリルート (../) を sys.path に追加し、コアエンジンを確実に import 可能にする
_core_dir = Path(__file__).resolve().parent.parent
if str(_core_dir) not in sys.path:
    sys.path.insert(0, str(_core_dir))

from agentpost import post, check, listen_loop

__all__ = ["post", "check", "listen_loop"]
