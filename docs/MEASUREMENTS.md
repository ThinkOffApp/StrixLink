# Measurements

Hardware: **Bosgame M5** (AMD Strix Halo, 128 GB, Vulkan/soft-RoCE, Linux) and a
**MacBook M5 Max** (128 GB unified, Metal), joined by a Thunderbolt cable. All
numbers at full power. Inference via llama.cpp; split inference via its RPC
backend (one model sharded across both GPUs).

## Inference throughput (tokens/sec)

### Qwen 3.8 27B Q4 (dense, fits one machine)

| | prompt (pp) | generation | generation + accel |
|---|---:|---:|---:|
| Strix M5 (Vulkan) | 376 | 12.4 | 25.0 (MTP) |
| MacBook M5 Max (Metal) | 748 | 25.3 | 32.3 (MLX) |
| Split, MB + M5 | 45.1 | 16.6 | — |

### DeepSeek V4 Flash (284B MoE, 97 GB, 3-bit)

| | prompt (pp) | generation |
|---|---:|---:|
| Strix M5 | 147 | 12.4 |
| MacBook M5 Max | 556 | 30.0 |
| Split, MB + M5 | 12.1 | 20.9 |

**What the split is for.** For a model that fits one machine, splitting is
*slower* — every token crosses the link, so single-box (especially with MTP/MLX)
wins. The split's value is **capacity**: running a model neither box holds alone.
Cold start pays a large one-time RPC layer upload (~90 min for a ~97 GB model);
a **warm restart against the cached server is ~84 s (~64x faster)**, so the pain
is amortized.

## Transport (StrixLink verbs, not inference)

Write+read round-trip over the Thunderbolt cable (MB → M5), TCP transport:

| chunk | before | optimized |
|---|---:|---:|
| 4 MiB | ~6.1 | 10.16 Gbit/s |
| 16 MiB | ~6.1 | 10.72 Gbit/s |
| 64 MiB | ~6.1 | 10.79 Gbit/s |

The optimization (preallocated `recv_into`, no full-frame send copy, larger
socket buffers, 16 MiB chunking) lifts the whole curve to ~10.7 Gbit/s — about
62% of the raw link (iperf3 17.3 Gbit/s, 0 retransmits). rxe/soft-RoCE loopback
on the Strix side measures ~1.8 µs write latency and ~16.8 Gbit/s at 64 KB;
the one-sided RDMA data path is proven there (see the main README).

Reproduce with `examples/bench_transport.py`.
