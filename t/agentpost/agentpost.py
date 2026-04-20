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

# 1. 環境変数優先
if "AGENTPOST_BASE" not in os.environ:
    # 2. 同ディレクトリ & 親ディレクトリの .env を探索
    for env_path in [_SCRIPT_DIR / ".env", _SCRIPT_DIR.parent / ".env"]:
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("AGENTPOST_BASE="):
                        os.environ["AGENTPOST_BASE"] = line.split("=", 1)[1].strip('"')
                        break
            if "AGENTPOST_BASE" in os.environ: break

# 3. 最終フォールバック
_env_base = os.environ.get("AGENTPOST_BASE")
if _env_base:
    BASE_DIR = Path(_env_base)
elif (_SCRIPT_DIR / ".agentpost").exists():
    BASE_DIR = _SCRIPT_DIR / ".agentpost"
else:
    BASE_DIR = Path.home() / ".agentpost"
    os.environ.setdefault("AGENTPOST_BASE", str(BASE_DIR))

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
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f: json.dump(cfg, f, indent=2, ensure_ascii=False)
    os.rename(tmp, CONFIG_FILE)
    os.chmod(CONFIG_FILE, 0o600)

def ensure_agent_dirs(agent: str):
    for sub in ["inbox", "processing", "archive"]:
        (BASE_DIR / "agents" / agent / sub).mkdir(parents=True, exist_ok=True)

# ─── 自動検出 & セットアップ ────────────────────────────────────
def detect_agents() -> List[dict]:
    # パイプ区切りで確実に分割（コマンド/ウィンドウ名にスペースが含まれても安全）
    fmt = "#{session_name}|#{window_index}|#{pane_index}|#{window_name}|#{pane_current_command}|#{pane_title}"
    raw = tmux_cmd(["list-panes", "-a", "-F", fmt])
    
    agents, seen = [], set()
    for line in raw.splitlines():
        parts = line.split("|")
        if len(parts) < 6: continue
        
        sess, win_idx, pane_idx, win_name, cmd, title = (
            parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
        )
        combined = f"{cmd} {title}".lower()

        name = None
        if "qwen" in combined: name = "qwen"
        elif "gemini" in combined: name = "gemini"
        elif any(k in combined for k in ["vibe", "mistral"]): name = "vibe"
        elif any(k in combined for k in ["claude", "anthropic"]): name = "claude"
        elif any(k in combined for k in ["cursor", "copilot"]): name = "cursor"
        else: continue

        if name not in seen:
            seen.add(name)
            agents.append({
                "name": name,
                "session": sess.strip(),
                "window": int(win_idx),
                "window_name": win_name.strip(),
                "pane": int(pane_idx)
            })
    return agents

def cmd_setup(args):
    _init_logging()
    agents = detect_agents()
    
    # 自動検出は参考情報として表示
    print("📋 Detected agents (reference only):")
    if not agents:
        print("   No agents detected.")
    for a in agents:
        print(f"   • {a['name']} -> session {a['session']}, window {a['window']}, pane {a['pane']}")
    
    print("")
    print("✏️  Enter agent panes (format: name=window.pane)")
    print("   Example: qwen=1.1, gemini=2.1, vibe=3.1")
    print("")
    
    agents = []
    while True:
        try:
            line = input("   Agent (or Enter to finish): ").strip()
        except EOFError:
            break
        
        if not line:
            break
        
        if '=' in line:
            name, pane = line.split('=', 1)
            # Parse session.window.pane or window.pane
            parts = pane.split('.')
            if len(parts) == 2:
                sess, win = "0", parts[0]
                p = parts[1]
            elif len(parts) == 3:
                sess, win, p = parts
            else:
                print(f"   ⚠️  Invalid format. Use window.pane or session.window.pane")
                continue
            
            agents.append({
                "name": name.strip(),
                "session": sess.strip(),
                "window": int(win),
                "pane": int(p)
            })
            print(f"   ✓ Added: {name} -> session {sess}, window {win}, pane {p}")
    
    if not agents:
        print("   ⚠️  No agents configured.")
        return
    
    # 保存
    cfg = {
        "version": 1,
        "auto_update": False,
        "agents": agents,
        "defaults": {"priority": "normal", "ttl_seconds": 86400}
    }
    save_config(cfg)
    print("")
    print(f"✅ Config saved with {len(agents)} agents")
    
    # tmux ウィンドウ作成（オプション）
    if hasattr(args, 'tmux') and args.tmux:
        try:
            tmux_cmd(["new-window", "-n", "agentpost"])
            print("✅ Created tmux window 'agentpost'")
        except:
            pass
    
    print("")
    print("📋 Next steps:")
    print("   1. tmux new-window -n agentpost")
    print("   2. agentpost listen --agent <name>")
    print("   3. Ctrl+b, \" (split pane vertically)")
    print("   4. agentpost listen --agent <another-name>")

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
            
            # timestamp キーの存在チェック
            if "timestamp" not in msg:
                logger.warning(f"Message {f.name} has no timestamp. Skipping.")
                continue
            
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
    p_setup = sub.add_parser("setup", help="Auto-detect tmux panes & generate config")
    p_setup.add_argument("--tmux", action="store_true", help="Create tmux window")
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
