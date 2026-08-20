"""Prove real RDMA on rxe: two endpoints on the same rxe device, side A does a
one-sided RDMA WRITE into B's registered memory. No sockets between them for
data; a local dict swap stands in for the QP-info side-channel.
"""
import sys
sys.path.insert(0, "/home/petrus/strixlink")
from strixlink.rxe_transport import RxeEndpoint

a = RxeEndpoint(dev="rxe_tb", region_size=4096)
b = RxeEndpoint(dev="rxe_tb", region_size=4096)

a.connect(b.local_conn())
b.connect(a.local_conn())

payload = b"RDMA-VERBS-OVER-THUNDERBOLT"
a.write(payload)  # one-sided: lands in B's memory without B doing anything

got = b.read_local(len(payload))
assert got == payload, (got, payload)
print("rxe RDMA WRITE verified: A wrote", len(payload), "bytes straight into B's memory")
print("payload round-trip:", got.decode())
