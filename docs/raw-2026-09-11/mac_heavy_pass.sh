#!/bin/bash
# Mac-heavy split pass for the three big GLM files (claudemm, 2026-09-10 evening). Self-contained: no waiting on anyone.
# Mac client (Metal) + M5 RPC device (Vulkan) on PR 27754 both ends. -ts order is RPC0/MTL0 (remote devices FIRST, measured Sep 11: 67/33 put 94 GB on the M5), so the M5 share comes first.
B=~/llama-glm5-27754/build/bin; RPC=10.55.0.2:50052; OUT=~/work/strixlink-bench-split; mkdir -p $OUT
LOG=$OUT/mac-heavy-pass-$(date -u +%Y%m%dT%H%MZ).log; exec > >(tee -a $LOG) 2>&1
echo "START $(date -u +%FT%TZ) host=$(hostname) build=$($B/llama-bench --version 2>&1 | head -1)"
run_row() { # name  first-shard  ts
  local name=$1 m=$2 ts=$3
  echo "## $name split Mac-heavy -ts $ts  $(date -u +%FT%TZ)"
  $B/llama-bench -m "$m" --rpc $RPC -ts $ts -p 512 -n 128 -r 3 -o md -v 2> $OUT/$name-load.err
  echo "buffers:"; grep -E "model buffer size|(Metal|RPC).*buffer" $OUT/$name-load.err | head -6
  echo "sample:"; $B/llama-completion -m "$m" --rpc $RPC -ts $ts -p "Explain in three sentences why the sky is blue." -n 64 --temp 0 -no-cnv 2>/dev/null | tail -4
  echo "GLM-ROW-DONE $name $(date -u +%FT%TZ)"
}
run_row Q3_K_XL-148GB ~/models/GLM-Q3_K_XL/GLM-5.3-Flash-UD-Q3_K_XL-00001-of-00004.gguf 33/67
run_row IQ4_XS-157GB  ~/models/GLM-IQ4_XS/GLM-5.3-Flash-UD-IQ4_XS-00001-of-00005.gguf 37/63
run_row Q4_K_XL-200GB "$(ls ~/models/GLM-Q4_K_XL/*00001-of-*.gguf | head -1)" 48/52
echo "ALL-DONE $(date -u +%FT%TZ)"
