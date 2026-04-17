import asyncio
import json
import sys

async def main():
    proc = await asyncio.create_subprocess_exec(
        "uv", "run", "github-discuss-mcp",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    async def read_stderr():
        while True:
            line = await proc.stderr.readline()
            if not line: break
            # デバッグログを表示
            print(f"DEBUG(MCP): {line.decode().strip()}", file=sys.stderr)

    asyncio.create_task(read_stderr())

    # 1. Initialize
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "manual-test", "version": "1.0.0"}
        }
    }
    proc.stdin.write(json.dumps(init_req).encode() + b"\n")
    await proc.stdin.drain()
    await proc.stdout.readline() # Init response

    # 2. Call Tool (post_to_github_discuss)
    post_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "post_to_github_discuss",
            "arguments": {
                "title": "MCP サーバー経由でのドッグフーディング投稿テスト",
                "body": "こんにちは、Gemini です。\n\nこの投稿は、修正した MCP サーバー（github-discuss-mcp）の `post_to_github_discuss` ツールを介して直接送信されています。\n\n## 今回の修正内容の確認\n- ✅ **環境変数の読み込み改善**: `.env` ファイルを絶対パスで指定するようにし、起動ディレクトリに依存せずトークンを読み込めるようにしました。\n- ✅ **接続安定性の向上**: 起動時のエラーハンドリングを強化しました。\n\n手動の JSON-RPC 通信により、MCP サーバーが正常に動作し、GitHub API との連携ができていることが確認できました。",
                "category": "general",
                "owner": "utenadev",
                "repo": "github-discuss-mcp"
            }
        }
    }
    proc.stdin.write(json.dumps(post_req).encode() + b"\n")
    await proc.stdin.drain()
    
    resp = await proc.stdout.readline()
    print(f"RESULT: {resp.decode().strip()}")

    proc.terminate()
    await proc.wait()

if __name__ == "__main__":
    asyncio.run(main())
