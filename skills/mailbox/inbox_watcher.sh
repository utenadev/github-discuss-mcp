#!/bin/bash
# inbox_watcher.sh - メールボックス監視（inotifywait 使用）
# Usage: bash skills/mailbox/inbox_watcher.sh <target>
# Example: bash skills/mailbox/inbox_watcher.sh vibe

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

TARGET="$1"

MAILBOX_DIR="$PROJECT_ROOT/.beads/mailbox"
MAILBOX_FILE="$MAILBOX_DIR/${TARGET}.json"
TMUX_PANE=$(tmux display-message -p '#I:#P' 2>/dev/null || echo "0")

# 引数チェック
if [ -z "$TARGET" ]; then
    echo "Usage: inbox_watcher.sh <target>" >&2
    echo "Example: inbox_watcher.sh vibe" >&2
    exit 1
fi

# inotifywait のチェック
if ! command -v inotifywait &>/dev/null; then
    echo "❌ inotifywait が見つかりません" >&2
    echo "   sudo apt install inotify-tools" >&2
    exit 1
fi

# メールボックスディレクトリ作成
mkdir -p "$MAILBOX_DIR"
touch "$MAILBOX_FILE"

echo "📬 $TARGET のメールボックス監視を開始..."
echo "   対象：$MAILBOX_FILE"
echo "   通知先：tmux pane $TMUX_PANE"
echo "   終了：Ctrl+C"
echo ""

# inotifywait でファイル変更を監視
inotifywait -m -e modify -e close_write "$MAILBOX_FILE" --format '%e' | while read event; do
    echo "[$(date)] 📬 通知を検知！"
    
    # メールボックスを表示
    if [ -s "$MAILBOX_FILE" ]; then
        echo "[$(date)] 内容："
        cat "$MAILBOX_FILE"
        echo ""
        
        # tmux pane に通知
        tmux send-keys -t "$TMUX_PANE" "# 📬 メールボックスに通知があります ($TARGET)" Enter
        tmux send-keys -t "$TMUX_PANE" "cat $MAILBOX_FILE" Enter
        
        # 読んだらクリア
        > "$MAILBOX_FILE"
        echo "[$(date)] ✅ メールボックスをクリアしました"
    fi
done
