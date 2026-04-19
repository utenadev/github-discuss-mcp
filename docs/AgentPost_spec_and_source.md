# AgentPost システム仕様書 & 実装コード

---

## 1. 概要
**AgentPost** は、tmux セッション上で動作する AI Coding Agent 間の**非同期メッセージングシステム**です。  
人間が介在せず、Agent 同士が自律的に指示・報告・確認を交換する **YOLO モード** を前提に設計されています。

- **サーバレス・ローカル完結**: ネットワーク・デーモン不要。tmux のローカルファイルシステムのみで動作。
- **イベント駆動**: `watchdog` 利用時はファイル作成と同時に即時通知。未インストール時は軽量ポーリングで自動フォールバック。
- **オプショナル連携**: `br` (beads_rust) や外部 Issue システムの `ref` は**任意フィールド**。単体でもテキスト/JSON で完全動作。
- **単一ファイル構成**: 依存パッケージを最小化。リポジトリ内の 2 ファイルで CLI・スキル・設定管理を完結。

---

## 2. アーキテクチャ & 設計方針

| 項目 | 設計 | 理由 |
|------|------|------|
| **通信方式** | ファイルベースキュー（1メッセージ1ファイル） | 排他ロック不要。クラッシュ時でもメッセージ消失ゼロ。 |
| **状態遷移** | `inbox/` → `processing/` → `archive/` | 原子 `rename()` により、処理中のクラッシュを自動リカバリ。 |
| **検出・通知** | `watchdog` (推奨) / 0.5s ポーリング (フォールバック) | 遅延ゼロと環境依存性排除の両立。 |
| **外部連携** | `ref` フィールド（任意） | `br` がなくてもシステムが停止しない。失敗時は `body` のみで動作継続。 |
| **設定管理** | `tmux list-panes` による自動検出 | `config.json` 手動編集を排除。tmux 起動即座に設定完了。 |

---

## 3. ディレクトリ構成

### 📦 リポジトリ構成（バージョン管理対象）
```
agentpost/                          # プロジェクト(リポジトリ)ルート
├── agentpost.py                    # CLI & コアエンジン（システム実行用）
├── skill/
│   └── agentpost.py                # AI CodingAgent 向けスキル（Python import 用）
└── install.sh                      # 環境構築＆PATH 設定スクリプト
```

### 💾 実行環境構成（`~/.agentpost/` に自動生成）
```
~/.agentpost/
├── config.json                     # エージェント/paneマッピング（自動生成）
├── agents/
│   ├── qwen/
│   │   ├── inbox/                  # 未読
│   │   ├── processing/             # 処理中（クラッシュリカバリ用）
│   │   └── archive/                # 処理済みログ
│   ├── gemini/
│   └── ...
└── logs/
    └── agentpost.log               # 運用ログ
```

---

## 4. 実装ソースコード

### 4.1 `agentpost.py` （CLI & コアエンジン）
システム全体の制御、ファイルI/O、CLI パーシング、受信リスナーを担う。
```python
#!/usr/bin/env python3
"""
AgentPost: tmux-based async messaging for AI Coding Agents.
CLI & Core Engine (Single File)
"""
import sys, os, json, time, subprocess, argparse, logging
from pathlib import Path
from typing import Optional, List, Literal
from datetime import datetime, timezone

# ─── 環境・パス解決 ─────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
os.environ.setdefault("AGENTPOST_BASE", str(Path.home() / ".agentpost"))
BASE_DIR = Path(os.environ["AGENTPOST_BASE"])
CONFIG_FILE = BASE_DIR / "config.json"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "agentpost.log"

if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

# ─── ロギング ──────────────────────────────────────────────────
def _init_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
            logging.StreamHandler(sys.stderr)
        ]
    )
    os.umask(0o077)

logger = logging.getLogger("agentpost")

# ─── ユーティリティ ─────────────────────────────────────────────
def tmux_cmd(args: List[str]) -> str:
    if "TMUX" not in os.environ: return ""
    res = subprocess.run(["tmux"] + args, capture_output=True, text=True, check=False)
    return res.stdout.strip() if res.returncode == 0 else ""

def load_config() -> dict:
    if not CONFIG_FILE.exists():
        logger.error("Config not found. Run `agentpost setup` first.")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_config(cfg: dict):
    tmp = CONFIG_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f: json.dump(cfg, f, indent=2, ensure_ascii=False)
    os.rename(tmp, CONFIG_FILE)
    os.chmod(CONFIG_FILE, 0o600)

def ensure_agent_dirs(agent: str):
    for sub in ["inbox", "processing", "archive"]:
        (BASE_DIR / "agents" / agent / sub).mkdir(parents=True, exist_ok=True)

# ─── 自動検出 & セットアップ ────────────────────────────────────
def detect_agents() -> List[dict]:
    raw = tmux_cmd(["list-panes", "-a", "-F", "#S:#I:#P #{pane_current_command} #{pane_title}"])
    agents, seen = [], set()
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) < 3: continue
        combined = " ".join(parts[1:]).lower()
        name = None
        if "qwen" in combined: name = "qwen"
        elif "gemini" in combined: name = "gemini"
        elif any(k in combined for k in ["vibe", "mistral"]): name = "vibe"
        elif any(k in combined for k in ["claude", "anthropic"]): name = "claude"
        elif any(k in combined for k in ["cursor", "copilot"]): name = "cursor"
        else: continue
        if name not in seen:
            seen.add(name)
            sess, pane = (parts[0].split(":") + ["default", "0.0"])[:2]
            agents.append({"name": name, "pane": pane, "session": sess})
    return agents

def cmd_setup(args):
    _init_logging()
    agents = detect_agents()
    if not agents:
        logger.warning("No agents detected. Using fallback 'default' agent.")
        agents = [{"name": "default", "pane": "0.0", "session": "default"}]
    cfg = {
        "version": 1, "auto_update": True, "agents": agents,
        "defaults": {"priority": "normal", "ttl_seconds": 86400},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    save_config(cfg)
    logger.info(f"✅ Config saved. Detected {len(agents)} agents:")
    for a in agents: logger.info(f"   • {a['name']} -> pane {a['pane']} ({a['session']})")

# ─── メッセージ送信 (API & CLI 共有) ───────────────────────────
def post(
    to: str, body: str, *, from_agent: Optional[str] = None,
    msg_type: Literal["task", "info", "question", "ack"] = "task",
    priority: Literal["low", "normal", "high", "urgent"] = "normal",
    ref: Optional[str] = None, reply_to: Optional[str] = None,
    ttl: Optional[int] = None
) -> str:
    _init_logging()
    cfg = load_config()
    from_agent = from_agent or os.getenv("AGENTPOST_AGENT", "unknown")
    if ttl is None: ttl = cfg.get("defaults", {}).get("ttl_seconds", 86400)
    ensure_agent_dirs(to)

    msg_id = f"msg_{int(time.time()*1000)}_{os.getpid()}"
    ref_obj = None
    if ref:
        s, i = (ref.split(":", 1) + [ref])[:2] if ":" in ref else ("br", ref)
        ref_obj = {"system": s, "issue_id": i}

    msg = {
        "version": 1, "id": msg_id, "from": from_agent, "to": to,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "type": msg_type, "priority": priority, "body": body,
        "ref": ref_obj, "reply_to": reply_to, "ttl_seconds": ttl
    }

    inbox = BASE_DIR / "agents" / to / "inbox"
    tmp, dest = inbox / f".{msg_id}.tmp", inbox / f"{msg_id}.json"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(msg, f, ensure_ascii=False, indent=2)
    os.rename(tmp, dest)
    os.chmod(dest, 0o600)

    try: tmux_cmd(["display-message", f"📤 AgentPost → {to}: {body[:40]}..."])
    except: pass
    logger.info(f"Posted to {to}: {msg_id}")
    return msg_id

# ─── 受信処理 & リゾルバー ─────────────────────────────────────
def resolve_ref(msg: dict) -> str:
    ref = msg.get("ref")
    if not ref: return msg["body"]
    sys_name, iid, repo = ref.get("system", ""), ref.get("issue_id", ""), ref.get("repo_path", ".")
    prefix = f"[{sys_name or 'ref'}:{iid}]"
    if sys_name == "br":
        try:
            res = subprocess.run(["br", "show", iid, "--json", "-C", repo], capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                data = json.loads(res.stdout)
                return f"{prefix} {data.get('title', iid)}\n{msg['body']}"
        except: pass
    return f"{prefix} {msg['body']}"

def process_inbox(agent: str, mark_read: bool = True) -> List[dict]:
    inbox = BASE_DIR / "agents" / agent / "inbox"
    proc = BASE_DIR / "agents" / agent / "processing"
    archive = BASE_DIR / "agents" / agent / "archive"
    if not inbox.exists(): return []

    msgs = []
    for f in sorted(inbox.glob("*.json")):
        if f.name.startswith("."): continue
        try:
            with open(f, "r", encoding="utf-8") as fh: msg = json.load(fh)
            ts = datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
            if (datetime.now(timezone.utc) - ts).total_seconds() > msg.get("ttl_seconds", 86400):
                f.unlink(); continue

            os.rename(f, proc / f.name)
            msgs.append(msg)
            if mark_read:
                time.sleep(0.05)
                os.rename(proc / f.name, archive / f.name)
        except Exception as e:
            logger.error(f"Failed to process {f}: {e}")
    return msgs

# ─── リスナー (watchdog 優先 / ポーリングフォールバック) ──────
def cmd_listen(args):
    _init_logging()
    agent = args.agent or os.getenv("AGENTPOST_AGENT")
    if not agent:
        logger.error("Agent name not specified. Use --agent or set AGENTPOST_AGENT.")
        sys.exit(1)
    ensure_agent_dirs(agent)
    logger.info(f"👂 AgentPost listener started for '{agent}'. (Ctrl+C to stop)")

    proc = BASE_DIR / "agents" / agent / "processing"
    if proc.exists():
        for f in proc.glob("*.json"):
            os.rename(f, BASE_DIR / "agents" / agent / "inbox" / f.name)
        logger.info("🔄 Recovered crashed messages from processing/ to inbox/")

    def handle_new():
        msgs = process_inbox(agent, mark_read=True)
        for m in msgs:
            display = resolve_ref(m)
            print(f"\n📩 [{m['type'].upper()}] from:{m['from']} | {display}")
            try: tmux_cmd(["display-message", f"📩 {m['from']}: {m['body'][:30]}..."])
            except: pass

    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        use_watchdog = True
    except ImportError:
        logger.info("⚠️  watchdog not found. Falling back to polling (0.5s).")
        use_watchdog = False

    if use_watchdog:
        class Handler(FileSystemEventHandler):
            def on_created(self, event):
                if event.is_directory or not event.src_path.endswith(".json"): return
                handle_new()
        observer = Observer()
        observer.schedule(Handler(), str(BASE_DIR / "agents" / agent / "inbox"), recursive=False)
        observer.start()
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt: observer.stop()
        observer.join()
    else:
        try:
            while True: handle_new(); time.sleep(0.5)
        except KeyboardInterrupt: pass

# ─── ステータス & ログ ─────────────────────────────────────────
def cmd_status(args):
    _init_logging(); cfg = load_config()
    for a in cfg.get("agents", []):
        inbox = BASE_DIR / "agents" / a["name"] / "inbox"
        count = len(list(inbox.glob("*.json"))) if inbox.exists() else 0
        print(f"{'✅' if count == 0 else '📬'} {a['name']}: {count} unread | pane {a['pane']}")

def cmd_log(args):
    if not LOG_FILE.exists(): print("No logs found."); return
    tail = int(args.tail) if args.tail else 20
    with open(LOG_FILE, "r", encoding="utf-8") as f: print("".join(f.readlines()[-tail:]))

# ─── スキル API (import agentpost で利用可能) ──────────────────
def check(agent: Optional[str] = None, mark_read: bool = True) -> List[dict]:
    _init_logging()
    target = agent or os.getenv("AGENTPOST_AGENT")
    return process_inbox(target, mark_read) if target else []

def listen_loop(agent: Optional[str] = None, callback=None):
    _init_logging()
    target = agent or os.getenv("AGENTPOST_AGENT")
    if not target: return
    while True:
        for m in process_inbox(target, mark_read=False):
            if callback: callback(m)
            else: print(f"\n📩 {m['body']}")
        process_inbox(target, mark_read=True)
        time.sleep(0.5)

# ─── CLI エントリポイント ───────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(prog="agentpost", description="Async messaging for AI Coding Agents")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("setup", help="Auto-detect tmux panes & generate config")
    p_post = sub.add_parser("post", help="Send a message")
    p_post.add_argument("--to", required=True); p_post.add_argument("--from", dest="from_agent")
    p_post.add_argument("--type", default="task"); p_post.add_argument("--priority", default="normal")
    p_post.add_argument("--ref"); p_post.add_argument("--reply-to"); p_post.add_argument("--ttl", type=int)
    p_post.add_argument("body", nargs="?", default="")
    p_listen = sub.add_parser("listen", help="Start receiving messages")
    p_listen.add_argument("--agent")
    sub.add_parser("status", help="Show unread counts")
    p_log = sub.add_parser("log", help="Show recent logs"); p_log.add_argument("--tail", type=int, default=20)

    args = parser.parse_args()
    if args.command == "setup": cmd_setup(args)
    elif args.command == "post":
        if not args.body: args.body = sys.stdin.read().strip()
        post(args.to, args.body, from_agent=args.from_agent, msg_type=args.type,
             priority=args.priority, ref=args.ref, reply_to=args.reply_to, ttl=args.ttl)
    elif args.command == "listen": cmd_listen(args)
    elif args.command == "status": cmd_status(args)
    elif args.command == "log": cmd_log(args)
    else: parser.print_help()

if __name__ == "__main__":
    main()
```

---

### 4.2 `skill/agentpost.py` （AI CodingAgent 向けスキル）
エージェントの生成コード内で `from skill.agentpost import post, check` と呼ぶための軽量ラッパー。  
**親ディレクトリの `agentpost.py` を動的に読み込み、機能の重複をゼロにする**設計。
```python
#!/usr/bin/env python3
"""
AgentPost Skill for AI Coding Agents.
Thin wrapper that dynamically imports the core engine from the parent directory.
Usage inside Agent Code:
    from skill.agentpost import post, check, listen_loop
"""
import sys
from pathlib import Path

# リポジトリルート(../) を sys.path に追加し、コアエンジンを確実に import 可能にする
_core_dir = Path(__file__).resolve().parent.parent
if str(_core_dir) not in sys.path:
    sys.path.insert(0, str(_core_dir))

from agentpost import post, check, listen_loop

__all__ = ["post", "check", "listen_loop"]
```

---

### 4.3 `install.sh` （環境セットアップ）
シンボリックリンクの作成、環境変数の追記、`watchdog` の自動インストールを行う。
```bash
#!/usr/bin/env bash
set -e

AP_DIR="$HOME/.agentpost"
BIN_DIR="$HOME/.local/bin"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "📦 Installing AgentPost..."
mkdir -p "$AP_DIR" "$BIN_DIR" "$AP_DIR/logs"

# シンボリックリンク作成（CLI コマンドとして利用可能に）
ln -sf "$REPO_DIR/agentpost.py" "$BIN_DIR/agentpost"
chmod +x "$REPO_DIR/agentpost.py"

# 環境変数追記 (重複防止)
SHELL_RC="$HOME/.$(basename $SHELL)rc"
if ! grep -q "AGENTPOST_BASE" "$SHELL_RC" 2>/dev/null; then
    echo "export AGENTPOST_BASE=\"$AP_DIR\"" >> "$SHELL_RC"
    echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_RC"
    echo "📝 Added PATH & AGENTPOST_BASE to $SHELL_RC"
    echo "   ⚠️  Run: source $SHELL_RC"
fi

# 依存チェック (watchdog オプション)
if ! python3 -c "import watchdog" 2>/dev/null; then
    echo "📦 Installing watchdog for event-driven listening..."
    pip3 install --user watchdog >/dev/null 2>&1
fi

echo "✅ AgentPost installed. Run: agentpost setup"
```

---

## 5. 使い方 & YOLO モード運用ガイド

### ① 初回セットアップ
```bash
# 1. tmux セッション開始 & 各 pane で AI エージェント起動
tmux new-session -s coding
# Pane 1.1: Qwen, Pane 2.1: Gemini, etc.

# 2. 任意の pane でリポジトリを取得＆インストール
git clone <your-repo> agentpost
cd agentpost
bash install.sh
source ~/.bashrc  # or ~/.zshrc

# 3. 設定自動生成（tmux pane を自動検出）
agentpost setup
```

### ② 受信リスナーの常駐（YOLO モードの核）
各エージェントの tmux pane 内で実行。`watchdog` がインストールされていればイベント駆動、未インストールでも 0.5s ポーリングで自動動作。
```bash
agentpost listen --agent qwen &
agentpost listen --agent gemini &
```

### ③ 送信方法（2パターン）
**A. CLI 直接実行（デバッグ・人間確認用）**
```bash
agentpost post --to gemini "bd-a1b2c3 のバリデーション実装、お願いします"
```

**B. エージェント生成コード内（Skill 利用）**
AI のプロンプトに以下を埋め込み、自律実行させる。
```python
from skill.agentpost import post, check

# 他エージェントへタスク委任
post(
    to="gemini",
    body="bd-a1b2c3 のログイン機能を実装してください",
    ref="br:bd-a1b2c3",
    msg_type="task",
    priority="high"
)

# 新着チェック & 返信処理
for msg in check():
    if msg["type"] == "task":
        # 実際の処理ロジック...
        print("Processing task...")
        post(to=msg["from"], body="完了しました", msg_type="ack", reply_to=msg["id"])
```

---

## 6. 重要な設計ポイント

| 項目 | 実装方針 | YOLO モードでの効果 |
|------|----------|-------------------|
| **ファイル分離** | リポジトリ(`agentpost/`) と 実行データ(`~/.agentpost/`) を明確に分離 | コードは Git 管理、セッション固有データは環境隔離。安全な共有・デプロイが可能 |
| **2つの `agentpost.py`** | `agentpost.py` = インフラ層 / `skill/agentpost.py` = エージェント用ラッパー | ロジック重複ゼロ。エージェントは `import skill.agentpost` だけで自律通信開始 |
| **原子操作キュー** | `tmp → rename` 書き込み / `inbox→processing→archive` 状態遷移 | LLM プロセスが `SIGKILL` されても、メッセージ消失・重複・破損ゼロ |
| **`ref` オプショナル** | `br` 連携は `try/except` で囲み、失敗時は `body` 単体で継続 | 外部ツール未導入環境でもシステム全体が停止しない。段階的導入に対応 |
| **自動リカバリ** | `listen` 起動時に `processing/` 残骸を `inbox/` に戻す | クラッシュ後の手動リカバリ作業不要。完全な自律ループを維持 |

この仕様書と実装コード一式をリポジトリに配置し、`bash install.sh` → `agentpost setup` → `agentpost listen &` を実行するだけで、tmux 上の CodingAgent は**人間を介さず自律協調**を開始します。
