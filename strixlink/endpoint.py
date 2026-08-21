"""strixlink endpoint: an RDMA-verbs-shaped memory link between a Mac
(Metal / MLX unified memory) and an AMD Strix Halo box (Vulkan / ROCm), over a
Thunderbolt cable.

Verbs today, over TCP:
    ep = Endpoint(local="10.55.0.2", peer="10.55.0.1")
    ep.start()                         # serve local regions + connect to peer
    rid = ep.register(buffer)          # expose a bytearray/memoryview, get an rkey
    ep.write(peer_rid, offset, data)   # push bytes into the peer's region
    data = ep.read(peer_rid, offset, n)# pull bytes from the peer's region
    ep.send(msg); ep.recv()            # two-sided message queue

The verbs are transport-agnostic. `transport.py` carries them over TCP now;
a future RDMA transport (see ROADMAP) implements the same frames one-sided.

Hardening (per review): frame length is capped in transport.read_frame, region
offsets/lengths are validated before any slice write, writes to the shared peer
socket are serialized with a lock so concurrent callers cannot interleave a
header and payload, and READ replies are correlated by request id so concurrent
reads cannot be mismatched. There is still NO peer authentication — bind only to
a point-to-point Thunderbolt address.
"""

from __future__ import annotations

import queue
import socket
import threading

from . import transport as T

_PORT = 50555


class Endpoint:
    def __init__(self, local: str, peer: str, port: int = _PORT):
        self.local = local
        self.peer = peer
        self.port = port
        self._regions: dict[int, bytearray] = {}
        self._next_rid = 1
        self._lock = threading.Lock()
        self._send_lock = threading.Lock()
        self._recv_q: "queue.Queue[bytes]" = queue.Queue()
        self._peer_sock: socket.socket | None = None
        self._srv: socket.socket | None = None
        # req_id -> Queue for that read's reply; correlates concurrent reads.
        self._pending: dict[int, "queue.Queue[bytes]"] = {}
        self._pending_lock = threading.Lock()
        self._next_req = 1

    # ---- region management (verbs: reg_mr) ----
    def register(self, buf: bytearray) -> int:
        """Expose a buffer to the peer; returns an rkey (region id)."""
        with self._lock:
            rid = self._next_rid
            self._next_rid += 1
            self._regions[rid] = buf
            return rid

    # Larger socket buffers keep a high-bandwidth link (multi-Gbit Thunderbolt)
    # full despite the round-trip; the ~200 KB default throttles big transfers.
    _SOCK_BUF = 4 * 1024 * 1024

    @classmethod
    def _tune(cls, s: socket.socket) -> None:
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        for opt in (socket.SO_SNDBUF, socket.SO_RCVBUF):
            try:
                s.setsockopt(socket.SOL_SOCKET, opt, cls._SOCK_BUF)
            except OSError:
                pass

    # ---- lifecycle ----
    def start(self) -> None:
        self._srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Set SO_RCVBUF on the listener BEFORE listen() so accepted sockets
        # inherit the large buffer and TCP window scaling is negotiated in the
        # SYN (per claudeMB review — setting it only post-accept can be too late).
        try:
            self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self._SOCK_BUF)
        except OSError:
            pass
        self._srv.bind((self.local, self.port))
        self._srv.listen(4)
        threading.Thread(target=self._serve_loop, daemon=True).start()

    def connect(self) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tune(s)
        s.connect((self.peer, self.port))
        self._peer_sock = s
        threading.Thread(target=self._client_reader, daemon=True).start()

    def _send(self, op, req_id, rid, off, length, payload=b""):
        # Serialize writes so a header and its payload are never interleaved
        # with another caller's frame on the shared socket.
        with self._send_lock:
            T.write_frame(self._peer_sock, op, req_id, rid, off, length, payload)

    # Split large transfers into CHUNK-sized frames. A single huge frame stalls
    # once it outgrows the socket buffer (measured: 64 MiB fell from 10.7 to 8.2
    # Gbit/s over the cable, p99 jumped); chunks stay in the pipelined sweet spot
    # regardless of the OS socket-buffer cap. Passing a memoryview slice to the
    # transport avoids copying each chunk out of the caller's buffer.
    _CHUNK = 16 * 1024 * 1024

    # ---- one-sided-style verbs ----
    def write(self, peer_rid: int, offset: int, data: bytes) -> None:
        n = len(data)
        if n <= self._CHUNK:
            self._send(T.OP_WRITE, 0, peer_rid, offset, n, data)
            return
        mv = memoryview(data)
        for o in range(0, n, self._CHUNK):
            piece = mv[o:o + self._CHUNK]
            self._send(T.OP_WRITE, 0, peer_rid, offset + o, len(piece), piece)

    def _read_one(self, peer_rid: int, offset: int, length: int) -> bytes:
        with self._pending_lock:
            req_id = self._next_req
            self._next_req += 1
            reply_q: "queue.Queue[bytes]" = queue.Queue()
            self._pending[req_id] = reply_q
        self._send(T.OP_READ, req_id, peer_rid, offset, length)
        try:
            return reply_q.get(timeout=30)
        finally:
            with self._pending_lock:
                self._pending.pop(req_id, None)

    def read(self, peer_rid: int, offset: int, length: int) -> bytes:
        if length <= self._CHUNK:
            return bytes(self._read_one(peer_rid, offset, length))
        out = bytearray(length)
        for o in range(0, length, self._CHUNK):
            piece = self._read_one(peer_rid, offset + o, min(self._CHUNK, length - o))
            out[o:o + len(piece)] = piece
        return bytes(out)

    # ---- two-sided verbs ----
    def send(self, msg: bytes) -> None:
        self._send(T.OP_SEND, 0, 0, 0, len(msg), msg)

    def recv(self, timeout: float | None = None) -> bytes:
        return self._recv_q.get(timeout=timeout)

    def close(self) -> None:
        for s in (self._peer_sock, self._srv):
            try:
                if s:
                    s.close()
            except OSError:
                pass

    # ---- internals ----
    @staticmethod
    def _valid_range(buf: bytearray, off: int, length: int) -> bool:
        return isinstance(off, int) and isinstance(length, int) and 0 <= off <= off + length <= len(buf)

    def _serve_loop(self) -> None:
        while True:
            try:
                conn, _ = self._srv.accept()
            except OSError:
                return
            self._tune(conn)
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn: socket.socket) -> None:
        conn_lock = threading.Lock()
        while True:
            try:
                op, req_id, rid, off, length, payload = T.read_frame(conn)
            except (ConnectionError, ValueError, OSError):
                return
            if op == T.OP_WRITE:
                buf = self._regions.get(rid)
                # Validate bounds AND exact payload length: bytearray slice
                # assignment can resize the region, so a mismatched length or
                # out-of-range offset must be rejected, not applied.
                if buf is not None and len(payload) == length and self._valid_range(buf, off, length):
                    buf[off:off + length] = payload
            elif op == T.OP_READ:
                buf = self._regions.get(rid)
                if buf is not None and self._valid_range(buf, off, length):
                    chunk = bytes(buf[off:off + length])
                else:
                    chunk = b""
                with conn_lock:
                    T.write_frame(conn, T.OP_READ_REPLY, req_id, rid, off, len(chunk), chunk)
            elif op == T.OP_SEND:
                self._recv_q.put(payload)

    def _client_reader(self) -> None:
        while True:
            try:
                op, req_id, rid, off, length, payload = T.read_frame(self._peer_sock)
            except (ConnectionError, ValueError, OSError):
                return
            if op == T.OP_READ_REPLY:
                with self._pending_lock:
                    q = self._pending.get(req_id)
                if q is not None:
                    q.put(payload)
            elif op == T.OP_SEND:
                self._recv_q.put(payload)
