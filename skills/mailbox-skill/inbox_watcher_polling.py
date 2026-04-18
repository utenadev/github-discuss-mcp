#!/usr/bin/env python3
"""
inbox_watcher_polling.py - メールボックス監視（Polling 版）

inotifywait を使わず、polling でファイル変更を検知します。
timeout の問題がある場合に使用します。

Usage:
    python skills/mailbox/inbox_watcher_polling.py <target>

Example:
    python skills/mailbox/inbox_watcher_polling.py vibe
"""

import json
import sys
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

def get_tmux_pane():
    """現在の tmux pane を取得（send-keys 用の形式）"""
    try:
        # セッション ID とウィンドウ・ペインを取得
        result = subprocess.run(
            ["tmux", "display-message", "-p", "#S:#I.#P"],
            capture_output=True,
            text=True,
            timeout=2
        )
        pane = result.stdout.strip()
        if pane:
            return pane
    except Exception as e:
        print(f"⚠️ tmux pane 取得エラー：{e}", file=sys.stderr)
    
    # フォールバック：現在のセッションの現在の pane
    try:
        result = subprocess.run(
            ["tmux", "list-panes", "-F", "#S:#I.#P", "-f", "#{pane_current_command}"],
            capture_output=True,
            text=True,
            timeout=2
        )
        panes = result.stdout.strip().split('\n')
        if panes and panes[0]:
            return panes[0]
    except Exception:
        pass
    
    return None

def send_to_tmux(pane, message):
    """tmux pane にメッセージを送信"""
    if not pane:
        print(f"⚠️ tmux pane が指定されていません：{message}", file=sys.stderr)
        return

    try:
        # メッセージを送信（Enter キーと一緒に行を送る）
        subprocess.run(
            ["tmux", "send-keys", "-t", pane, f"# 📬 {message}", "C-m"],
            timeout=5
        )
        # 最後の改行を追加（Agent によって必要）
        subprocess.run(
            ["tmux", "send-keys", "-t", pane, "C-m"],
            timeout=5
        )
    except Exception as e:
        print(f"⚠️ tmux 送信エラー：{e}", file=sys.stderr)

def main():
    if len(sys.argv) < 2:
        print("Usage: inbox_watcher_polling.py <target> [tmux_window]", file=sys.stderr)
        print("Example: inbox_watcher_polling.py vibe 3.1", file=sys.stderr)
        sys.exit(1)

    target = sys.argv[1]
    tmux_window = sys.argv[2] if len(sys.argv) > 2 else None

    # プロジェクトルートを取得
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    mailbox_dir = project_root / ".beads" / "mailbox"
    mailbox_file = mailbox_dir / f"{target}.json"
    
    # tmux window を決定
    if tmux_window:
        # 引数で指定された場合
        tmux_pane = tmux_window
    else:
        # 自動検出
        tmux_pane = get_tmux_pane()
    
    # メールボックスディレクトリ作成
    mailbox_dir.mkdir(parents=True, exist_ok=True)
    mailbox_file.touch()
    
    print(f"📬 {target} のメールボックス監視を開始...（polling 版）")
    print(f"   対象：{mailbox_file}")
    print(f"   通知先：tmux pane {tmux_pane}")
    print(f"   終了：Ctrl+C")
    print()
    
    # 前回のファイルサイズを記録
    last_size = 0
    last_mtime = 0
    
    # Polling ループ（5 秒ごと）
    try:
        while True:
            try:
                stat = mailbox_file.stat()
                current_size = stat.st_size
                current_mtime = stat.st_mtime
                
                # ファイルが更新されたかチェック
                if current_size > 0 and (current_size != last_size or current_mtime != last_mtime):
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📬 通知を検知！")

                    # メールボックスを表示
                    with open(mailbox_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    message = data.get('message', '')
                    if not message:
                        message = data.get('content', 'No message')
                    
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 内容：{message}")
                    print()
                    
                    # tmux pane に通知
                    send_to_tmux(tmux_pane, f"メールボックスに通知があります ({target})")
                    send_to_tmux(tmux_pane, f"cat {mailbox_file}")
                    
                    # 読んだらクリア（本当に空にする）
                    with open(mailbox_file, 'w', encoding='utf-8') as f:
                        f.write('')  # 空文字列を書く（サイズ 0）

                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ メールボックスをクリアしました")

                    last_size = 0
                    last_mtime = 0
                
                else:
                    last_size = current_size
                    last_mtime = current_mtime
                
                # 5 秒待機
                time.sleep(5)
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"⚠️ エラー：{e}", file=sys.stderr)
                time.sleep(5)
    
    except KeyboardInterrupt:
        print("\n👋 監視を終了しました")
        sys.exit(0)

if __name__ == "__main__":
    main()
