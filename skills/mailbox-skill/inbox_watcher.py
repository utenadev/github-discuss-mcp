#!/usr/bin/env python3
"""
inbox_watcher.py - メールボックス監視（Python 版）

inotifywait を使用してファイル変更を検知し、tmux に通知します。

Usage:
    python skills/mailbox/inbox_watcher.py <target>

Example:
    python skills/mailbox/inbox_watcher.py vibe
"""

import json
import sys
import os
import subprocess
import signal
from datetime import datetime
from pathlib import Path

def get_tmux_pane():
    """現在の tmux pane を取得"""
    try:
        result = subprocess.run(
            ["tmux", "display-message", "-p", "#I:#P"],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.stdout.strip()
    except Exception:
        return "0"

def send_to_tmux(pane, message):
    """tmux pane にメッセージを送信"""
    try:
        # コメントとして表示
        subprocess.run(
            ["tmux", "send-keys", "-t", pane, f"# 📬 {message}", "Enter"],
            timeout=5
        )
    except Exception as e:
        print(f"⚠️ tmux 送信エラー：{e}", file=sys.stderr)

def main():
    if len(sys.argv) < 2:
        print("Usage: inbox_watcher.py <target>", file=sys.stderr)
        print("Example: inbox_watcher.py vibe", file=sys.stderr)
        sys.exit(1)
    
    target = sys.argv[1]
    
    # プロジェクトルートを取得
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    mailbox_dir = project_root / ".beads" / "mailbox"
    mailbox_file = mailbox_dir / f"{target}.json"
    tmux_pane = get_tmux_pane()
    
    # メールボックスディレクトリ作成
    mailbox_dir.mkdir(parents=True, exist_ok=True)
    mailbox_file.touch()
    
    print(f"📬 {target} のメールボックス監視を開始...")
    print(f"   対象：{mailbox_file}")
    print(f"   通知先：tmux pane {tmux_pane}")
    print(f"   終了：Ctrl+C")
    print()
    
    # inotifywait を使用して監視
    try:
        inotifywait = subprocess.Popen(
            ["inotifywait", "-m", "-e", "modify", "-e", "close_write", str(mailbox_file), "--format", "%e"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        for line in inotifywait.stdout:
            event = line.strip()
            if event:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📬 通知を検知！")
                
                # メールボックスを表示
                if mailbox_file.stat().st_size > 0:
                    with open(mailbox_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    message = data.get('message', 'No message')
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 内容：{message}")
                    print()
                    
                    # tmux pane に通知
                    send_to_tmux(tmux_pane, f"メールボックスに通知があります ({target})")
                    send_to_tmux(tmux_pane, f"cat {mailbox_file}")
                    
                    # 読んだらクリア
                    with open(mailbox_file, 'w', encoding='utf-8') as f:
                        json.dump({}, f)
                    
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ メールボックスをクリアしました")
        
    except FileNotFoundError:
        print("❌ inotifywait が見つかりません", file=sys.stderr)
        print("   sudo apt install inotify-tools", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 監視を終了しました")
        inotifywait.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
