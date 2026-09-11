#!/bin/bash
# One GLM split row, size-guarded: glm-row.sh <name> <model-dir> <first-shard> <ts M5/Mac>. M5 share = size*a/(a+b) must be <= 110 GB.
set -e
name=$1 dir=$2 shard=$3 ts=$4; a=${ts%/*}; b=${ts#*/}
B=~/llama-glm5-27754/build/bin; RPC=10.55.0.2:50052; OUT=~/work/strixlink-bench-split; LOG=$OUT/row-$name-$(date -u +%Y%m%dT%H%MZ).log
bytes=$(stat -f %z ~/models/$dir/*.gguf | awk '{s+=$1} END{print s}'); gb=$((bytes/1000000000)); m5=$((gb*a/(a+b))); mac=$((gb-m5))
echo "$name: $gb GB, -ts $ts -> M5 $m5 GB, Mac $mac GB" | tee -a $LOG
[ $m5 -le 110 ] || { echo "REFUSED: M5 share $m5 > 110" | tee -a $LOG; exit 3; }
echo "## $name split -ts $ts (M5/Mac)  $(date -u +%FT%TZ)" >> $LOG
$B/llama-bench -m ~/models/$dir/$shard --rpc $RPC -ts $ts -p 512 -n 128 -r 3 -o md -v 2> $OUT/$name-load.err >> $LOG || echo "BENCH-FAILED code=$?" >> $LOG
grep -E "model buffer size|Insufficient|status 5|abort" $OUT/$name-load.err | head -8 >> $LOG
echo "GLM-ROW-DONE $name $(date -u +%FT%TZ)" >> $LOG
