#!/usr/bin/env python3
"""Run a local engineering script using the already-running Fusion API add-in."""
import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser()
parser.add_argument("script", type=Path)
parser.add_argument("--description", required=True)
parser.add_argument("--url", default="http://127.0.0.1:8765/mcp",
                    help="Existing Fusion endpoint; alternate local interface avoids a conflicting loopback listener")
args = parser.parse_args()
payload = {
    "jsonrpc": "2.0", "id": 1, "method": "tools/call",
    "params": {"name": "execute_python", "arguments": {
        "code": args.script.read_text(), "description": args.description,
        "session_id": "so101_calligraphy", "persistent": False,
    }},
}
request = Request(args.url, data=json.dumps(payload).encode(),
                  headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
with urlopen(request, timeout=180) as response:
    for line in response:
        line = line.decode().strip()
        if not line.startswith("data:"):
            continue
        result = json.loads(line[5:])
        for block in result.get("result", {}).get("content", []):
            if block.get("type") == "text":
                try:
                    body = json.loads(block["text"])
                    print(body.get("stdout", ""), end="")
                    if not body.get("success", False):
                        print(json.dumps(body, ensure_ascii=False, indent=2))
                        raise SystemExit(1)
                except json.JSONDecodeError:
                    print(block["text"])
        if "error" in result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            raise SystemExit(1)
        if result.get("id") == 1:
            break
