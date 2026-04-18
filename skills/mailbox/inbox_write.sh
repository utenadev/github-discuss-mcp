#!/bin/bash
# inbox_write.sh - メールボックスへの通知書き込み
# Usage: bash skills/mailbox/inbox_write.sh <target> <message>
# Example: bash skills/mailbox/inbox_write.sh vibe "br を確認せよ！"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

TARGET="$1"
MESSAGE="$2"

MAILBOX_DIR="$PROJECT_ROOT/.beads/mailbox"
MAILBOX_FILE="$MAILBOX_DIR/${TARGET}.json"
LOCKFILE="${MAILBOX_FILE}.lock"

# 引数チェック
if [ -z "$TARGET" ] || [ -z "$MESSAGE" ]; then
    echo "Usage: inbox_write.sh <target> <message>" >&2
    echo "Example: inbox_write.sh vibe \"br を確認せよ！\"" >&2
    exit 1
fi

# メールボックスディレクトリ作成
mkdir -p "$MAILBOX_DIR"

# タイムスタンプ生成
TIMESTAMP=$(date -Iseconds)
MSG_ID="msg_$(date +%Y%m%d_%H%M%S)_$$"

# 排他ロックで安全に書き込み
(
    if command -v flock &>/dev/null; then
        exec 200>"$LOCKFILE"
        flock -w 5 200 || { echo "❌ ロック取得失敗" >&2; exit 1; }
    fi

    # JSON で保存（簡易版：1 件だけ保持）
    cat > "$MAILBOX_FILE" <<EOF
{
  "id": "$MSG_ID",
  "timestamp": "$TIMESTAMP",
  "message": "$MESSAGE"
}
EOF

) 200>"$LOCKFILE"

echo "✅ $TARGET に通知しました："
echo "   $MESSAGE"
