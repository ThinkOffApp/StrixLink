# tools

Small one-off utilities from the [StrixLink](../) project. StrixLink is a measured study of
running one large language model across two machines that are not supposed to work together:
an Apple Silicon Mac and an AMD Strix Halo box, joined by a single Thunderbolt cable.

## `dsv41-inject-engram.py`

**If you arrived here from the llama.cpp pull request, read this first: you probably do not need
this script any more.** The GGUF author shipped an official repair and a fixed converter on
2026-09-11, shortly after this was written. Use those. This script is kept for the record, and for
anyone still holding a file converted *before* that repair.

### What the problem was

DeepSeek-V4.1-Flash needs five "engram" constants in the GGUF for its n-gram memory to work:
`multipliers`, `primes`, `offsets`, `token_map` and `pad_id`. Every V4.1 GGUF published before
2026-09-11 was converted with a patch that wrote only four older `deepseek4.engram.*` keys, so the
runtime refused to load any of them:

```
error loading model hyperparameters: key not found in model: deepseek41.engram.layer_ids
array key not found in model: deepseek41.engram.multipliers
```

Re-converting from the source weights means a 700 GB FP8 job, which most people cannot do.

### Why it did not need a re-conversion

Those five constants are **deterministic functions of `config.json` and the tokenizer**, never of
the weights. The multipliers come from a fixed per-layer seed, the primes from a sieve above the
engram vocabulary size, and the token map from the tokenizer's own normalizer. So they can be
recomputed exactly and written into a copy of shard 1, which is the shard carrying the
hyperparameters. Tensor bytes are copied unchanged.

We verified this the only way that counts: when the author published his official repair, we ran it
on the same original file and compared field by field. All nine engram keys came out identical,
same values and same types. The reconstruction was exact.

### What it does not fix

Loading is not running. With the constants injected the model loads and generates, but on a runtime
without the CSA2 sparse attention it emits one token repeated, because the forward pass is not
V4.1's yet. That is a runtime gap, not a file gap.

```bash
python3 dsv41-inject-engram.py <hf-model-dir> <in-shard-1.gguf> <out-shard-1.gguf>
```

## More from this project

- [StrixLink](../) — the Thunderbolt link itself: measured throughput, the transport ladder, and the
  raw logs behind the M5² benchmark tables.
- [mac-amd-llm-cluster](https://github.com/ThinkOffApp/mac-amd-llm-cluster) — the recipe: running a
  321B model across the Mac and the Strix box, with every number measured.
