#!/usr/bin/env python3
"""Fixed-prompt generation benchmark against a live llama-server (/completion).
Usage: spec_bench.py URL LABEL [n_predict]  -> prints one table row + per-prompt lines; reads prompts.json next to it.
Reports tokens/s from the server's own timings and the draft acceptance rate when speculative decoding is on."""
import json, sys, time, urllib.request, os, statistics
url, label = sys.argv[1], sys.argv[2]; n = int(sys.argv[3]) if len(sys.argv) > 3 else 256
prompts = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "spec_prompts.json")))
# untimed warm-up (shader compile, pages coming in) so the first timed prompt is not the slow one (claudeMB review P2)
warm = {"prompt": "Warm-up: count from one to twenty.", "n_predict": 64, "temperature": 0, "cache_prompt": False}
urllib.request.urlopen(urllib.request.Request(url.rstrip("/") + "/completion", data=json.dumps(warm).encode(), headers={"Content-Type": "application/json"}), timeout=1800).read()
rows = []
for p in prompts:
    body = {"prompt": p["prompt"], "n_predict": n, "temperature": 0, "cache_prompt": False}
    t0 = time.time()
    r = json.load(urllib.request.urlopen(urllib.request.Request(url.rstrip("/") + "/completion", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}), timeout=1800))
    t = r.get("timings", {}); wall = time.time() - t0
    gen = t.get("predicted_per_second"); pp = t.get("prompt_per_second")
    dn, da = t.get("draft_n"), t.get("draft_n_accepted")
    acc = (da / dn) if dn else None
    rows.append((p["id"], pp, gen, t.get("predicted_n"), acc, wall))
    print(f"  {p['id']:9s} pp {pp:7.1f} t/s  gen {gen:6.2f} t/s  n={t.get('predicted_n')}  acc={'%.0f%%' % (acc*100) if acc is not None else '-'}  wall {wall:5.1f}s", flush=True)
gens = [r[2] for r in rows if r[2]]; pps = [r[1] for r in rows if r[1]]
accs = [r[4] for r in rows if r[4] is not None]
print(f"| {label} | pp {statistics.mean(pps):.1f} ± {statistics.pstdev(pps):.1f} | gen {statistics.mean(gens):.2f} ± {statistics.pstdev(gens):.2f} | acceptance {('%.0f%%' % (statistics.mean(accs)*100)) if accs else 'n/a'} | {len(rows)} prompts x {n} tokens, temp 0 |")
