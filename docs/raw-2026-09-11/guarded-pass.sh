#!/bin/bash
# Size guard for mac_heavy_pass.sh: -ts order is RPC0/MTL0 (M5 FIRST), so the M5 share is size * a/(a+b) for -ts a/b; must stay under 110 GB.
set -e
check() { local dir=$1 ts=$2; local a=${ts%/*} b=${ts#*/}
  local bytes=$(stat -f %z ~/models/$dir/*.gguf | awk '{s+=$1} END{print s}')
  local gb=$(( bytes / 1000000000 )); local share=$(( gb * a / (a + b) ))
  echo "$dir: ${gb} GB, -ts $ts -> M5 share ${share} GB"
  [ "$share" -le 110 ] || { echo "REFUSED: M5 share ${share} GB > 110 GB"; exit 3; }
}
check GLM-Q3_K_XL 33/67; check GLM-IQ4_XS 37/63; check GLM-Q4_K_XL 48/52
grep -q -- " 33/67" ~/mac_heavy_pass.sh && grep -q -- " 37/63" ~/mac_heavy_pass.sh && grep -q -- " 48/52" ~/mac_heavy_pass.sh
echo "GUARD OK $(date -u +%FT%TZ)"
exec ~/mac_heavy_pass.sh
