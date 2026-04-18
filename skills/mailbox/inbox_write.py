#!/usr/bin/env python3
"""
inbox_write.py - メールボックスへの通知書き込み（Python 版）

Usage:
    python skills/mailbox/inbox_write.py <target> <message>

Example:
    python skills/mailbox/inbox_write.py vibe "br を確認せよ！"
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
import fcntl

def main():
    if len(sys.argv) < 3:
        print("Usage: inbox_write.py <target> <message>", file=sys.stderr)
        print("Example: inbox_write.py vibe \"br を確認せよ！\"", file=sys.stderr)
        sys.exit(1)
    
    target = sys.argv[1]
    message = sys.argv[2]
    
    # プロジェクトルートを取得
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    mailbox_dir = project_root / ".beads" / "mailbox"
    mailbox_file = mailbox_dir / f"{target}.json"
    lockfile = mailbox_file.with_suffix(".json.lock")
    
    # メールボックスディレクトリ作成
    mailbox_dir.mkdir(parents=True, exist_ok=True)
    
    # タイムスタンプ生成
    timestamp = datetime.now().isoformat()
    msg_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
    
    # 排他ロックで安全に書き込み
    try:
        with open(lockfile, 'w') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            
            try:
                # JSON で保存（簡易版：1 件だけ保持）
                data = {
                    "id": msg_id,
                    "timestamp": timestamp,
                    "message": message
                }
                
                with open(mailbox_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ {target} に通知しました：")
                print(f"   {message}")
                
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    
    except Exception as e:
        print(f"❌ エラー：{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
