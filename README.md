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
| StrixLink verbs (TCP, 256 MiB write+read round-trip) | 6.05 Gbit/s | `examples/tb_transfer.py` |
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
