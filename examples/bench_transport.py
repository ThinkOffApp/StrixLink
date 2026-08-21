"""Transport micro-benchmark: write+read round-trips over the TCP transport at
several chunk sizes, reporting throughput and p50/p99 latency.

Loopback by default (no hardware) to compare code changes; point --peer/--local
at the two Thunderbolt IPs for the real cross-machine number.

    python3 examples/bench_transport.py                 # loopback
    python3 examples/bench_transport.py --local 10.55.0.2 --peer 10.55.0.1 --server
"""
import argparse
import os
import statistics
import time

from strixlink import Endpoint


def run_client(local, peer, port, sizes_mib, iters):
    ep = Endpoint(local=local, peer=peer, port=port)
    ep.connect()
    print(f"{'chunk':>8} {'iters':>6} {'GB/s':>7} {'Gbit/s':>8} {'p50 ms':>8} {'p99 ms':>8}")
    for mib in sizes_mib:
        n = mib * 1024 * 1024
        payload = os.urandom(n)
        lat = []
        for _ in range(iters):
            t0 = time.perf_counter()
            ep.write(1, 0, payload)
            back = ep.read(1, 0, n)
            lat.append(time.perf_counter() - t0)
            assert len(back) == n
        lat.sort()
        gbps = (n * 2) / statistics.median(lat) / 1e9        # write+read bytes
        p50 = statistics.median(lat) * 1e3
        p99 = lat[min(len(lat) - 1, int(len(lat) * 0.99))] * 1e3
        print(f"{mib:>6}Mi {iters:>6} {gbps:>7.2f} {gbps*8:>8.2f} {p50:>8.2f} {p99:>8.2f}")
    ep.close()


def run_server(local, port, max_mib):
    ep = Endpoint(local=local, peer=local, port=port)
    ep.start()
    ep.register(bytearray(max_mib * 1024 * 1024))
    print(f"serving on {local}:{port} (Ctrl-C to stop)")
    while True:
        time.sleep(3600)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--local", default="127.0.0.1")
    p.add_argument("--peer", default="127.0.0.1")
    p.add_argument("--port", type=int, default=50700)
    p.add_argument("--server", action="store_true")
    p.add_argument("--iters", type=int, default=20)
    p.add_argument("--sizes", default="1,4,16,64")
    a = p.parse_args()
    sizes = [int(x) for x in a.sizes.split(",")]
    if a.server:
        run_server(a.local, a.port, max(sizes))
        return
    if a.local == a.peer == "127.0.0.1":
        # self-contained loopback: spin the server in-process
        srv = Endpoint(local="127.0.0.1", peer="127.0.0.1", port=a.port)
        srv.start()
        srv.register(bytearray(max(sizes) * 1024 * 1024))
        time.sleep(0.2)
    run_client(a.local, a.peer, a.port, sizes, a.iters)


if __name__ == "__main__":
    main()
