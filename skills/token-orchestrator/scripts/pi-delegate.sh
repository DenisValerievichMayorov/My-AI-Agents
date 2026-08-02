#!/usr/bin/env bash
# pi-delegate.sh — non-interactive pi for orchestrators
set -euo pipefail
PROMPT="${1:-}"
MODEL="${2:-}"
if [[ -z "$PROMPT" ]]; then
  echo "Usage: pi-delegate.sh \"prompt\" [model]" >&2
  exit 1
fi
if ! command -v pi >/dev/null 2>&1; then
  echo "pi not found — run: bash ~/Sync/Scripts/install_pi_agent_linux.sh" >&2
  exit 1
fi
echo "=== pi delegate ==="
if [[ -n "$MODEL" ]]; then
  pi -p "$PROMPT" --model "$MODEL" --no-session
else
  pi -p "$PROMPT" --no-session
fi