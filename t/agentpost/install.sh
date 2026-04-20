#!/usr/bin/env bash
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
PREFIX="./.agentpost"  # デフォルト：プロジェクト内

while [[ $# -gt 0 ]]; do
  case $1 in
    --prefix) PREFIX="$2"; shift 2 ;;
    *) echo "Usage: bash install.sh [--prefix <path>]"; exit 1 ;;
  esac
done

# 相対パスを絶対パスに解決
[[ "$PREFIX" != /* ]] && PREFIX="$REPO_DIR/$PREFIX"

echo "📦 Installing AgentPost to: $PREFIX"
mkdir -p "$PREFIX/logs" "$PREFIX/agents"
chmod +x "$REPO_DIR/agentpost.py" "$REPO_DIR/agentpost"

# シンボリックリンク作成（wrapper script を使用）
ln -sf "$REPO_DIR/agentpost" "$BIN_DIR/agentpost"

# uv run 用に .env 出力（スペースを含むパスも安全）
printf 'AGENTPOST_BASE="%s"\n' "$PREFIX" > "$REPO_DIR/.env"
echo "📝 Wrote AGENTPOST_BASE to .env"

# watchdog 依存チェック（uv 対応）
if ! python3 -c "import watchdog" 2>/dev/null; then
  if command -v uv &> /dev/null; then
    echo "📦 Adding watchdog via uv..."
    uv add watchdog >/dev/null 2>&1 || echo "⚠️  uv add failed. Run: uv add watchdog"
  else
    echo "⚠️  uv not found. Install watchdog manually: pip install watchdog"
  fi
fi

echo "✅ Installation complete."
echo "🚀 Next: uv run agentpost setup"
