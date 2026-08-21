"""Hardening tests (per code review): prove the transport rejects malformed
input instead of allocating unboundedly or corrupting a region, and that
concurrent reads are correlated correctly.
"""
import threading
import time

from strixlink import Endpoint
from strixlink import transport as T


def test_frame_length_capped():
    import io
    # a header claiming a huge length must be rejected before any big alloc
    class FakeSock:
        def __init__(self, data): self.buf = data
        def recv(self, n):
            chunk = self.buf[:n]; self.buf = self.buf[n:]; return chunk
        def recv_into(self, view, n):
            chunk = self.buf[:n]; self.buf = self.buf[n:]
            view[:len(chunk)] = chunk; return len(chunk)
    hdr = T._HDR.pack(T._MAGIC, T.OP_WRITE, 0, 1, 0, T.MAX_FRAME_BYTES + 1)
    try:
        T.read_frame(FakeSock(hdr))
        assert False, "should have rejected oversized frame"
    except ValueError as e:
        assert "exceeds cap" in str(e)


def test_out_of_bounds_write_rejected():
    b = Endpoint(local="127.0.0.1", peer="127.0.0.1", port=50610)
    a = Endpoint(local="127.0.0.1", peer="127.0.0.1", port=50610)
    region = bytearray(16)
    b.start(); rid = b.register(region); time.sleep(0.1); a.connect()
    # write past the end of the 16-byte region: must be ignored, region intact
    a.write(rid, 10, b"OVERFLOWING")  # 10+11 > 16
    time.sleep(0.2)
    assert len(region) == 16, "region was resized by an out-of-bounds write"
    assert bytes(region) == bytes(16), "region was corrupted"
    # a valid write still works
    a.write(rid, 0, b"OK")
    time.sleep(0.2)
    assert bytes(region[:2]) == b"OK"
    a.close(); b.close()


def test_concurrent_reads_correlated():
    b = Endpoint(local="127.0.0.1", peer="127.0.0.1", port=50611)
    a = Endpoint(local="127.0.0.1", peer="127.0.0.1", port=50611)
    region = bytearray(b"0123456789ABCDEF")
    b.start(); rid = b.register(region); time.sleep(0.1); a.connect()
    results = {}
    def do_read(off, n, key):
        results[key] = a.read(rid, off, n)
    threads = [threading.Thread(target=do_read, args=(i * 4, 4, i)) for i in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert results[0] == b"0123" and results[1] == b"4567"
    assert results[2] == b"89AB" and results[3] == b"CDEF"
    a.close(); b.close()


if __name__ == "__main__":
    test_frame_length_capped()
    test_out_of_bounds_write_rejected()
    test_concurrent_reads_correlated()
    print("hardening OK: frame cap enforced, out-of-bounds write rejected, concurrent reads correlated")
