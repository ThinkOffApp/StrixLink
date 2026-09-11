#!/usr/bin/env python3
"""Inject the DeepSeek V4.1 engram constants into a stale GGUF shard 1 (claudeMB, 2026-09-11).

The runtime branch (vcruz305/llama.cpp runtime/deepseek41) requires five engram constants that the
published GGUFs lack. They are deterministic functions of config.json + the tokenizer, never of the
weights, so they can be reproduced exactly as conversion/deepseek.py computes them and written into a
copy of shard 1 (the shard that carries the hyperparameters). Tensor bytes are copied unchanged.
Also renames the four stale `deepseek4.engram.*` keys to `deepseek41.engram.*`.
"""
import json, sys, os
sys.path.insert(0, os.path.expanduser('~/llama-dsv41/gguf-py'))
import numpy as np
import gguf
from gguf import GGUFReader, GGUFWriter, GGUFValueType
from tqdm import tqdm

src_dir, in_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
cfg = json.load(open(os.path.join(src_dir, 'config.json')))
h = dict(cfg); h.update(cfg.get('text_config') or {})          # _v41_flatten_hparams
arch = 'deepseek41'
layer_ids = tuple(h['engram_layer_ids']); max_ngram = h['engram_max_ngram_size']; n_heads = h['engram_n_heads']
engram_vocab = h['engram_vocab_size']; expected_cvs = h['engram_compressed_vocab_size']; pad_raw = h.get('engram_pad_id', 2)

# ---- token map (verbatim logic from conversion/deepseek.py _v41_build_compressed_token_map) ----
from transformers import AutoTokenizer
from tokenizers import Regex, normalizers
tok = AutoTokenizer.from_pretrained(src_dir)
sentinel = ""
norm = normalizers.Sequence([normalizers.NFKC(), normalizers.NFD(), normalizers.StripAccents(), normalizers.Lowercase(),
    normalizers.Replace(Regex(r"[ \t\r\n]+"), " "), normalizers.Replace(Regex(r"^ $"), sentinel), normalizers.Strip(),
    normalizers.Replace(sentinel, " ")])
backend = tok.backend_tokenizer
key_to_new = {}; lookup = [0] * len(tok)
for tid in range(len(tok)):
    text = backend.decode([tid], skip_special_tokens=False)
    if "�" in text: key = backend.id_to_token(tid)
    else:
        n = norm.normalize_str(text); key = n if n else text
    nid = key_to_new.get(key)
    if nid is None: nid = len(key_to_new); key_to_new[key] = nid
    lookup[tid] = nid
token_map, cvs = lookup, len(key_to_new)
if cvs != expected_cvs:
    raise SystemExit(f"compressed vocab size {cvs} != config {expected_cvs}: tokenizer mismatch, refusing")
print("token map ok:", len(token_map), "tokens ->", cvs, "compressed")

# ---- multipliers (numpy, same RNG as the converter; torch only wrapped the result there) ----
max_long = np.iinfo(np.int64).max
bound = max(1, (max_long // cvs) // 2)
mult = np.stack([np.random.default_rng(10007 * l).integers(low=0, high=bound, size=(max_ngram,), dtype=np.int64) * 2 + 1 for l in layer_ids])

# ---- primes and offsets (verbatim loop) ----
def is_prime(n):
    if n < 2: return False
    for p in (2,3,5,7,11,13,17,19,23,29,31,37):
        if n % p == 0: return n == p
    f = 41
    while f * f <= n:
        if n % f == 0 or n % (f + 2) == 0: return False
        f += 6
    return True
def next_prime(start, seen):
    c = start + 1
    while not is_prime(c) or c in seen: c += 1
    return c
seen = set(); primes = []
for l in layer_ids:
    per = []
    for g in range(max_ngram - 1):
        cur = engram_vocab - 1; sizes = []
        for hd in range(n_heads):
            cur = next_prime(cur, seen); seen.add(cur); sizes.append(cur)
        per.append(sizes)
    primes.append(per)
primes = np.array(primes, dtype=np.uint64)
offsets = np.array([np.cumsum(np.concatenate(([0], lp.flatten()[:-1]))).reshape(lp.shape) for lp in primes], dtype=np.uint64)
pad_id = int(token_map[pad_raw])
print("multipliers", mult.shape, mult.tolist()); print("primes", primes.shape, "first", primes.flatten()[:3].tolist()); print("pad_id", pad_id)

# ---- copy shard 1 with the fixed metadata ----
reader = GGUFReader(in_path)
writer = GGUFWriter(out_path, arch)
rename = {f"deepseek4.engram.{k}": f"{arch}.engram.{k}" for k in ("layer_ids","head_count","key_length","max_ngram_size")}
for field in reader.fields.values():
    if field.name == gguf.Keys.General.ARCHITECTURE or field.name.startswith('GGUF.'): continue
    vt = field.types[0]; st = field.types[-1] if vt == GGUFValueType.ARRAY else None
    writer.add_key_value(rename.get(field.name, field.name), field.contents(), vt, sub_type=st)
def add_u64(key, arr): writer.add_key_value(key, [int(x) for x in np.asarray(arr).reshape(-1)], GGUFValueType.ARRAY, GGUFValueType.UINT64)
add_u64(f"{arch}.engram.multipliers", mult); add_u64(f"{arch}.engram.primes", primes); add_u64(f"{arch}.engram.offsets", offsets)
writer.add_key_value(f"{arch}.engram.token_map", [int(x) for x in token_map], GGUFValueType.ARRAY, GGUFValueType.INT32)
writer.add_uint32(f"{arch}.engram.pad_id", pad_id)
writer.add_key_value("general.engram_constants_injected_by", "claudeMB 2026-09-11 from config+tokenizer, runtime/deepseek41 f37da57 recipe", GGUFValueType.STRING)
total = 0
for t in reader.tensors:
    total += t.n_bytes; writer.add_tensor_info(t.name, t.data.shape, t.data.dtype, t.data.nbytes, t.tensor_type)
writer.write_header_to_file(); writer.write_kv_data_to_file(); writer.write_ti_data_to_file()
bar = tqdm(desc="Writing", total=total, unit="byte", unit_scale=True)
for t in reader.tensors:
    writer.write_tensor_data(t.data, tensor_endianess=reader.endianess); bar.update(t.n_bytes)
writer.close(); print("DONE", out_path)
