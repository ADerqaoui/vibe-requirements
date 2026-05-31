#!/usr/bin/env bash
# Start the frontend on http://localhost:5173 (also LAN-reachable via --host).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/frontend"
export PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH"
[ -d node_modules ] || pnpm install
fuser -k 5173/tcp 2>/dev/null || true   # free a stale port if needed
exec pnpm dev --host
