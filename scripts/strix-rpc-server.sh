#!/usr/bin/env bash
# Strix side: expose this machine's GPU to the Mac's llama.cpp over the TB
# link. SECURITY: the RPC protocol has NO authentication - bind ONLY to the
# point-to-point Thunderbolt address, never 0.0.0.0 or a LAN interface.
set -euo pipefail

STRIX_IP="${STRIX_IP:-10.55.0.2}"
PORT="${PORT:-50052}"
RPC_SERVER="${RPC_SERVER:-$HOME/llama.cpp/build/bin/rpc-server}"

exec "$RPC_SERVER" --host "$STRIX_IP" --port "$PORT"
