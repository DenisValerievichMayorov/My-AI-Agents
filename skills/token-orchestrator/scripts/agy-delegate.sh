#!/usr/bin/env bash
# agy-delegate.sh — non-interactive agy for orchestrators (Termux / Linux)
set -euo pipefail
PROMPT="${1:-}"
if [[ -z "$PROMPT" ]]; then
  echo "Usage: agy-delegate.sh \"prompt\"" >&2
  exit 1
fi
export PATH="$HOME/.local/bin:$HOME/bin:$PATH"
AGY="$(command -v agy 2>/dev/null || echo "$HOME/bin/agy")"
if [[ ! -x "$AGY" ]]; then
  echo "agy not found — run: bash ~/Sync/Scripts/install_agy_unix.sh" >&2
  exit 1
fi
echo "=== agy delegate ==="
"$AGY" --print --dangerously-skip-permissions -p "$PROMPT"