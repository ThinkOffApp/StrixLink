# StrixLink

Direct Thunderbolt/USB4 compute link between a Mac (Apple Silicon) and an AMD
Strix Halo box, for local-LLM clustering. Built and measured on a MacBook Pro
(M5 Max, 128 GB) and a Bosgame M5 (Ryzen AI MAX+ 395 "Strix Halo", 128 GB,
Ubuntu 26.04) on 2026-08-20.

One cable gives you an IP link an order of magnitude faster than gigabit LAN,
and with llama.cpp's RPC backend the two machines' GPUs (Metal + Vulkan) can
serve one model together.

## Measured numbers

| What | Value |
|---|---|
| Link ping (both directions) | 0.2 - 0.8 ms |
| Throughput (through ssh encryption - a floor, not the ceiling) | 1 582 MB/s (~12.6 Gbit/s) |
| 91 GB model file transfer | ~2 minutes |

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
