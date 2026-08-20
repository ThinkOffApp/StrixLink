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
        self._recv_q: "queue.Queue[bytes]" = queue.Queue()
        self._peer_sock: socket.socket | None = None
        self._srv: socket.socket | None = None
        self._read_replies: "queue.Queue[bytes]" = queue.Queue()

    # ---- region management (verbs: reg_mr) ----
    def register(self, buf: bytearray) -> int:
        """Expose a buffer to the peer; returns an rkey (region id)."""
        with self._lock:
            rid = self._next_rid
            self._next_rid += 1
            self._regions[rid] = buf
            return rid

    # ---- lifecycle ----
    def start(self) -> None:
        self._srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srv.bind((self.local, self.port))
        self._srv.listen(4)
        threading.Thread(target=self._serve_loop, daemon=True).start()

    def connect(self) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s.connect((self.peer, self.port))
        self._peer_sock = s
        threading.Thread(target=self._client_reader, daemon=True).start()

    # ---- one-sided-style verbs ----
    def write(self, peer_rid: int, offset: int, data: bytes) -> None:
        T.write_frame(self._peer_sock, T.OP_WRITE, peer_rid, offset, len(data), data)

    def read(self, peer_rid: int, offset: int, length: int) -> bytes:
        T.write_frame(self._peer_sock, T.OP_READ, peer_rid, offset, length)
        return self._read_replies.get(timeout=30)

    # ---- two-sided verbs ----
    def send(self, msg: bytes) -> None:
        T.write_frame(self._peer_sock, T.OP_SEND, 0, 0, len(msg), msg)

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
    def _serve_loop(self) -> None:
        while True:
            try:
                conn, _ = self._srv.accept()
            except OSError:
                return
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn: socket.socket) -> None:
        while True:
            try:
                op, rid, off, length, payload = T.read_frame(conn)
            except (ConnectionError, ValueError, OSError):
                return
            if op == T.OP_WRITE:
                buf = self._regions.get(rid)
                if buf is not None:
                    buf[off:off + length] = payload
            elif op == T.OP_READ:
                buf = self._regions.get(rid)
                chunk = bytes(buf[off:off + length]) if buf is not None else b""
                T.write_frame(conn, T.OP_READ_REPLY, rid, off, len(chunk), chunk)
            elif op == T.OP_SEND:
                self._recv_q.put(payload)

    def _client_reader(self) -> None:
        while True:
            try:
                op, rid, off, length, payload = T.read_frame(self._peer_sock)
            except (ConnectionError, ValueError, OSError):
                return
            if op == T.OP_READ_REPLY:
                self._read_replies.put(payload)
            elif op == T.OP_SEND:
                self._recv_q.put(payload)
