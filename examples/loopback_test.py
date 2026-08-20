"""Self-contained loopback test: two endpoints on 127.0.0.1 exercise every
verb (register / write / read / send / recv). Runs anywhere, no Thunderbolt
needed, so CI and a laptop can both prove the API works.

For the real two-machine run over Thunderbolt, see examples/tb_transfer.py.
"""

import time

from strixlink import Endpoint


def main() -> int:
    a = Endpoint(local="127.0.0.1", peer="127.0.0.1", port=50600)
    b = Endpoint(local="127.0.0.1", peer="127.0.0.1", port=50600)

    # b serves a region; a connects and drives verbs against it.
    region = bytearray(64)
    b.start()
    rid = b.register(region)
    time.sleep(0.1)
    a.connect()

    # one-sided write, then read it back
    a.write(rid, 8, b"STRIXLINK")
    got = a.read(rid, 8, 9)
    assert got == b"STRIXLINK", got
    assert bytes(region[8:17]) == b"STRIXLINK"

    # two-sided message
    a.send(b"hello strix")
    assert b.recv(timeout=5) == b"hello strix"

    a.close()
    b.close()
    print("loopback OK: write, read, send/recv all verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
