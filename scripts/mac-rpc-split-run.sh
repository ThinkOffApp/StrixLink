#!/usr/bin/env bash
# Mac side: run one model split across the Mac's Metal GPU and the Strix GPU
# reached over the TB link. Requires a llama.cpp build with -DGGML_RPC=ON
# (the rpc-server binary has no dedicated make target - build the full set).
set -euo pipefail

MODEL="${MODEL:?set MODEL=/path/to/model.gguf}"
STRIX_RPC="${STRIX_RPC:-10.55.0.2:50052}"
LLAMA_CLI="${LLAMA_CLI:-$HOME/llm-bench/llama.cpp/build/bin/llama-cli}"

exec "$LLAMA_CLI" -m "$MODEL" --rpc "$STRIX_RPC" -ngl 99 "$@"
