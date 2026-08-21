"""Mac-side RDMA transport stub — the MCDMA-shaped slot.

The Strix/Linux end of strixlink already does real one-sided RDMA over
Thunderbolt via soft-RoCE (see rxe_transport.py). macOS has no soft-RoCE, so the
Mac end needs a transport built on an Apple-Thunderbolt-RDMA path — for example
MCDMA (Metal/CUDA DMA over USB4/Thunderbolt, by Ash Hart), which exposes exactly
the primitives this interface needs: registered memory, rkeys, one-sided
READ/WRITE.

This file is intentionally a stub: it fixes the interface so an implementation
has one precise place to land, and so the rest of strixlink (Endpoint verbs)
works over Mac<->Strix without caller changes once it is filled in. See
docs/MCDMA_INTEGRATION.md for the bootstrap contract and the mapping to MCDMA's
primitives.

Nothing here imports a Mac-only dependency, so the module loads everywhere; the
methods raise NotImplementedError until a real backend is wired in.
"""

from __future__ import annotations


class MacRegion:
    """A registered Mac-side memory region: a pinned buffer the peer can
    one-sidedly READ/WRITE, identified to the peer by (addr, rkey)."""

    def __init__(self, addr: int, rkey: int, size: int):
        self.addr = addr
        self.rkey = rkey
        self.size = size


class MacRdmaTransport:
    """One RDMA connection from a Mac to a Strix `rxe` endpoint.

    Implement these five methods on top of an Apple-TB-RDMA / MCDMA backend and
    strixlink's Endpoint verbs work unchanged over the cable. The method shapes
    mirror RxeEndpoint so the two ends bootstrap against each other directly.
    """

    def __init__(self, region_size: int = 1 << 20):
        self.region_size = region_size

    def register(self, buf) -> MacRegion:
        """Pin `buf` (e.g. a Metal / unified-memory buffer) for remote access
        and return a MacRegion carrying its (addr, rkey)."""
        raise NotImplementedError("wire an Apple-TB-RDMA / MCDMA memory registration here")

    def local_conn(self) -> dict:
        """Return the bootstrap object exchanged with the peer before RDMA
        traffic: {qpn, psn, gid, addr, rkey}. Must match the shape
        RxeEndpoint.local_conn() emits (see docs/MCDMA_INTEGRATION.md)."""
        raise NotImplementedError("return the QP/region bootstrap params")

    def connect(self, remote: dict) -> None:
        """Consume the peer's bootstrap object and drive the local queue pair to
        a ready-to-send state (the Mac-stack equivalent of INIT->RTR->RTS)."""
        raise NotImplementedError("bring the connection to ready-to-send")

    def write(self, data: bytes, remote_offset: int = 0) -> None:
        """One-sided RDMA WRITE of `data` into the peer's registered region at
        `remote_offset` — no peer host-CPU involvement per op."""
        raise NotImplementedError("post a one-sided RDMA WRITE")

    def read(self, length: int, offset: int = 0) -> bytes:
        """Read `length` bytes at `offset` — either from the local region after
        a completed WRITE, or via a one-sided remote READ."""
        raise NotImplementedError("read back the region / post a one-sided RDMA READ")
