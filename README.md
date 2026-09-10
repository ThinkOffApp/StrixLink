# StrixLink

Direct Thunderbolt/USB4 compute link between a Mac (Apple Silicon) and an AMD
Strix Halo box, for local-LLM clustering. Built and measured on a MacBook Pro
(M5 Max, 128 GB) and a Bosgame M5 (Ryzen AI MAX+ 395 "Strix Halo", 128 GB,
Ubuntu 26.04) on 2026-08-20.

One cable gives you an IP link an order of magnitude faster than gigabit LAN,
and with llama.cpp's RPC backend the two machines' GPUs (Metal + Vulkan) can
serve one model together.

## Measured numbers

The transport ladder, all measured on this pair on 2026-08-20 — each layer
shows exactly what its overhead costs:

| Layer | Throughput | Notes |
|---|---|---|
| Raw link (iperf3, one-way, 5 s) | **17.3 Gbit/s** | zero retransmits |
| ssh-encrypted file copy | 12.6 Gbit/s | cipher-bound floor; 91 GB model in ~2 min |
| StrixLink verbs (TCP, write+read round-trip) | **10.7-10.8 Gbit/s**, flat across 1-64 MiB | after the 2026-08-21 optimization pass (PR #6: copy elimination, 4 MiB socket buffers, 16 MiB chunking): was 6.05 before, so ~1.7x on the real cable and ~62% of the raw link; loopback went 19.6 to 54-62 Gbit/s (2.7-3.1x). `examples/bench_transport.py` |
| llama.cpp RPC tensor upload (model load phase) | ~0.11 Gbit/s | per-tensor framing + syscalls eat 99% of the link — cold-starting a split model takes 10+ min |
| rxe soft-RoCE loopback (same box, stack overhead only) | 16.8 Gbit/s, 1.8 µs WRITE latency | `examples/rxe_loopback.py` |
| Link ping (both directions) | 0.2 - 0.8 ms | |
| llama.cpp RPC split inference (DeepSeek V4 Flash 284B MoE, 97 GB, same split) | gen 20.9 t/s, pp 12.1 t/s | MoE splits better than dense (smaller active set crosses the link): 20.9 vs the dense 27B's 16.6. Still capacity-framing: loses to the best single box (Mac 30.0), beats Strix alone (12.4). Cold start ~45 GB upload took ~90 min through RPC framing; warm restart with the server-side tensor cache (`rpc-server -c`) measured **84 s** end-to-end (~64x) at identical speed - always run the server with `-c` |
| llama.cpp RPC split inference (27B Q4 across Mac Metal + Strix Vulkan) | gen 16.6 t/s, pp 45.1 t/s | one model, two machines, one cable. Honest read: SLOWER than the best single box (Mac raw 25.3, MTP 25.0, MLX 32.3) because every token crosses the link - splitting a model that fits one machine costs speed. The split's value is CAPACITY: models neither box holds alone (150-250 GB class). Cold start: ~7 GB layer upload at ~0.11 Gbit/s (10+ min) |

The gap between rows 1 and 4 is the whole argument for the RDMA layers below:
the cable is fine, the copies are not. The 1.8 µs rxe latency (vs sub-ms TCP)
is what makes per-token KV streaming plausible.

LLM throughput context (same day, both machines at full power, llama-bench
pp512/tg128): dense 27B Q4 runs 748/25.3 t/s on the Mac and 376/12.4 t/s on
Strix Halo (25.0 t/s with MTP speculative decoding); a 284B MoE at 3-bit runs
556/30.0 vs 147/12.4. Raw generation is bandwidth-bound on both.

### 2026-09-10 rerun: the corrected picture

The August rows above were taken with the Strix at a 64 GB BIOS carve. On
2026-09-09 the carve went to 1 GB with 120 GB of GTT (the whole memory as one
GPU-addressable region), both boxes were put on the same llama.cpp commit
(434ddbb, Vulkan+RPC on the Strix, Metal+RPC on the Mac), and every row was
measured again, card protocol (pp512 / tg128, tokens/s, 3 runs for the 97 GiB
model, 5 for the rest). Raw log: [docs/measurements-2026-09-10-raw.md](docs/measurements-2026-09-10-raw.md).

| Model | Configuration | pp512 | tg128 | August | Notes |
|---|---|---|---|---|---|
| DeepSeek V4 Flash IQ3_XXS (97 GiB, 284B MoE) | Strix alone, Vulkan, direct-IO load | 140.3 ± 4.4 | **18.56 ± 0.01** | 147 / 12.4 | generation +50%: in August the model spilled past the carve. Needs `-lm dio` (`--load-mode dio` on llama-server): with mmap the page cache and the pinned GTT copy of the same file exceed the 122 GB of RAM and the load never finishes |
| DeepSeek V4 Flash IQ3_XXS | Mac alone, Metal | 584.5 ± 3.2 | **33.42 ± 0.00** | 556 / 30.0 | still the fastest single box |
| DeepSeek V4 Flash IQ3_XXS | split, Mac client + Strix RPC device | 235.0 ± 10.4 | 20.24 ± 0.04 | 12.1 / 20.9 | prompt side ~20x August (llama.cpp's own RPC path improved); generation unchanged; 18 tensors cached on the Strix (`rpc-server -c`) |
| DeepSeek V4 Flash IQ3_XXS | split, Strix client (direct-IO) + Mac RPC device | 234.3 ± 12.6 | 19.30 ± 0.08 | new | the Mac's `ggml-rpc-server` must be started with `-d MTL0`; its default device is the BLAS CPU path, which aborts mid-graph on this model |
| Qwen3.8-27B Q4_K_XL (16.3 GiB, dense) | Mac alone, Metal | 726.6 ± 2.6 | 25.45 ± 0.52 | 748 / 25.3 | unchanged |
| Qwen3.8-27B Q4_K_XL | Strix alone, Vulkan | 291.6 ± 28.6 | 12.15 ± 0.02 | 376 / 12.4 | generation unchanged by the carve: a model that fits is bandwidth-bound either way; prompt measured at the balanced profile (August: accelerator-performance) |
| Qwen3.8-27B Q4_K_XL | split, Mac client + Strix RPC device | 433.8 ± 4.9 | 15.25 ± 0.13 | 45.1 / 16.6 | splitting a model that fits one box still loses on generation (15 vs the Mac's 25) |
| Nex-N2.5-mini Q4_K_M (19.7 GiB, 35B-A3B MoE) | Mac alone / split Mac client + Strix | 3099 ± 11 / 1431.9 ± 1.9 | 117.1 ± 0.9 / 69.6 ± 2.8 | new | the small-model control: the split halves a model that fits |
| DeepSeek V4 Flash IQ3_XXS | Mac alone, live llama-server, speculative decoding with the DSpark drafter (`examples/spec_bench.py`, 5 prompts, 256 tokens, temp 0) | gen 32.23 ± 0.47 baseline vs **30.76 ± 3.40** drafted, acceptance 57% | | new | net loss on the Mac: the 10.9 GB drafter (mxfp4 experts, not requantizable) does not fit beside the 97 GiB model in the 110 GB Metal budget, so it ran on the CPU (`-ngld 0`) and the drafting cost exceeded the gain; only the reasoning prompt gained (37.0 at 75% acceptance), the others lost |

Coherence was checked on every DeepSeek row with the same prompt at
temperature 0 (`llama-completion -st -c 4096`): all four configurations produced
the identical correct answer. The August "garbage output" was the carve spill,
not the RPC code. Practical rules from the rerun: load big models on the Strix
with direct IO at the minimum carve; pin the Mac RPC server to `MTL0`; keep a
small context on sample runs (the default is the model's full context, whose
KV cache alone can exhaust memory); the link itself re-measured at 16.5 Gbit/s.

## Layer 1: the IP link

Thunderbolt/USB4 between the two machines, IP on top. No switch, no LAN.

- **Strix/Linux side**: `thunderbolt-net` kernel module + a netplan address on
  the `thunderbolt0` interface — see [scripts/strix-setup.sh](scripts/strix-setup.sh).
- **Mac side**: macOS creates the "Thunderbolt Bridge" service automatically;
  give it a static address — see [scripts/mac-setup.sh](scripts/mac-setup.sh).

This repo uses `10.55.0.1/24` (Mac) and `10.55.0.2/24` (Strix). The link is
point-to-point: nothing else can see these addresses.

A bare machine with no OS does **not** enumerate on the Mac's Thunderbolt bus
at all — both ends need a running OS before the cable does anything.

## Layer 2: shared inference (llama.cpp RPC)

llama.cpp's RPC backend exposes one machine's GPU memory to the other's
inference process, so a single model splits across both machines.

- Strix side runs `ggml-rpc-server` **bound to the TB address only** — the RPC
  protocol has **no authentication**, so it must never listen on a LAN or
  public interface. See [scripts/strix-rpc-server.sh](scripts/strix-rpc-server.sh).
- Mac side builds llama.cpp with `-DGGML_RPC=ON` and points at it:
  see [scripts/mac-rpc-split-run.sh](scripts/mac-rpc-split-run.sh).

Character of this mode: layer-granular TCP copies, both CPUs touch every
transfer. It is a **capacity** tool (run a model neither machine fits alone),
not a latency tool — every generated token crosses the link.

## Layer 3 (planned): KV-cache handoff

The two machines have complementary strengths: the Mac reads long prompts
several times faster, the Strix box generates cheaply and always-on. The next
layer prefills a large context on the Mac, ships the KV state over the link
(seconds at this bandwidth), and lets the Strix side generate. Good for
agent/batch workloads; not interactive-chat-shaped yet.

## Layer 4 (waiting): MCDMA

[Ash Hart's MCDMA](https://x.com/ashxhart) (now in collaboration with
[EXO Labs](https://github.com/exo-explore)) reverse-engineers Apple's
Thunderbolt XDomain RDMA protocol: registered memory, rkeys, one-sided
READ/WRITE with no CPU in the data path — the proper version of what layers
1-2 approximate with TCP. No code is published yet. When it ships, this link
and both endpoints are ready to become an integration target: same cable,
same addresses, drop-in replacement for the transport underneath the RPC and
KV layers.

## Security notes

- The RPC server binds only to the point-to-point TB address. Keep it that way.
- Model-serving endpoints on the boxes should carry API keys even on a home
  LAN; only the TB link itself is unauthenticated by protocol, which is why it
  never leaves the cable.
