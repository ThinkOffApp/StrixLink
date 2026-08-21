"""Transport layer for strixlink.

The public API (register / read / write / send / recv) is modeled on RDMA
verbs so that a real one-sided RDMA transport can be dropped in later without
touching callers. Today the only transport is TCP over a point-to-point
Thunderbolt link (thunderbolt-net), which is two-sided and copies through the
kernel. When a microsecond-latency RDMA transport (e.g. MCDMA) becomes
available, implement the same Transport interface and callers keep working.

Security note: the TCP transport has NO authentication and MUST only be bound
to a point-to-point Thunderbolt address. TB-only binding is a deployment
constraint, not authorization. Frame length is bounded and region offsets are
validated (see endpoint.py) so a malformed peer cannot force an unbounded
allocation or corrupt a registered region.
"""

from __future__ import annotations

import socket
import struct

# Wire framing: magic, op, req_id, region id, offset, length, then payload.
# req_id correlates READ replies with their requests so concurrent reads on one
# connection cannot be mismatched.
_MAGIC = b"SXL2"
_HDR = struct.Struct("!4sBQQQQ")

# Hard cap on any single frame's payload. A peer cannot request an allocation
# or read larger than this. 256 MiB covers a large tensor shard; raise
# deliberately if a use case needs more.
MAX_FRAME_BYTES = 256 * 1024 * 1024

OP_WRITE = 1        # requester pushes bytes into a remote region
OP_READ = 2         # requester pulls bytes from a remote region
OP_SEND = 3         # two-sided message onto the peer's recv queue
OP_READ_REPLY = 4

_PAYLOAD_OPS = (OP_WRITE, OP_SEND, OP_READ_REPLY)
_VALID_OPS = (OP_WRITE, OP_READ, OP_SEND, OP_READ_REPLY)


class Transport:
    """Interface every transport implements. Swap TCP for RDMA here."""

    def connect(self) -> None: ...
    def serve(self) -> None: ...
    def close(self) -> None: ...


def _recvall(sock: socket.socket, n: int) -> bytearray:
    # Preallocate once and recv_into it. The old `buf += chunk` reallocated and
    # copied the whole accumulator each chunk — O(n^2) bytes moved for a large
    # frame. recv_into a fixed buffer is O(n) and does zero intermediate copies.
    buf = bytearray(n)
    view = memoryview(buf)
    got = 0
    while got < n:
        r = sock.recv_into(view[got:], n - got)
        if r == 0:
            raise ConnectionError("peer closed mid-frame")
        got += r
    return buf


def read_frame(sock: socket.socket):
    magic, op, req_id, rid, off, length = _HDR.unpack(_recvall(sock, _HDR.size))
    if magic != _MAGIC:
        raise ValueError(f"bad magic {magic!r}")
    if op not in _VALID_OPS:
        raise ValueError(f"bad op {op}")
    if length > MAX_FRAME_BYTES:
        raise ValueError(f"frame length {length} exceeds cap {MAX_FRAME_BYTES}")
    payload = _recvall(sock, length) if length and op in _PAYLOAD_OPS else b""
    return op, req_id, rid, off, length, payload


def write_frame(sock: socket.socket, op: int, req_id: int, rid: int, off: int,
                length: int, payload: bytes = b"") -> None:
    if length > MAX_FRAME_BYTES:
        raise ValueError(f"frame length {length} exceeds cap {MAX_FRAME_BYTES}")
    header = _HDR.pack(_MAGIC, op, req_id, rid, off, length)
    # Send header then payload separately. The old `header + payload` allocated
    # and copied a fresh buffer the size of the whole frame (a 256 MiB payload
    # meant a 256 MiB temporary); two sendall calls send the existing payload
    # bytes with no extra copy. The caller holds the per-connection send lock,
    # so the two calls stay atomic relative to other frames.
    if payload:
        sock.sendall(header)
        sock.sendall(payload)
    else:
        sock.sendall(header)
