"""Real two-machine transfer over the Thunderbolt link.

On the Strix box (10.55.0.2):
    python3 examples/tb_transfer.py serve  --local 10.55.0.2

On the Mac (10.55.0.1):
    python3 examples/tb_transfer.py client --local 10.55.0.1 --peer 10.55.0.2 --mb 256

The client registers nothing; it writes an MB-sized payload into the server's
region, reads it back, and reports throughput. This is the honest TCP-over-TB
number (kernel-copied, two-sided) — the floor a real RDMA transport improves on.
"""

import argparse
import time

from strixlink import Endpoint

REGION_RID_HINT = 1  # first register() on the server returns rid 1


def serve(args):
    ep = Endpoint(local=args.local, peer=args.local, port=args.port)
    ep.start()
    ep.register(bytearray(args.mb * 1024 * 1024))
    print(f"serving a {args.mb} MiB region on {args.local}:{args.port} (Ctrl-C to stop)")
    while True:
        time.sleep(3600)


def client(args):
    ep = Endpoint(local=args.local, peer=args.peer, port=args.port)
    ep.connect()
    payload = bytes(args.mb * 1024 * 1024)
    t0 = time.time()
    ep.write(REGION_RID_HINT, 0, payload)
    back = ep.read(REGION_RID_HINT, 0, len(payload))
    dt = time.time() - t0
    assert len(back) == len(payload), "round-trip length mismatch"
    gbit = (len(payload) * 2 * 8) / dt / 1e9
    print(f"round-tripped {args.mb} MiB in {dt:.3f}s = {gbit:.2f} Gbit/s (write+read, TCP/TB)")
    ep.close()


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="mode", required=True)
    for name in ("serve", "client"):
        sp = sub.add_parser(name)
        sp.add_argument("--local", required=True)
        sp.add_argument("--peer", default="")
        sp.add_argument("--port", type=int, default=50555)
        sp.add_argument("--mb", type=int, default=256)
    a = p.parse_args()
    (serve if a.mode == "serve" else client)(a)


if __name__ == "__main__":
    main()
