"""Transport layer for strixlink.

The public API (register / read / write / send / recv) is modeled on RDMA
verbs so that a real one-sided RDMA transport can be dropped in later without
touching callers. Today the only transport is TCP over a point-to-point
Thunderbolt link (thunderbolt-net), which is two-sided and copies through the
kernel. When a microsecond-latency RDMA transport (e.g. MCDMA) becomes
available, implement the same Transport interface and callers keep working.
"""

from __future__ import annotations

import socket
import struct
import threading

# Wire framing: 4-byte magic, 1-byte op, 8-byte region id, 8-byte offset,
# 8-byte length, then payload. Fixed header keeps the parser trivial.
_MAGIC = b"SXL1"
_HDR = struct.Struct("!4sBQQQ")

OP_WRITE = 1   # requester pushes bytes into a remote region (one-sided-like)
OP_READ = 2    # requester pulls bytes from a remote region
OP_SEND = 3    # two-sided message onto the peer's recv queue
OP_READ_REPLY = 4


class Transport:
    """Interface every transport implements. Swap TCP for RDMA here."""

    def connect(self) -> None: ...
    def serve(self) -> None: ...
    def close(self) -> None: ...


def _recvall(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("peer closed mid-frame")
        buf += chunk
    return bytes(buf)


def read_frame(sock: socket.socket):
    magic, op, rid, off, length = _HDR.unpack(_recvall(sock, _HDR.size))
    if magic != _MAGIC:
        raise ValueError(f"bad magic {magic!r}")
    payload = _recvall(sock, length) if length and op in (OP_WRITE, OP_SEND, OP_READ_REPLY) else b""
    return op, rid, off, length, payload


def write_frame(sock: socket.socket, op: int, rid: int, off: int, length: int, payload: bytes = b"") -> None:
    sock.sendall(_HDR.pack(_MAGIC, op, rid, off, length) + payload)
