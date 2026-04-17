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
            print(f"STDERR: {line.decode().strip()}", file=sys.stderr)

    asyncio.create_task(read_stderr())

    # 1. Initialize
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0.0"}
        }
    }
    proc.stdin.write(json.dumps(init_req).encode() + b"\n")
    await proc.stdin.drain()
    
    resp = await proc.stdout.readline()
    print(f"INIT RESP: {resp.decode().strip()}")

    # 2. List tools
    list_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    proc.stdin.write(json.dumps(list_req).encode() + b"\n")
    await proc.stdin.drain()
    
    resp = await proc.stdout.readline()
    print(f"LIST RESP: {resp.decode().strip()}")

    proc.terminate()
    await proc.wait()

if __name__ == "__main__":
    asyncio.run(main())
