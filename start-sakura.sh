#!/usr/bin/env bash
# For the Ollama user service configured on the translation server.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$ROOT/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
    echo "Missing Python environment: $ROOT/.venv" >&2
    exit 1
fi

echo "Starting Ollama..."
systemctl --user start ollama-sakura.service

"$PYTHON" - <<'PY'
import sys
import time

import requests

base = "http://127.0.0.1:11434"
try:
    for attempt in range(30):
        try:
            requests.get(f"{base}/api/tags", timeout=2).raise_for_status()
            break
        except requests.RequestException:
            if attempt == 29:
                raise
            time.sleep(1)

    print("Loading sakura (the first load may take a few minutes)...", flush=True)
    response = requests.post(
        f"{base}/api/generate",
        json={
            "model": "sakura:latest",
            "prompt": "",
            "stream": False,
            "keep_alive": -1,
            "options": {"num_ctx": 4096},
        },
        timeout=(10, 600),
    )
    response.raise_for_status()
    result = response.json()
    if result.get("error"):
        raise RuntimeError(result["error"])
    if not result.get("done"):
        raise RuntimeError(f"Unexpected response: {result}")
except (requests.RequestException, ValueError, RuntimeError) as exc:
    print(f"Startup failed: {exc}", file=sys.stderr)
    print("Logs: journalctl --user -u ollama-sakura.service -n 50", file=sys.stderr)
    sys.exit(1)

print("Sakura is ready and will stay loaded until stopped.")
PY

printf '\nTranslate with:\n  cd %q\n  source .venv/bin/activate\n  python single/sakura.py -s /data/ichinoe/ranobe-tools/src -d /data/ichinoe/ranobe-tools/dst\n' "$ROOT"
printf '\nStop and release model memory:\n  systemctl --user stop ollama-sakura.service\n'
