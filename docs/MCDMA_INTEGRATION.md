# MCDMA readiness: the Mac-side interface

strixlink's Strix / Linux end already does real one-sided RDMA over Thunderbolt
via in-kernel soft-RoCE (`rdma_rxe`) — see [`strixlink/rxe_transport.py`](../strixlink/rxe_transport.py)
and [`examples/rxe_loopback.py`](../examples/rxe_loopback.py), which posts an
RDMA WRITE straight into a peer's registered memory and verifies it.

The open piece is the **macOS end**: macOS has no soft-RoCE, so a Mac cannot yet
answer RDMA to the Strix `rxe` endpoint. Apple's Thunderbolt supports an
RDMA-style protocol, and [MCDMA](https://x.com/ashxhart) (Metal ⇄ CUDA DMA, by
Ash Hart) reverse-engineers exactly that path for CUDA ⇄ Metal. This document
defines the small, explicit contract a Mac-side transport must satisfy to
complete the **Mac ⇄ Strix** chain, so an MCDMA-style implementation has one
precise place to plug in.

## What the Strix end already provides

Per connection, the `rxe` endpoint exposes an RC (reliable-connected) queue pair
and a registered memory region. It offers, and expects the peer to offer:

| capability | Strix side (working) | what the Mac side must provide |
|---|---|---|
| memory registration | `reg_mr` → `(addr, rkey)` with local-write + remote-read + remote-write | register a Metal/unified-memory buffer, yield `(addr, rkey)` |
| one-sided WRITE | posts `IBV_WR_RDMA_WRITE` into peer `(addr, rkey)` | accept remote WRITE into a registered region without host-CPU involvement per op |
| one-sided READ | (symmetric) | serve remote READ from a registered region |
| connection bootstrap | exchanges the params below, drives QP `INIT→RTR→RTS` | produce the same params, reach a ready-to-send state |

MCDMA's announced primitives — *registered memory, rkeys, one-sided READ/WRITE,
two-sided SEND/RECV with credit flow* — are a 1:1 match for this table. That is
why the two ends are complementary rather than overlapping.

## Connection bootstrap contract

Both ends exchange one small JSON object over a plain TCP side-channel (the
Thunderbolt IP link is fine) *before* any RDMA traffic. This is exactly what
`RxeEndpoint.local_conn()` emits and `connect()` consumes:

```json
{
  "qpn":  "<uint32 queue-pair number>",
  "psn":  "<uint32 starting packet sequence number>",
  "gid":  "<peer GID, string form>",
  "addr": "<uint64 base address of the registered region>",
  "rkey": "<uint32 remote key for that region>"
}
```

A RoCE v2 peer also needs the GID (and, on an IB fabric, the LID); an
MCDMA/Apple-TB transport substitutes whatever addressing its fabric uses, but
the *shape* — identify the queue pair, identify the region — is the same. After
the swap, each side transitions its queue pair to ready-to-send. The Strix side
uses the standard `INIT → RTR → RTS` sequence with `IBV_MTU_1024`; a Mac
transport picks the equivalent for its stack.

## The transport interface to implement

strixlink keeps transports behind one interface so the wire can change without
touching callers (see [`strixlink/transport.py`](../strixlink/transport.py)).
A Mac transport implements the shape in
[`strixlink/mac_transport.py`](../strixlink/mac_transport.py):

- `register(buf) -> region` — pin a buffer, return an object exposing `addr` and `rkey`.
- `local_conn() -> dict` — the bootstrap object above.
- `connect(remote: dict)` — consume the peer's bootstrap object, reach ready.
- `write(data, remote_offset=0)` — one-sided RDMA WRITE into the peer region.
- `read(length, offset=0) -> bytes` — read back the local region (post-WRITE), or a one-sided remote READ.

Match these and `Endpoint`'s verbs (`register` / `read` / `write` / `send` /
`recv`) work over the Mac ⇄ Strix link with no caller changes.

## Verifying the full chain

Once a Mac transport exists, the cross-machine test mirrors
`examples/rxe_loopback.py` but with the two endpoints on different machines:

1. Strix runs `RxeEndpoint`, registers a region, prints `local_conn()`.
2. Mac runs the MCDMA transport, registers a region, prints its `local_conn()`.
3. Exchange the two objects over the TB IP link (`examples/` has the helper).
4. Mac issues an RDMA WRITE into the Strix region; Strix reads it back and
   compares — the same `A wrote N bytes straight into B's memory` proof, but
   now Mac→Strix over the cable.

Measured latency/throughput then replaces the honest placeholder in the README's
**Measured** section (today it carries Strix-side loopback numbers only).

## Status

- Strix / Linux end: **done**, real RDMA, verified.
- Bootstrap + memory model: **defined here**, matches the working `rxe` code.
- Mac end: **open** — this is the MCDMA-shaped slot. `strixlink/mac_transport.py`
  is the stub to fill in.
